"""
analytics_service.py — PostHog tracking cho Sport Seeker backend.

Device ID:
  - macOS: ~/SportSeeker/device_id (file)
  - Windows: HKCU\\Software\\Aibus\\SportSeeker\\device_id (Registry), fallback sang %APPDATA%\\SportSeeker\\device_id

Session:
  - Mỗi lần backend khởi động = 1 session mới
  - Lưu session state vào file để recover unclean exit ở lần khởi động sau
  - end_session() phải được gọi trước khi backend thoát (shutdown route + zombie_killer)
"""

import os
import sys
import json
import time
import uuid
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_BASE_PROPERTIES: dict = {}


class AnalyticsService:
    def __init__(self):
        self._posthog = None
        self._device_id: str | None = None
        self._session_id: str | None = None
        self._session_start: datetime | None = None
        self._initialized = False
        self._session_ended = False
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def init(self, api_key: str, host: str, extra_properties: dict | None = None):
        """Khởi tạo analytics. Gọi 1 lần duy nhất trong startup_event."""
        if self._initialized:
            return
            
        try:
            import posthog as ph  # type: ignore
            if not api_key:
                print("❌ [Analytics] API KEY RỖNG - Hủy khởi tạo!", flush=True)
                return
                
            ph.api_key = api_key
            ph.host = host.rstrip("/")
            ph.debug = True  # Giữ debug để xem log mạng PostHog
            ph.disabled = False
            self._posthog = ph
            print("✅ [Analytics] Import và cấu hình PostHog thành công!", flush=True)
            
        except Exception as e:
            print(f"❌ [Analytics] LỖI KHỞI TẠO: {e}", flush=True)
            return

        global _BASE_PROPERTIES
        _BASE_PROPERTIES = extra_properties or {}

        self._device_id = self._load_or_create_device_id()
        
        # BẬT CỜ INITIALIZED TRƯỚC KHI GỌI START_SESSION
        self._initialized = True 
        print("✅ [Analytics] Đã bật cờ _initialized = True", flush=True)
        
        self._recover_unclosed_session()
        self._start_session()
        
        print(f"✅ [Analytics] HOÀN TẤT INIT! Device: {self._device_id}, Session: {self._session_id}", flush=True)

    def capture(self, event: str, properties: dict | None = None):
        """Ghi 1 event vào PostHog queue (non-blocking)."""
        if not self._initialized or self._posthog is None:
            print(f"  -> ❌ [Capture] Bị chặn (Init: {self._initialized}, PostHog: {self._posthog is not None})", flush=True)
            return
            
        try:
            props = self._build_properties(properties)
            # SỬA LỖI TẠI ĐÂY: Đưa event lên đầu, truyền distinct_id bằng keyword
            self._posthog.capture(event, distinct_id=self._device_id, properties=props)
            print(f"  -> ✅ [Capture] Đã nhét event '{event}' vào hàng đợi!", flush=True)
        except Exception as e:
            print(f"  -> ❌ [Capture] Lỗi khi gọi capture: {e}", flush=True)

    def end_session(self, reason: str = "shutdown"):
        """Kết thúc session, flush ngay lập tức. Gọi trước khi process thoát."""
        with self._lock:
            if not self._initialized or self._session_ended or self._session_id is None:
                return
            self._session_ended = True

        try:
            end_time = datetime.now(timezone.utc)
            duration = int((end_time - self._session_start).total_seconds()) if self._session_start else 0
            
            print(f"🛑 [Analytics] Đang kết thúc session do: {reason}", flush=True)
            self.capture("app_session_ended", {
                "session_id": self._session_id,
                "session_start": self._session_start.isoformat() if self._session_start else None,
                "session_end": end_time.isoformat(),
                "session_duration_seconds": max(0, duration),
                "end_reason": reason,
            })
            self.flush()
            self._persist_session_state(closed=True)
            print("✅ [Analytics] Kết thúc session thành công!", flush=True)
        except Exception as e:
            print(f"❌ [Analytics] end_session error: {e}", flush=True)

    def flush(self):
        """Flush PostHog queue synchronously."""
        if self._posthog:
            try:
                self._posthog.flush()
            except Exception as e:
                print(f"❌ [Analytics] Lỗi flush: {e}", flush=True)

    # ------------------------------------------------------------------ #
    # Internal                                                             #
    # ------------------------------------------------------------------ #

    def _start_session(self):
        self._session_id = f"session_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        self._session_start = datetime.now(timezone.utc)
        self._session_ended = False
        self._persist_session_state(closed=False)
        
        print(f"🔄 [Analytics] Đang gọi capture app_opened...", flush=True)
        self.capture("app_opened", {
            "session_id": self._session_id,
            "platform": sys.platform,
            **_BASE_PROPERTIES,
        })
        
        if self._posthog:
            print(f"💨 [Analytics] Ép PostHog xả hàng đợi (flush)...", flush=True)
            self.flush()

    def _recover_unclosed_session(self):
        state = self._load_session_state()
        if not state or state.get("closed"):
            return
        session_id = state.get("session_id")
        started_at_raw = state.get("session_start")
        if not session_id or not started_at_raw:
            return
        try:
            started_at = datetime.fromisoformat(started_at_raw)
            recovered_at = datetime.now(timezone.utc)
            duration = int((recovered_at - started_at).total_seconds())
            if self._posthog and self._device_id:
                print(f"♻️ [Analytics] Đang khôi phục session cũ: {session_id}", flush=True)
                # SỬA LỖI TẠI ĐÂY: Đưa event lên đầu, truyền distinct_id bằng keyword
                self._posthog.capture(
                    "app_session_ended",
                    distinct_id=self._device_id,
                    properties=self._build_properties({
                        "session_id": session_id,
                        "session_start": started_at_raw,
                        "session_end": recovered_at.isoformat(),
                        "session_duration_seconds": max(0, duration),
                        "end_reason": "recovered_after_unclean_exit",
                    }),
                )
                self.flush()
        except Exception as e:
            print(f"❌ [Analytics] recover error: {e}", flush=True)

    # ---- Device ID ---------------------------------------------------- #

    def _load_or_create_device_id(self) -> str:
        if sys.platform == "win32":
            return self._device_id_windows()
        return self._device_id_file(Path.home() / "SportSeeker" / "device_id")

    def _device_id_windows(self) -> str:
        # Ưu tiên Registry — survive uninstall/reinstall app
        try:
            import winreg  # type: ignore
            key_path = r"Software\Aibus\SportSeeker"
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
                val, _ = winreg.QueryValueEx(key, "device_id")
                winreg.CloseKey(key)
                if val:
                    return val
            except FileNotFoundError:
                pass
            device_id = self._new_id("device")
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "device_id", 0, winreg.REG_SZ, device_id)
            winreg.CloseKey(key)
            return device_id
        except Exception as e:
            appdata = os.environ.get("APPDATA", str(Path.home()))
            return self._device_id_file(Path(appdata) / "SportSeeker" / "device_id")

    def _device_id_file(self, path: Path) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            val = path.read_text(encoding="utf-8").strip()
            if val:
                return val
        device_id = self._new_id("device")
        path.write_text(device_id, encoding="utf-8")
        return device_id

    # ---- Session state persistence ------------------------------------ #

    def _session_state_file(self) -> Path:
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", str(Path.home()))) / "SportSeeker"
        else:
            base = Path.home() / "SportSeeker"
        base.mkdir(parents=True, exist_ok=True)
        return base / "analytics_session.json"

    def _persist_session_state(self, closed: bool):
        try:
            self._session_state_file().write_text(
                json.dumps({
                    "session_id": self._session_id,
                    "session_start": self._session_start.isoformat() if self._session_start else None,
                    "closed": closed,
                }),
                encoding="utf-8",
            )
        except Exception as e:
            pass

    def _load_session_state(self) -> dict | None:
        try:
            f = self._session_state_file()
            if not f.exists():
                return None
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            return None

    # ---- Helpers ------------------------------------------------------ #

    def _build_properties(self, extra: dict | None = None) -> dict:
        props: dict = {
            "distinct_id": self._device_id,
            "device_id": self._device_id,
            "session_id": self._session_id,
            "platform": sys.platform,
            **_BASE_PROPERTIES,
        }
        if extra:
            props.update(extra)
        return props

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{int(time.time() * 1000)}_{uuid.uuid4().hex}"

analytics_service = AnalyticsService()
