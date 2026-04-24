import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:file_picker/file_picker.dart';

class SearchActions extends ChangeNotifier {
  final String projectId;
  final Function(String) onError;

  int searchType = 0; // 0: BIB, 1: Face
  final TextEditingController bibCtrl = TextEditingController();
  String? faceImagePath;
  double threshold = 0.4;

  bool isSearching = false;
  List<dynamic> results = [];

  SearchActions({required this.projectId, required this.onError});

  void setSearchType(int type) {
    searchType = type;
    notifyListeners();
  }

  Future<void> pickImage() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles(type: FileType.image);
    if (result != null) {
      faceImagePath = result.files.single.path;
      notifyListeners();
    }
  }

  void openFile(String path) async {
    if (Platform.isMacOS) {
      try {
        await Process.run('open', [path], runInShell: true);
      } catch (e) {
        onError("Lỗi mở file: $e");
      }
    } else if (Platform.isWindows) {
      Process.run('explorer', [path], runInShell: true);
    } else if (Platform.isLinux) {
      Process.run('xdg-open', [path], runInShell: true);
    }
  }

  Future<void> doSearch(bool isFormValid) async {
    if (searchType == 0 && !isFormValid) return;

    isSearching = true;
    results.clear();
    notifyListeners();
    
    try {
      var request = http.MultipartRequest('POST', Uri.parse('http://127.0.0.1:10330/search'));
      request.fields['project_id'] = projectId;
      request.fields['k'] = '50';

      if (searchType == 0) {
        request.fields['type'] = 'bib';
        request.fields['text'] = bibCtrl.text.trim();
      } else {
        if (faceImagePath == null) throw Exception("Vui lòng chọn ảnh mẫu");
        request.fields['type'] = 'face';
        request.fields['threshold'] = threshold.toString();
        request.files.add(await http.MultipartFile.fromPath('file', faceImagePath!));
      }

      var response = await request.send();
      var resData = await response.stream.bytesToString();
      
      if (response.statusCode == 200) {
        results = jsonDecode(resData)['results'] ?? [];
      } else {
        results = [];
        print("Search API Failed: ${response.statusCode}");
      }
    } catch (e) {
      onError("Lỗi kết nối: $e");
    } finally {
      isSearching = false;
      notifyListeners();
    }
  }

  @override
  void dispose() {
    bibCtrl.dispose();
    super.dispose();
  }
}
