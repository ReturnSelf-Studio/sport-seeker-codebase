import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

import 'env.dart';
import 'backend_manager.dart';

class BackendManagerWindows extends BackendManager {
  BackendManagerWindows() : super.internal();
  Process? _backendProcess;

  @override
  Future<void> startBackend({Function(String)? onProgress}) async {
    if (onProgress != null) onProgress("Đang kết nối môi trường AI...");

    final String appData = Platform.environment['APPDATA'] ?? '';
    final String backendRoot = '$appData\\SportSeeker\\app\\backend';

    String pythonCmd = '$backendRoot\\.venv\\Scripts\\python.exe';
    // Đã sửa lại thành chạy trực tiếp file main.py thay vì absolute path 
    // vì chúng ta sẽ cấu hình workingDirectory ngay bên dưới
    String scriptPath = 'main.py';

    if (!await File(pythonCmd).exists()) {
      throw Exception("Không tìm thấy môi trường AI! Vui lòng chạy file 'install_sport_seeker.bat' trước.");
    }

    final env = Map<String, String>.from(Platform.environment);
    env['SPORT_SEEKER_PARENT_PID'] = pid.toString();
    env['PYTHONUNBUFFERED'] = '1'; // Ep Python in log ra ngay lap tuc de lay phan tram
    env['PYTHONIOENCODING'] = 'utf-8';
    // Analytics — backend dùng để init PostHog
    env['POSTHOG_API_KEY'] = Env.posthogApiKey;
    env['POSTHOG_API_HOST'] = Env.posthogApiHost;
    env['SPORT_SEEKER_APP_VERSION'] = Env.appVersion;
    env['SPORT_SEEKER_BUILD_NUMBER'] = Env.buildNumber.toString();

    try {
      await Process.run('cmd', ['/c', 'for /f "tokens=5" %a in (\'netstat -aon ^| findstr :10330\') do taskkill /F /PID %a /T']);
      await Future.delayed(const Duration(milliseconds: 1000));

      print("=" * 60);
      print("🚀 FRONTEND SPAWN BACKEND COMMAND:");
      print("Executable : $pythonCmd");
      print("Arguments  : ${[scriptPath].join(' ')}");
      print("Working Dir: $backendRoot");
      print("=" * 60);

      _backendProcess = await Process.start(
        pythonCmd,
        [scriptPath],
        environment: env,
        runInShell: false,
        workingDirectory: backendRoot // DÒNG QUAN TRỌNG NHẤT: Ép tiến trình chạy đúng tại thư mục backend
      );

      bool processDied = false;
      _backendProcess?.exitCode.then((code) {
        if (!isReady) processDied = true;
      });

      String crashLogs = "";

      _backendProcess?.stdout.transform(const Utf8Decoder(allowMalformed: true)).listen((data) {
        stdout.write('[API] $data');
        if (data.trim().isNotEmpty) {
          latestLog.value = data.trim().split('\n').last;
        }
      });

      _backendProcess?.stderr.transform(const Utf8Decoder(allowMalformed: true)).listen((data) {
        stderr.write('[API ERR] $data');
        crashLogs += data;
        if (data.trim().isNotEmpty) {
          latestLog.value = data.trim().split('\n').last;
        }

        final match = RegExp(r'(\d+)%').firstMatch(data);
        if (match != null) {
           final percent = int.tryParse(match.group(1)!);
           if (percent != null && percent <= 100) {
             modelDownloadProgress.value = percent / 100.0;
           }
        }
      });

      await _waitForHealthCheck(() => processDied, () => crashLogs);
    } catch (e) {
      throw Exception("Lỗi khởi động Engine: $e");
    }
  }

  Future<void> _waitForHealthCheck(bool Function() isProcessDead, String Function() getCrashLogs) async {
    int retries = 240;
    while (retries > 0) {
      if (isProcessDead()) {
        String errorMsg = getCrashLogs();
        if (errorMsg.length > 200) errorMsg = errorMsg.substring(errorMsg.length - 200);
        throw Exception("AI Engine bị crash ngầm!\nChi tiết: $errorMsg");
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
