import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:file_picker/file_picker.dart';
import '../theme.dart';

class ProjectManagerPage extends StatefulWidget {
  final Function(Map<String, dynamic>) onOpenProject;
  const ProjectManagerPage({super.key, required this.onOpenProject});

  @override
  State<ProjectManagerPage> createState() => _ProjectManagerPageState();
}

class _ProjectManagerPageState extends State<ProjectManagerPage> {
  List<dynamic> _projects = [];
  bool _isLoading = true;

  final TextEditingController _nameCtrl = TextEditingController();
  final TextEditingController _sourceCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _fetchProjects();
  }

  void _showError(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message), backgroundColor: AppTheme.error),
      );
    }
  }

  Future<bool> _showConfirmDialog(String title, String content) async {
    return await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.bgSurface,
        title: Text(title, style: const TextStyle(color: AppTheme.textPrimary)),
        content: Text(content, style: const TextStyle(color: AppTheme.textSecondary)),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Hủy', style: TextStyle(color: AppTheme.textSecondary)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.error),
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Xác nhận', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    ) ?? false;
  }

  Future<void> _fetchProjects() async {
    try {
      final res = await http.get(Uri.parse('http://127.0.0.1:10330/projects')).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        setState(() {
          _projects = jsonDecode(res.body)['projects'];
          _isLoading = false;
        });
      } else {
        throw Exception("Server trả về mã lỗi: ${res.statusCode}");
      }
    } catch (e) {
      setState(() => _isLoading = false);
      _showError('Lỗi tải danh sách dự án: $e');
    }
  }

  Future<void> _createProject() async {
    if (_nameCtrl.text.isEmpty || _sourceCtrl.text.isEmpty) return;
    try {
      final res = await http.post(
        Uri.parse('http://127.0.0.1:10330/projects'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'name': _nameCtrl.text, 'source_dir': _sourceCtrl.text}),
      );
      if (res.statusCode == 200) {
        _nameCtrl.clear();
        _sourceCtrl.clear();
        _fetchProjects();
      } else {
        throw Exception("Server trả về mã lỗi: ${res.statusCode}");
      }
    } catch (e) {
      _showError('Lỗi tạo dự án: $e');
    }
  }

  Future<void> _deleteProject(String id, String name) async {
    final confirm = await _showConfirmDialog(
      "Xác nhận xóa dự án",
      "Bạn có chắc chắn muốn xóa dự án '$name' không? Dữ liệu FAISS index sẽ bị xóa, nhưng file gốc vẫn được giữ lại.",
    );
    if (!confirm) return;

    try {
      final res = await http.delete(Uri.parse('http://127.0.0.1:10330/projects/$id?delete_files=true'));
      if (res.statusCode == 200) {
        _fetchProjects();
      } else {
        throw Exception("Server trả về mã lỗi: ${res.statusCode}");
      }
    } catch (e) {
      _showError('Lỗi xóa dự án: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('QUẢN LÝ DỰ ÁN', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, fontFamily: 'monospace', color: AppTheme.textPrimary)),
          const Divider(color: AppTheme.border, height: 32),
          _buildCreateForm(),
          const SizedBox(height: 24),
          const Text('DANH SÁCH DỰ ÁN', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, fontFamily: 'monospace', letterSpacing: 1.5, color: AppTheme.textMuted)),
          const SizedBox(height: 8),
          Expanded(child: _buildProjectList()),
        ],
      ),
    );
  }

  Widget _buildCreateForm() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: AppTheme.bgSurface, border: Border.all(color: AppTheme.border), borderRadius: BorderRadius.circular(6)),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Tên Dự án *', style: TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                const SizedBox(height: 4),
                TextField(
                  controller: _nameCtrl,
                  style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
                  decoration: const InputDecoration(filled: true, fillColor: AppTheme.bgElevated, border: OutlineInputBorder(), isDense: true),
                ),
              ],
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Thư mục Nguồn *', style: TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _sourceCtrl,
                        readOnly: true,
                        style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
                        decoration: const InputDecoration(filled: true, fillColor: AppTheme.bgElevated, border: OutlineInputBorder(), isDense: true),
                      ),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: AppTheme.bgActive),
                      onPressed: () async {
                        try {
                          String? path = await FilePicker.platform.getDirectoryPath(
                            dialogTitle: 'Chọn thư mục Nguồn dự án',
                          );
                          if (path != null) {
                            setState(() => _sourceCtrl.text = path);
                          }
                        } catch (e) {
                          _showError('Lỗi mở thư mục: $e');
                        }
                      },
                      child: const Text('Duyệt...', style: TextStyle(color: AppTheme.textPrimary)),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(width: 16),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.textPrimary, padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16)),
            onPressed: _createProject,
            child: const Text('+ Tạo Mới', style: TextStyle(color: AppTheme.bgBase, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Widget _buildProjectList() {
    if (_isLoading) return const Center(child: CircularProgressIndicator());
    if (_projects.isEmpty) return const Center(child: Text('Chưa có dự án nào.', style: TextStyle(color: AppTheme.textSecondary)));

    return ListView.builder(
      itemCount: _projects.length,
      itemBuilder: (context, index) {
        final p = _projects[index];
        final hasIndex = p['has_index'] ?? false;
        return Card(
          color: AppTheme.bgSurface,
          margin: const EdgeInsets.only(bottom: 8),
          shape: RoundedRectangleBorder(side: const BorderSide(color: AppTheme.border), borderRadius: BorderRadius.circular(4)),
          child: ListTile(
            title: Text(p['name'], style: const TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.bold)),
            subtitle: Text(p['source_dir'], style: const TextStyle(color: AppTheme.textMuted, fontSize: 11)),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(color: hasIndex ? AppTheme.bgActive : AppTheme.bgBase, borderRadius: BorderRadius.circular(2)),
                  child: Text(hasIndex ? 'Đã Index' : 'Chưa Index', style: TextStyle(color: hasIndex ? AppTheme.textPrimary : AppTheme.textSecondary, fontSize: 11)),
                ),
                const SizedBox(width: 16),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: AppTheme.bgActive),
                  onPressed: () => widget.onOpenProject(p),
                  child: const Text('Mở', style: TextStyle(color: AppTheme.textPrimary)),
                ),
                const SizedBox(width: 8),
                IconButton(
                  icon: const Icon(Icons.delete, color: AppTheme.error, size: 20),
                  onPressed: () => _deleteProject(p['id'], p['name']),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
