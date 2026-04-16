import 'dart:io';
import 'package:flutter/foundation.dart';

import 'backend_manager_windows.dart';
import 'backend_manager_macos.dart';

abstract class BackendManager {
  static BackendManager? _instance;

  BackendManager.internal();

  factory BackendManager() {
    if (_instance == null) {
      if (Platform.isWindows) {
        _instance = BackendManagerWindows();
      } else {
        _instance = BackendManagerMacOS();
      }
    }
    return _instance!;
  }

  bool isReady = false;
  bool useBackendBinary = kReleaseMode;

  final String currentBundledVersion = "1.0.1";

  final ValueNotifier<double?> modelDownloadProgress = ValueNotifier(null);

  final ValueNotifier<String> latestLog = ValueNotifier("Đang kết nối Engine...");

  Future<void> startBackend({Function(String)? onProgress});
  void stopBackend();
}
