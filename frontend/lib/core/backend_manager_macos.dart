import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:dio/dio.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'env.dart';
import 'backend_manager.dart';

class BackendManagerMacOS extends BackendManager {
  BackendManagerMacOS() : super.internal();
  Process? _backendProcess;

  Future<void> _silentCheckAndUpdate(String supportDirPath) async {
    try {
      String targetUrl = "${Env.backendBaseUrl}macos/version.json";

      final res = await http.get(Uri.parse(targetUrl)).timeout(const Duration(seconds: 5));
      if (res.statusCode != 200) return;

      final data = jsonDecode(res.body);
      final latestVersion = data['version'];
      final baseUrl = data['base_url'];
      final List<String> chunks = List<String>.from(data['chunks']);

      final prefs = await SharedPreferences.getInstance();
      final installedVersion = prefs.getString('installed_backend_version') ?? currentBundledVersion;

      if (installedVersion == latestVersion) return;

      print("[Update] Phát hiện bản OTA $latestVersion (macOS). Bắt đầu tải ${chunks.length} chunks...");
      final stagingDir = Directory('$supportDirPath/sport_seeker_staging');
      if (!await stagingDir.exists()) await stagingDir.create(recursive: true);

      Dio dio = Dio();
      int downloadedChunks = 0;

      for (String chunkName in chunks) {
        final chunkFile = File('${stagingDir.path}/$chunkName');
        if (await chunkFile.exists()) {
          downloadedChunks++;
          continue;
        }
        print("[Update] Đang tải $chunkName...");
        bool success = false;
        int retries = 3;
        while (!success && retries > 0) {
          try {
            await dio.download('$baseUrl$chunkName', chunkFile.path);
            success = true;
          } catch (e) {
            retries--;
            await Future.delayed(const Duration(seconds: 2));
          }
        }
        if (!success) {
          print("[Update] Rớt mạng quá nhiều. Dừng cập nhật OTA để lần sau tải tiếp!");
          return;
        }
        downloadedChunks++;
      }

      print("[Update] Đã tải đủ 100% chunk. Bắt đầu ghép file...");
      final tarFile = File('${stagingDir.path}/api_payload.tar.gz');
      if (await tarFile.exists()) await tarFile.delete();

      final sink = tarFile.openWrite(mode: FileMode.writeOnlyAppend);
      for (String chunkName in chunks) {
        final chunkFile = File('${stagingDir.path}/$chunkName');
        await sink.addStream(chunkFile.openRead());
        await chunkFile.delete();
      }
      await sink.close();

      print("[Update] Đang giải nén AI Engine OTA...");
      final extractDir = Directory('${stagingDir.path}/extracted');
      if (await extractDir.exists()) await extractDir.delete(recursive: true);
      await extractDir.create();

      // Sử dụng tar native để giữ nguyên toàn bộ quyền file và symlinks
      final extractResult = await Process.run('tar', ['-xzf', tarFile.path, '-C', extractDir.path]);
      if (extractResult.exitCode != 0) {
        print("[Update Error] Lỗi giải nén tar: ${extractResult.stderr}");
        return;
      }
      await tarFile.delete();

      await Process.run('chmod', ['-R', '+x', extractDir.path]);

      await prefs.setString('staged_backend_version', latestVersion);
      print("[Update] Sẵn sàng áp dụng bản $latestVersion ở lần mở app tiếp theo!");

    } catch (e) {
      print("[Update Error] $e");
    }
  }

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

    String pythonCmd = '';
    List<String> args = [];

    if (useBackendBinary) {
      final supportDir = await getApplicationSupportDirectory();
      final backendDir = Directory('${supportDir.path}/sport_seeker_backend');
      final stagingDir = Directory('${supportDir.path}/sport_seeker_staging');
      final extractDir = Directory('${stagingDir.path}/extracted');

      final stagedVer = prefs.getString('staged_backend_version');
      if (stagedVer != null && await extractDir.exists()) {
        if (onProgress != null) onProgress("Đang áp dụng bản cập nhật AI Engine mới...");

        if (await backendDir.exists()) await backendDir.delete(recursive: true);
        await extractDir.rename(backendDir.path);

        if(await stagingDir.exists()) await stagingDir.delete(recursive: true);
        await prefs.setString('installed_backend_version', stagedVer);
        await prefs.remove('staged_backend_version');
      }

      pythonCmd = '${backendDir.path}/SportSeekerAPI';
      final exeFile = File(pythonCmd);
      final lastExtractedVersion = prefs.getString('extracted_bundled_version') ?? "";

      if (!await exeFile.exists() || lastExtractedVersion != currentBundledVersion) {
        if (onProgress != null) onProgress("Đang cài đặt và cập nhật AI Engine (10-30s)...");

        if (await backendDir.exists()) await backendDir.delete(recursive: true);
        await backendDir.create(recursive: true);

        try {
          final ByteData tarBytes = await rootBundle.load('assets/backend/api_payload.tar.gz');
          final tmpTar = File('${backendDir.path}/temp_payload.tar.gz');
          await tmpTar.writeAsBytes(tarBytes.buffer.asUint8List());
          
          // Sử dụng lệnh tar hệ thống thay vì package archive
          final extractResult = await Process.run('tar', ['-xzf', tmpTar.path, '-C', backendDir.path]);
          if (extractResult.exitCode != 0) {
            throw Exception("Lỗi tar: ${extractResult.stderr}");
          }
          await tmpTar.delete();

          await Process.run('chmod', ['-R', '+x', backendDir.path]);

          await prefs.setString('extracted_bundled_version', currentBundledVersion);
          await prefs.setString('installed_backend_version', currentBundledVersion);
        } catch (e) {
          if (onProgress != null) onProgress("Lỗi giải nén AI Engine: $e");
          return;
        }
      }
      _silentCheckAndUpdate(supportDir.path).ignore();
    } else {
      pythonCmd = '../.venv/bin/python';
      args = ['../main.py'];
    }

    if (onProgress != null) onProgress("Đang khởi động AI Engine...");

    String crashLogs = "";
    bool processDied = false;

    try {
      _backendProcess = await Process.start(pythonCmd, args, environment: env, runInShell: false);

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
