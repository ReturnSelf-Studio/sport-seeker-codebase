import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class ProjectManagerActions extends ChangeNotifier {
  final Function(String) onError;
  final Future<bool> Function(String, String) onShowConfirm;

  List<dynamic> projects = [];
  bool isLoading = true;

  final TextEditingController nameCtrl = TextEditingController();
  final TextEditingController sourceCtrl = TextEditingController();

  ProjectManagerActions({required this.onError, required this.onShowConfirm}) {
    fetchProjects();
  }

  // LOGIC FIX TICKET 27: Kiểm tra trùng tên dự án (Không phân biệt hoa/thường)
  bool isNameDuplicate(String name) {
    final lowerName = name.trim().toLowerCase();
    return projects.any((p) => p['name'].toString().toLowerCase() == lowerName);
  }

  Future<void> fetchProjects() async {
    isLoading = true;
    notifyListeners();
    try {
      final res = await http.get(Uri.parse('http://127.0.0.1:10330/projects')).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        projects = jsonDecode(res.body)['projects'];
      } else {
        throw Exception("Server trả về mã lỗi: ${res.statusCode}");
      }
    } catch (e) {
      onError('Lỗi tải danh sách dự án: $e');
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  Future<void> createProject(bool isValid) async {
    if (!isValid) return;
    if (sourceCtrl.text.isEmpty) {
      onError("Vui lòng chọn thư mục Nguồn");
      return;
    }

    try {
      final res = await http.post(
        Uri.parse('http://127.0.0.1:10330/projects'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'name': nameCtrl.text.trim(), 'source_dir': sourceCtrl.text}),
      );
      if (res.statusCode == 200) {
        nameCtrl.clear();
        sourceCtrl.clear();
        await fetchProjects(); // Refresh lại danh sách
      } else {
        throw Exception("Server trả về mã lỗi: ${res.statusCode}");
      }
    } catch (e) {
      onError('Lỗi tạo dự án: $e');
    }
  }

  Future<void> deleteProject(String id, String name) async {
    final confirm = await onShowConfirm(
      "Xác nhận xóa dự án",
      "Bạn có chắc chắn muốn xóa dự án '$name' không? Dữ liệu FAISS index sẽ bị xóa, nhưng file gốc vẫn được giữ lại.",
    );
    if (confirm != true) return;

    try {
      final res = await http.delete(Uri.parse('http://127.0.0.1:10330/projects/$id?delete_files=true'));
      if (res.statusCode == 200) {
        await fetchProjects(); // Refresh lại danh sách
      } else {
        throw Exception("Server trả về mã lỗi: ${res.statusCode}");
      }
    } catch (e) {
      onError('Lỗi xóa dự án: $e');
    }
  }

  void setSourceDir(String path) {
    sourceCtrl.text = path;
    notifyListeners();
  }

  @override
  void dispose() {
    nameCtrl.dispose();
    sourceCtrl.dispose();
    super.dispose();
  }
}
