import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:flutter/services.dart' show rootBundle;
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'env.dart';
import 'backend_manager.dart';

class BackendManagerMacOS extends BackendManager {
  BackendManagerMacOS() : super.internal();
  Process? _backendProcess;

  // Version key dùng bundledBackendVersion từ env.dart
  // Tự động bump khi có thay đổi file Python trong app/, main.py, requirements, pyproject.toml, uv.toml
  static const String _currentEngineVersion = Env.bundledBackendVersion;

  @override
  Future<void> startBackend({Function(String)? onProgress}) async {
    if (onProgress != null) onProgress("Đang kiểm tra AI Engine (macOS)...");

    try {
      await http.post(Uri.parse('http://127.0.0.1:10330/shutdown')).timeout(const Duration(milliseconds: 500));
    } catch (_) {}
    await Process.run('pkill', ['-9', '-f', 'SportSeekerAPI']);
    await Future.delayed(const Duration(milliseconds: 1000));

    final currentPid = pid;
    final prefs = await SharedPreferences.getInstance();

    final customModelPath = prefs.getString('custom_model_path') ?? '';
    final customModelName = prefs.getString('custom_model_name') ?? 'buffalo_l';

    final env = Map<String, String>.from(Platform.environment);
    env['SPORT_SEEKER_PARENT_PID'] = currentPid.toString();
    env['SPORT_SEEKER_MODELS_ROOT'] = customModelPath;
    env['SPORT_SEEKER_MODEL_NAME'] = customModelName;

    // Analytics — backend dùng để init PostHog
    env['POSTHOG_API_KEY'] = Env.posthogApiKey;
    env['POSTHOG_API_HOST'] = Env.posthogApiHost;
    env['SPORT_SEEKER_APP_VERSION'] = Env.appVersion;
    env['SPORT_SEEKER_BUILD_NUMBER'] = Env.buildNumber.toString();

    String pythonCmd = '';
    List<String> args = [];
    String? runDirectory; // BỔ SUNG: Khởi tạo biến lưu thư mục làm việc

    if (useBackendBinary) {
      final supportDir = await getApplicationSupportDirectory();
      final backendDir = Directory('${supportDir.path}/sport_seeker_backend');

      runDirectory = backendDir.path; // BỔ SUNG: Set working directory cho môi trường production
      pythonCmd = '${backendDir.path}/SportSeekerAPI';
      
      final exeFile = File(pythonCmd);
      final lastInstalledVersion = prefs.getString('installed_engine_version') ?? '';

      // Reinstall nếu: binary không tồn tại HOẶC version key không khớp
      // Version key = appVersion+buildNumber → tự động thay đổi mỗi build mới
      if (!await exeFile.exists() || lastInstalledVersion != _currentEngineVersion) {
        if (onProgress != null) {
          onProgress(
            lastInstalledVersion.isEmpty
                ? "Đang cài đặt AI Engine lần đầu (10-30s)..."
                : "Phát hiện phiên bản mới, đang cập nhật AI Engine...",
          );
        }

        // Xóa engine cũ (model/user data không nằm ở đây → an toàn)
        if (await backendDir.exists()) await backendDir.delete(recursive: true);
        await backendDir.create(recursive: true);

        try {
          // Dùng tar chuẩn POSIX để giữ toàn bộ symlinks (.dylib của Paddle/NumPy)
          final ByteData tarBytes = await rootBundle.load('assets/backend/api_payload.tar.gz');
          final tmpTar = File('${backendDir.path}/temp_payload.tar.gz');
          await tmpTar.writeAsBytes(tarBytes.buffer.asUint8List());

          final extractResult = await Process.run('tar', ['-xzf', tmpTar.path, '-C', backendDir.path]);
          if (extractResult.exitCode != 0) {
            throw Exception("Lỗi tar: ${extractResult.stderr}");
          }
          await tmpTar.delete();

          await Process.run('chmod', ['-R', '+x', backendDir.path]);

          // Lưu version key mới — lần sau sẽ skip nếu cùng build
          await prefs.setString('installed_engine_version', _currentEngineVersion);

          // Giữ key cũ để tương thích ngược (nếu code khác đang đọc)
          await prefs.setString('extracted_bundled_version', _currentEngineVersion);
          await prefs.setString('installed_backend_version', _currentEngineVersion);
        } catch (e) {
          if (onProgress != null) onProgress("Lỗi giải nén AI Engine: $e");
          return;
        }
      }
    } else {
      pythonCmd = '../.venv/bin/python';
      args = ['../main.py'];
      // Dev mode: Giữ nguyên runDirectory là null để nó sử dụng working directory hiện tại của flutter run
    }

    if (onProgress != null) onProgress("Đang khởi động AI Engine...");

    String crashLogs = "";
    bool processDied = false;

    try {
      _backendProcess = await Process.start(
        pythonCmd, 
        args, 
        environment: env, 
        runInShell: false,
        workingDirectory: runDirectory // BỔ SUNG: Truyền biến này vào lệnh gọi Process
      );

      _backendProcess?.exitCode.then((code) {
        if (!isReady) {
          processDied = true;
          print("[BackendManager] Tiến trình AI chết ngầm với mã lỗi: $code");
        }
      });

      _backendProcess?.stdout.transform(utf8.decoder).listen((data) => stdout.write('[API] $data'));
      _backendProcess?.stderr.transform(utf8.decoder).listen((data) {
        stderr.write('[API ERR] $data');
        crashLogs += data;
        final match = RegExp(r'(\d+)%\|').firstMatch(data);
        if (match != null) modelDownloadProgress.value = int.parse(match.group(1)!) / 100.0;
      });

      await _waitForHealthCheck(() => processDied, () => crashLogs);
    } catch (e) {
      throw Exception("Không thể khởi động tiến trình: $e");
    }
  }

  Future<void> _waitForHealthCheck(bool Function() isProcessDead, String Function() getCrashLogs) async {
    int retries = 240;
    while (retries > 0) {
      if (isProcessDead()) {
        String errorMsg = getCrashLogs();
        if (errorMsg.length > 200) errorMsg = errorMsg.substring(errorMsg.length - 200);
        throw Exception("AI Engine bị crash ngầm do lỗi thư viện hệ thống!\nChi tiết: $errorMsg");
      }
      try {
        final res = await http.get(Uri.parse('http://127.0.0.1:10330/health')).timeout(const Duration(milliseconds: 500));
        if (res.statusCode == 200) { isReady = true; return; }
      } catch (_) {}
      await Future.delayed(const Duration(milliseconds: 500));
      retries--;
    }
    throw Exception("Timeout: Backend không phản hồi sau 2 phút.");
  }

  @override
  void stopBackend() => _backendProcess?.kill();
}
