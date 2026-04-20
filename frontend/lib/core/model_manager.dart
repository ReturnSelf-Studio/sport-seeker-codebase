import 'dart:convert';
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:archive/archive_io.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'env.dart';

class ModelManager {
  static final ModelManager _instance = ModelManager._internal();
  factory ModelManager() => _instance;
  ModelManager._internal();

  final ValueNotifier<double?> downloadProgress = ValueNotifier(null);
  final ValueNotifier<String> statusMessage = ValueNotifier("Sẵn sàng");

  bool isDownloading = false;
  CancelToken? _cancelToken;

  String get _homePath {
    if (Platform.isWindows) return Platform.environment['USERPROFILE'] ?? 'C:\\';
    return Platform.environment['HOME'] ?? '/';
  }

  Future<String> getTargetModelDir() async {
    final prefs = await SharedPreferences.getInstance();
    final customPath = prefs.getString('custom_model_path') ?? '';
    if (customPath.isNotEmpty) return customPath;
    return '$_homePath/SportSeeker/models'; // Thư mục mặc định
  }

  Future<void> pauseDownload() async {
    if (isDownloading && _cancelToken != null) {
      _cancelToken!.cancel("User paused");
      isDownloading = false;
      statusMessage.value = "Đã tạm dừng";
    }
  }

  Future<void> checkAndDownloadModels() async {
    if (isDownloading) return;

    if (Env.modelsVersionUrl.isEmpty || Env.modelsVersionUrl.contains("YourRepo")) {
      statusMessage.value = "Lỗi: Chưa cấu hình MODELS_UPDATE_URL trong .env";
      return;
    }

    isDownloading = true;
    _cancelToken = CancelToken();

    try {
      statusMessage.value = "Đang kiểm tra phiên bản Models...";
      final res = await http.get(Uri.parse(Env.modelsVersionUrl)).timeout(const Duration(seconds: 5));
      if (res.statusCode != 200) throw Exception("Không tải được version.json");

      final data = jsonDecode(res.body);
      final baseUrl = data['base_url'];
      final List<String> chunks = List<String>.from(data['chunks']);
      final targetVersion = data['version'];

      final prefs = await SharedPreferences.getInstance();
      final currentVersion = prefs.getString('installed_models_version');

      if (currentVersion == targetVersion) {
        statusMessage.value = "Models đã là bản mới nhất!";
        isDownloading = false;
        return;
      }

      final targetDir = await getTargetModelDir();
      final stagingDir = Directory('$targetDir/.staging_download');
      if (!await stagingDir.exists()) await stagingDir.create(recursive: true);

      Dio dio = Dio();
      int downloadedChunks = 0;

      for (String chunkName in chunks) {
        final chunkFile = File('${stagingDir.path}/$chunkName');
        if (await chunkFile.exists()) {
          downloadedChunks++;
        }
      }

      for (String chunkName in chunks) {
        if (_cancelToken!.isCancelled) break;

        final chunkFile = File('${stagingDir.path}/$chunkName');
        if (await chunkFile.exists()) continue; // Skip nếu đã có

        statusMessage.value = "Đang tải $chunkName...";
        downloadProgress.value = downloadedChunks / chunks.length;

        bool success = false;
        int retries = 3;

        while (!success && retries > 0 && !_cancelToken!.isCancelled) {
          try {
            await dio.download(
              '$baseUrl$chunkName',
              chunkFile.path,
              cancelToken: _cancelToken,
              onReceiveProgress: (rcv, total) {
                double chunkProg = total > 0 ? (rcv / total) : 0;
                downloadProgress.value = (downloadedChunks + chunkProg) / chunks.length;
              }
            );
            success = true;
          } catch (e) {
            if (CancelToken.isCancel(e as DioException)) throw e; // User bấm Pause
            retries--;
            await Future.delayed(const Duration(seconds: 2));
          }
        }

        if (!success) throw Exception("Rớt mạng quá nhiều lần. Vui lòng tải lại.");
        downloadedChunks++;
      }

      if (_cancelToken!.isCancelled) return;

      statusMessage.value = "Đang ghép nối dữ liệu Models...";
      downloadProgress.value = null; // Hiển thị quay vòng tròn (Indeterminate)

      final zipFile = File('${stagingDir.path}/merged_models.zip');
      if (await zipFile.exists()) await zipFile.delete();

      final sink = zipFile.openWrite(mode: FileMode.writeOnlyAppend);
      for (String chunkName in chunks) {
        final chunkFile = File('${stagingDir.path}/$chunkName');
        await sink.addStream(chunkFile.openRead());
        await chunkFile.delete(); // Giải phóng dung lượng
      }
      await sink.close();

      statusMessage.value = "Đang bung nén Models (quá trình này mất vài phút)...";
      await extractFileToDisk(zipFile.path, targetDir);

      await zipFile.delete();
      await stagingDir.delete(recursive: true);
      await prefs.setString('installed_models_version', targetVersion);

      statusMessage.value = "Cập nhật Models hoàn tất!";
      isDownloading = false;

    } catch (e) {
      isDownloading = false;
      if (e is DioException && CancelToken.isCancel(e)) {
        statusMessage.value = "Đã tạm dừng tải Models.";
      } else {
        statusMessage.value = "Lỗi: $e";
      }
      downloadProgress.value = null;
    }
  }
}
