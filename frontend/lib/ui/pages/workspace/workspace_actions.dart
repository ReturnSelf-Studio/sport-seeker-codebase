import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/widgets.dart';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';

class WorkspaceActions extends ChangeNotifier with WidgetsBindingObserver {
  final String projectId;
  final Function(String) onError;
  final ValueNotifier<bool> isProcessingNotifier;

  WebSocketChannel? _channel;
  Timer? _wsReconnectTimer;
  bool _disposed = false;

  List<String> logs = [];
  double progress = 0.0;
  String status = "SẴN SÀNG QUÉT";
  String videoProgressText = ''; // "87/2384 frames (3.6%)" — hiển thị dưới progress bar

  // Weighted progress state
  // Key = video name, value = total_frames (từ prescan)
  Map<String, int> _videoTotalFrames = {};
  // Frames đã hoàn tất hoàn toàn (video_done)
  int _completedFrames = 0;
  // Tổng frames của toàn session
  int _totalFrames = 0;
  // Frames của video đang xử lý hiện tại (từ log ▶)
  int _currentVideoProcessedFrames = 0;

  bool get isProcessing => isProcessingNotifier.value;

  String pipelineMode = 'face_bib';
  int frameInterval = 30;

  // Pre-scan state
  Map<String, dynamic>? prescanData;
  bool isPrescanLoading = false;
  bool isPrescanDone = false;

  // Prefix backend dùng cho dòng progress video — phải khớp với video_pipeline.py
  // Backend emit: f"   ▶ {fname}: {cf}/{tf} frames ({pct:.1f}%)"
  static const String _progressPrefix = '   ▶ ';

  WorkspaceActions({
    required this.projectId,
    required this.onError,
    required this.isProcessingNotifier,
  }) {
    WidgetsBinding.instance.addObserver(this);
    _connectWebSocket();
    _syncStatusFromBackend();
  }

  // ── App lifecycle ────────────────────────────────────────────────────────

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _syncStatusFromBackend();
      if (_channel == null) _connectWebSocket();
    }
  }

  Future<void> _syncStatusFromBackend() async {
    try {
      final res = await http
          .get(Uri.parse('http://127.0.0.1:10330/process/status'))
          .timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        final backendRunning = data['is_running'] as bool;
        if (backendRunning != isProcessingNotifier.value) {
          isProcessingNotifier.value = backendRunning;
          if (!backendRunning && status == "ĐANG XỬ LÝ...") {
            status = "HOÀN TẤT";
          }
          notifyListeners();
        }
      }
    } catch (_) {}
  }

  // ── WebSocket ────────────────────────────────────────────────────────────

  void _connectWebSocket() {
    if (_disposed) return;
    try {
      _channel = WebSocketChannel.connect(Uri.parse('ws://127.0.0.1:10330/ws'));
      _channel!.stream.listen(
        _onWsMessage,
        onError: (_) => _scheduleReconnect(),
        onDone: _scheduleReconnect,
        cancelOnError: false,
      );
    } catch (_) {
      _scheduleReconnect();
    }
  }

  void _scheduleReconnect() {
    if (_disposed) return;
    _channel = null;
    _wsReconnectTimer?.cancel();
    _wsReconnectTimer = Timer(const Duration(seconds: 3), () {
      if (!_disposed) _connectWebSocket();
    });
  }

  void _onWsMessage(dynamic message) {
    if (_disposed) return;
    final data = jsonDecode(message as String);

    if (data['type'] == 'log') {
      final raw = data['data'] as String;
      final line = '> $raw';

      if (raw.startsWith(_progressPrefix)) {
        // Backend format: "   ▶ filename: X/Y frames (Z%)"
        // Extract "X/Y frames (Z%)" để hiển thị dưới progress bar
        final colonIdx = raw.indexOf(': ', _progressPrefix.length);
        if (colonIdx != -1) {
          final frameInfo = raw.substring(colonIdx + 2).trim();
          videoProgressText = frameInfo;
          // Parse X để tính weighted progress
          final slashIdx = frameInfo.indexOf('/');
          if (slashIdx != -1 && _totalFrames > 0) {
            _currentVideoProcessedFrames = int.tryParse(frameInfo.substring(0, slashIdx).trim()) ?? 0;
            progress = (_completedFrames + _currentVideoProcessedFrames) / _totalFrames;
            progress = progress.clamp(0.0, 1.0);
          }
        }
      } else {
        // Dòng static (bắt đầu video, xong video, lỗi...) → append bình thường
        logs.add(line);
        if (logs.length > 200) logs.removeAt(0);
      }

    } else if (data['type'] == 'progress') {
      // Không dùng — progress được tính theo weighted frame logic
      // để tránh override _completedFrames + _currentVideoProcessedFrames

    } else if (data['type'] == 'video_done') {
      // Backend emit sau mỗi video xong → update prescan widget realtime + weighted progress
      final videoName = data['data']['name'] as String;
      final doneTotalFrames = (data['data']['total_frames'] as num?)?.toInt();
      _applyVideoDone(videoName, doneTotalFrames: doneTotalFrames);

    } else if (data['type'] == 'stage') {
      final stage = data['data'] as String;
      if (stage == 'done' || stage == 'error' || stage == 'stopped') {
        isProcessingNotifier.value = false;
        status = stage == 'done'
            ? "HOÀN TẤT"
            : stage == 'stopped'
                ? "ĐÃ DỪNG"
                : "LỖI";
        if (stage == 'done' || stage == 'stopped') {
          loadPrescan();
        }
      } else {
        isProcessingNotifier.value = true;
        status = "ĐANG XỬ LÝ...";
      }
    }

    notifyListeners();
  }

  /// Update prescanData in-memory ngay khi video_done, không chờ reload
  void _applyVideoDone(String videoName, {int? doneTotalFrames}) {
    if (prescanData == null) return;

    final summary = Map<String, dynamic>.from(prescanData!['summary'] as Map);
    final videos = (prescanData!['videos'] as List).map((v) {
      final vMap = Map<String, dynamic>.from(v as Map);
      if (vMap['name'] == videoName) vMap['scan_status'] = 'done';
      return vMap;
    }).toList();

    summary['done'] = (summary['done'] as int) + 1;
    summary['pending'] = ((summary['pending'] as int) - 1).clamp(0, 99999);

    prescanData = {...prescanData!, 'summary': summary, 'videos': videos};

    // Cộng frames đã hoàn tất vào _completedFrames
    final frames = doneTotalFrames ?? _videoTotalFrames[videoName] ?? 0;
    _completedFrames += frames;
    _currentVideoProcessedFrames = 0; // reset frame đang xử lý
    if (_totalFrames > 0) {
      progress = _completedFrames / _totalFrames;
      progress = progress.clamp(0.0, 1.0);
    }
  }

  // ── Config ───────────────────────────────────────────────────────────────

  void updateConfig({String? mode, int? interval}) {
    if (mode != null) pipelineMode = mode;
    if (interval != null) frameInterval = interval;
    notifyListeners();
  }

  // ── Pre-scan ─────────────────────────────────────────────────────────────

  Future<void> loadPrescan() async {
    isPrescanLoading = true;
    isPrescanDone = false;
    prescanData = null;
    notifyListeners();

    try {
      final res = await http
          .get(Uri.parse('http://127.0.0.1:10330/process/prescan/$projectId'))
          .timeout(const Duration(seconds: 30));

      if (res.statusCode == 200) {
        prescanData = jsonDecode(res.body);
        isPrescanDone = true;
      } else {
        onError('Lỗi pre-scan: ${res.body}');
      }
    } catch (e) {
      onError('Lỗi kết nối pre-scan: $e');
    } finally {
      isPrescanLoading = false;
      notifyListeners();
    }
  }

  // ── Start / Cancel ───────────────────────────────────────────────────────

  Future<void> startProcess({bool rescanAll = false}) async {
    if (isProcessing) return;

    if (!isPrescanDone || prescanData == null) {
      onError('Vui lòng kiểm tra danh sách video trước khi bắt đầu.');
      return;
    }

    final summary = prescanData!['summary'] as Map<String, dynamic>;
    final pending = summary['pending'] as int;
    final overLimit = prescanData!['over_limit'] as bool;

    if (overLimit) {
      onError('Dự án vượt giới hạn ${prescanData!['max_videos']} video. Vui lòng chia nhỏ.');
      return;
    }

    if (!rescanAll && pending == 0) {
      onError('Tất cả video đã quét. Dùng "Quét lại tất cả" nếu cần.');
      return;
    }

    logs.clear();
    progress = 0.0;
    videoProgressText = '';
    _completedFrames = 0;
    _currentVideoProcessedFrames = 0;
    _videoTotalFrames = {};
    _totalFrames = 0;

    // Build frame map từ prescanData để tính weighted progress
    if (prescanData != null) {
      final videos = prescanData!['videos'] as List;
      for (final v in videos) {
        final vMap = v as Map<String, dynamic>;
        final name = vMap['name'] as String;
        final tf = (vMap['total_frames'] as num?)?.toInt() ?? 0;
        // Chỉ tính video sẽ được quét trong session này
        final shouldScan = rescanAll || vMap['scan_status'] != 'done';
        if (shouldScan && tf > 0) {
          _videoTotalFrames[name] = tf;
          _totalFrames += tf;
        }
      }
    }

    status = "ĐANG KHỞI TẠO...";
    isProcessingNotifier.value = true;
    notifyListeners();

    try {
      final res = await http.post(
        Uri.parse('http://127.0.0.1:10330/process/start'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          "project_id": projectId,
          "pipeline_mode": pipelineMode,
          "frame_interval": frameInterval,
          "bib_min": 3,
          "bib_max": 5,
          "rescan_all": rescanAll,
        }),
      );
      if (res.statusCode != 200) {
        throw Exception("Server trả về lỗi: ${res.body}");
      }
    } catch (e) {
      isProcessingNotifier.value = false;
      status = "LỖI KẾT NỐI API";
      notifyListeners();
      onError("Lỗi xử lý: $e");
    }
  }

  Future<bool> cancelAndRollback() async {
    try {
      final res = await http
          .post(Uri.parse('http://127.0.0.1:10330/process/cancel'))
          .timeout(const Duration(seconds: 15));
      if (res.statusCode == 200) {
        isProcessingNotifier.value = false;
        status = "ĐÃ HỦY";
        notifyListeners();
        return true;
      }
    } catch (_) {}
    return false;
  }

  // ── Dispose ──────────────────────────────────────────────────────────────

  @override
  void dispose() {
    _disposed = true;
    WidgetsBinding.instance.removeObserver(this);
    _wsReconnectTimer?.cancel();
    _channel?.sink.close();
    super.dispose();
  }
}
