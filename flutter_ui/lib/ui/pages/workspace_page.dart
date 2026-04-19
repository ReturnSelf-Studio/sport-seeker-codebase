import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';
import '../theme.dart';

class WorkspacePage extends StatefulWidget {
  final Map<String, dynamic> project;
  const WorkspacePage({super.key, required this.project});

  @override
  State<WorkspacePage> createState() => _WorkspacePageState();
}

class _WorkspacePageState extends State<WorkspacePage> {
  WebSocketChannel? _channel;
  List<String> _logs = [];
  double _progress = 0.0;
  String _status = "SẴN SÀNG QUÉT";
  bool _isProcessing = false;

  String _pipelineMode = 'face_bib';
  int _frameInterval = 30;

  @override
  void initState() {
    super.initState();
    _connectWebSocket();
  }

  void _showError(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message), backgroundColor: AppTheme.error),
      );
    }
  }

  void _connectWebSocket() {
    try {
      _channel = WebSocketChannel.connect(Uri.parse('ws://127.0.0.1:10330/ws'));
      _channel!.stream.listen((message) {
        final data = jsonDecode(message);
        setState(() {
          if (data['type'] == 'log') {
            _logs.add('> ${data['data']}');
            if (_logs.length > 100) _logs.removeAt(0); // Keep last 100 lines
          } else if (data['type'] == 'progress') {
            int done = data['data']['done'];
            int total = data['data']['total'];
            _progress = total > 0 ? done / total : 0.0;
          } else if (data['type'] == 'stage') {
            if (data['data'] == 'done' || data['data'] == 'error') {
              _isProcessing = false;
              _status = data['data'] == 'done' ? "HOÀN TẤT" : "LỖI";
            } else {
              _status = "ĐANG XỬ LÝ...";
            }
          }
        });
      }, onError: (error) {
        _showError("Mất kết nối WebSocket: $error");
      });
    } catch (e) {
      _showError("Lỗi khởi tạo WebSocket: $e");
    }
  }

  @override
  void dispose() {
    _channel?.sink.close();
    super.dispose();
  }

  Future<void> _toggleProcess() async {
    if (_isProcessing) {
      // 1. NGAY LẬP TỨC ngắt Loading UI để tránh bị treo chờ Backend
      setState(() {
        _isProcessing = false;
        _status = "ĐÃ GỬI LỆNH DỪNG";
      });
      
      // 2. Gọi API báo cho Python Backend biết để hủy vòng lặp ngầm
      try {
        await http.post(Uri.parse('http://127.0.0.1:10330/api/process/stop'));
      } catch (e) {
        print('Lỗi kết nối khi gửi lệnh dừng: $e');
      }
    } else {
      // Logic Bắt đầu tiến trình bình thường
      setState(() {
        _logs.clear();
        _progress = 0.0;
        _isProcessing = true;
        _status = "ĐANG KHỞI TẠO...";
      });
      try {
        final res = await http.post(
          Uri.parse('http://127.0.0.1:10330/process/start'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            "project_id": widget.project['id'],
            "pipeline_mode": _pipelineMode,
            "frame_interval": _frameInterval,
            "bib_min": 3,
            "bib_max": 5
          }),
        );
        if (res.statusCode != 200) {
          throw Exception("Server trả về lỗi: ${res.body}");
        }
      } catch (e) {
        setState(() {
          _isProcessing = false;
          _status = "LỖI KẾT NỐI API";
        });
        _showError("Lỗi xử lý: $e");
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildConfigSection(),
          const SizedBox(height: 16),
          _buildControlSection(),
          const SizedBox(height: 16),
          Expanded(child: _buildLogSection()),
        ],
      ),
    );
  }

  Widget _buildConfigSection() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
          color: AppTheme.bgSurface,
          border: Border.all(color: AppTheme.border),
          borderRadius: BorderRadius.circular(6)),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Luồng xử lý',
                    style:
                        TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  value: _pipelineMode,
                  dropdownColor: AppTheme.bgElevated,
                  style: const TextStyle(
                      color: AppTheme.textPrimary, fontSize: 13),
                  decoration: const InputDecoration(
                      filled: true,
                      fillColor: AppTheme.bgElevated,
                      border: OutlineInputBorder(),
                      isDense: true),
                  items: const [
                    DropdownMenuItem<String>(
                        value: 'face_bib', child: Text('Kết hợp (Face & BIB)')),
                    DropdownMenuItem<String>(
                        value: 'face_only',
                        child: Text('Chỉ khuôn mặt (Face)')),
                    DropdownMenuItem<String>(
                        value: 'bib_only', child: Text('Chỉ số BIB')),
                  ],
                  onChanged: _isProcessing
                      ? null
                      : (v) => setState(() => _pipelineMode = v!),
                ),
              ],
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Tần suất trích xuất Video',
                    style:
                        TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                const SizedBox(height: 8),
                DropdownButtonFormField<int>(
                  value: _frameInterval,
                  dropdownColor: AppTheme.bgElevated,
                  style: const TextStyle(
                      color: AppTheme.textPrimary, fontSize: 13),
                  decoration: const InputDecoration(
                      filled: true,
                      fillColor: AppTheme.bgElevated,
                      border: OutlineInputBorder(),
                      isDense: true),
                  items: const [
                    DropdownMenuItem<int>(
                        value: 60,
                        child: Text('Quét rất nhanh (Thưa khung hình)')),
                    DropdownMenuItem<int>(
                        value: 30, child: Text('Quét trung bình (Cân bằng)')),
                    DropdownMenuItem<int>(
                        value: 10,
                        child: Text('Quét kỹ - Chậm (Dày khung hình)')),
                  ],
                  onChanged: _isProcessing
                      ? null
                      : (v) => setState(() => _frameInterval = v!),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildControlSection() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
          color: AppTheme.bgSurface,
          border: Border.all(color: AppTheme.border),
          borderRadius: BorderRadius.circular(6)),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  if (_isProcessing) ...[
                    const SizedBox(
                      width: 14,
                      height: 14,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: AppTheme.warning),
                    ),
                    const SizedBox(width: 8),
                  ],
                  Text(
                    'Trạng thái: $_status${_isProcessing && _progress > 0 ? ' (${(_progress * 100).toStringAsFixed(1)}%)' : ''}',
                    style: TextStyle(
                        color: _status == "HOÀN TẤT"
                            ? AppTheme.success
                            : AppTheme.warning,
                        fontWeight: FontWeight.bold),
                  ),
                ],
              ),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor:
                      _isProcessing ? AppTheme.error : AppTheme.textPrimary,
                  padding:
                      const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                ),
                onPressed: _toggleProcess,
                child: Text(_isProcessing ? '■ DỪNG XỬ LÝ' : '▶ BẮT ĐẦU XỬ LÝ',
                    style: TextStyle(
                        color: _isProcessing ? Colors.white : AppTheme.bgBase,
                        fontWeight: FontWeight.bold)),
              ),
            ],
          ),
          const SizedBox(height: 16),
          LinearProgressIndicator(
              value: (_isProcessing && _progress == 0.0) ? null : _progress,
              backgroundColor: AppTheme.bgElevated,
              color: AppTheme.success,
              minHeight: 6),
        ],
      ),
    );
  }

  Widget _buildLogSection() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
          color: Colors.black,
          border: Border.all(color: AppTheme.border),
          borderRadius: BorderRadius.circular(6)),
      child: ListView.builder(
        itemCount: _logs.length,
        itemBuilder: (context, index) {
          return Text(_logs[index],
              style: const TextStyle(
                  color: Colors.greenAccent,
                  fontFamily: 'monospace',
                  fontSize: 12));
        },
      ),
    );
  }
}
