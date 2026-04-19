import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../theme.dart';
import 'workspace_page.dart';
import 'search_page.dart';

class ProjectDetailPage extends StatefulWidget {
  final Map<String, dynamic> project;
  final VoidCallback onBack;

  const ProjectDetailPage({super.key, required this.project, required this.onBack});

  @override
  State<ProjectDetailPage> createState() => _ProjectDetailPageState();
}

class _ProjectDetailPageState extends State<ProjectDetailPage> {
  late Map<String, dynamic> project;

  @override
  void initState() {
    super.initState();
    project = Map.from(widget.project);
  }

  Future<void> _changeSourceDir() async {
    String? path = await FilePicker.platform.getDirectoryPath(dialogTitle: 'Chọn thư mục giải chạy (Ảnh/Video)');
    if (path != null) {
      try {
        final res = await http.put(
          Uri.parse('http://127.0.0.1:10330/projects/${project['id']}'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'source_dir': path}),
        );
        if (res.statusCode == 200) {
          setState(() {
            project['source_dir'] = path;
          });
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Đã cập nhật thư mục lưu trữ thành công!'), backgroundColor: AppTheme.success)
            );
          }
        } else {
          throw Exception('Lỗi cập nhật backend');
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Lỗi: $e'), backgroundColor: AppTheme.error)
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    bool hasIndex = project['has_index'] ?? false;

    return DefaultTabController(
      length: 2,
      initialIndex: hasIndex ? 1 : 0,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 24, 32, 0),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                IconButton(
                  icon: const Icon(Icons.arrow_back, color: AppTheme.textPrimary),
                  tooltip: 'Quay lại',
                  onPressed: widget.onBack,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'GIẢI CHẠY: ${project['name'].toString().toUpperCase()}',
                        style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, fontFamily: 'monospace', color: AppTheme.textPrimary),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          const Icon(Icons.folder_open, size: 16, color: AppTheme.textSecondary),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              project['source_dir'] ?? 'Chưa cấu hình thư mục đầu vào',
                              style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary, fontFamily: 'monospace'),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          const SizedBox(width: 8),
                          OutlinedButton.icon(
                            style: OutlinedButton.styleFrom(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                              minimumSize: Size.zero,
                              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                            ),
                            onPressed: _changeSourceDir,
                            icon: const Icon(Icons.edit, size: 14),
                            label: const Text('Đổi thư mục', style: TextStyle(fontSize: 12)),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 16),
                Container(
                  height: 40,
                  decoration: BoxDecoration(
                    color: AppTheme.bgElevated,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: AppTheme.border),
                  ),
                  child: TabBar(
                    isScrollable: true,
                    dividerColor: Colors.transparent,
                    indicatorSize: TabBarIndicatorSize.tab,
                    indicator: BoxDecoration(
                      color: AppTheme.bgActive,
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: AppTheme.textPrimary.withOpacity(0.3)),
                    ),
                    labelColor: AppTheme.textPrimary,
                    unselectedLabelColor: AppTheme.textSecondary,
                    tabs: const [
                      Tab(child: Padding(padding: EdgeInsets.symmetric(horizontal: 16), child: Text('1. CẤU HÌNH & XỬ LÝ'))),
                      Tab(child: Padding(padding: EdgeInsets.symmetric(horizontal: 16), child: Text('2. TÌM KIẾM & TRÍCH XUẤT'))),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 32),
            child: Divider(color: AppTheme.border, height: 32),
          ),
          Expanded(
            child: TabBarView(
              physics: const NeverScrollableScrollPhysics(),
              children: [
                WorkspacePage(project: project),
                SearchPage(project: project),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
