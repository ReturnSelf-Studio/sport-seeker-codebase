import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';

class WorkspaceActions extends ChangeNotifier {
  final String projectId;
  final Function(String) onError;
  final ValueNotifier<bool> isProcessingNotifier;

  WebSocketChannel? _channel;
  List<String> logs = [];
  double progress = 0.0;
  String status = "SẴN SÀNG QUÉT";
  
  // Dùng Getter để lấy giá trị từ Global Notifier
  bool get isProcessing => isProcessingNotifier.value;

  String pipelineMode = 'face_bib';
  int frameInterval = 30;

  WorkspaceActions({
    required this.projectId, 
    required this.onError, 
    required this.isProcessingNotifier
  }) {
    _connectWebSocket();
  }

  void updateConfig({String? mode, int? interval}) {
    if (mode != null) pipelineMode = mode;
    if (interval != null) frameInterval = interval;
    notifyListeners(); 
  }

  void _connectWebSocket() {
    try {
      _channel = WebSocketChannel.connect(Uri.parse('ws://127.0.0.1:10330/ws'));
      _channel!.stream.listen((message) {
        final data = jsonDecode(message);
        if (data['type'] == 'log') {
          logs.add('> ${data['data']}');
          if (logs.length > 100) logs.removeAt(0); 
        } else if (data['type'] == 'progress') {
          int done = data['data']['done'];
          int total = data['data']['total'];
          progress = total > 0 ? done / total : 0.0;
        } else if (data['type'] == 'stage') {
          if (data['data'] == 'done' || data['data'] == 'error') {
            isProcessingNotifier.value = false; // Báo cho hệ thống: Đã xong
            status = data['data'] == 'done' ? "HOÀN TẤT" : "LỖI";
          } else {
            status = "ĐANG XỬ LÝ...";
          }
        }
        notifyListeners(); 
      }, onError: (error) {
        onError("Mất kết nối WebSocket: $error");
      });
    } catch (e) {
      onError("Lỗi khởi tạo WebSocket: $e");
    }
  }

  Future<void> startProcess() async {
    if (isProcessing) return;

    logs.clear();
    progress = 0.0;
    status = "ĐANG KHỞI TẠO...";
    isProcessingNotifier.value = true; // Báo cho hệ thống: Bắt đầu chạy
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
          "bib_max": 5
        }),
      );
      if (res.statusCode != 200) {
        throw Exception("Server trả về lỗi: ${res.body}");
      }
    } catch (e) {
      isProcessingNotifier.value = false; // Báo lỗi: Tắt trạng thái
      status = "LỖI KẾT NỐI API";
      notifyListeners();
      onError("Lỗi xử lý: $e");
    }
  }

  @override
  void dispose() {
    _channel?.sink.close();
    super.dispose();
  }
}
