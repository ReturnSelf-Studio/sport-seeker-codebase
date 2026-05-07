import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

/// TrackingService — thin wrapper gửi events về backend Python.
/// Backend chịu trách nhiệm device ID, session lifecycle, queue và forward lên PostHog.
/// Public API giữ nguyên để không ảnh hưởng caller.
class TrackingService {
  TrackingService._();

  static final TrackingService instance = TrackingService._();

  static const String _backendBase = 'http://127.0.0.1:10330';

  bool _initialized = false;
  String? _currentScreenFingerprint;

  // ------------------------------------------------------------------ //
  // Lifecycle                                                            //
  // ------------------------------------------------------------------ //

  Future<void> init() async {
    if (_initialized) return;
    _initialized = true;
    // Analytics lifecycle (app_opened / session) được backend tự xử lý khi khởi động.
    // Flutter không cần gửi gì thêm ở đây.
  }

  // ------------------------------------------------------------------ //
  // Core capture                                                         //
  // ------------------------------------------------------------------ //

  Future<void> capture(
    String event, {
    Map<String, dynamic>? properties,
  }) async {
    if (!_initialized) return;
    _post('/analytics/event', {
      'event': event,
      'properties': properties ?? <String, dynamic>{},
    });
  }

  // ------------------------------------------------------------------ //
  // Screen tracking                                                      //
  // ------------------------------------------------------------------ //

  Future<void> trackScreen(
    String screenName, {
    Map<String, dynamic>? properties,
  }) async {
    final fingerprint = jsonEncode({
      'screen_name': screenName,
      'properties': properties ?? const <String, dynamic>{},
    });
    if (_currentScreenFingerprint == fingerprint) return;
    _currentScreenFingerprint = fingerprint;
    await capture('screen_view', properties: {
      'screen_name': screenName,
      if (properties != null) ...properties,
    });
  }

  // ------------------------------------------------------------------ //
  // Project tracking                                                     //
  // ------------------------------------------------------------------ //

  Future<void> trackProjectOpened(Map<String, dynamic> project) {
    return capture('project_opened', properties: {
      'project_id': project['id'],
      'project_name': project['name'],
    });
  }

  Future<void> trackProjectClosed(Map<String, dynamic> project) {
    return capture('project_closed', properties: {
      'project_id': project['id'],
      'project_name': project['name'],
    });
  }

  // ------------------------------------------------------------------ //
  // Session end                                                          //
  // ------------------------------------------------------------------ //

  /// Gọi khi user đóng app. Backend sẽ flush session và gửi lên PostHog.
  Future<void> endSession({required String reason}) async {
    if (!_initialized) return;
    try {
      await http
          .post(
            Uri.parse('$_backendBase/analytics/end_session'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'reason': reason}),
          )
          .timeout(const Duration(seconds: 3));
    } catch (_) {
      // Backend đã tắt — zombie_killer sẽ recover session ở lần khởi động sau.
    }
  }

  // ------------------------------------------------------------------ //
  // Visibility hooks (no-op — backend không cần biết foreground state)  //
  // ------------------------------------------------------------------ //

  Future<void> markVisible() async {}
  Future<void> markHidden() async {}

  // ------------------------------------------------------------------ //
  // Internal                                                             //
  // ------------------------------------------------------------------ //

  /// Fire-and-forget POST. Không throw, không block caller.
  void _post(String path, Map<String, dynamic> body) {
    http
        .post(
          Uri.parse('$_backendBase$path'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 5))
        .catchError((_) {
      // Ignore — backend chưa sẵn sàng hoặc đã tắt
      return http.Response('', HttpStatus.serviceUnavailable);
    });
  }
}
