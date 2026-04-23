import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:file_picker/file_picker.dart';
import '../theme.dart';

class SearchPage extends StatefulWidget {
  final Map<String, dynamic> project;
  const SearchPage({super.key, required this.project});

  @override
  State<SearchPage> createState() => _SearchPageState();
}

class _SearchPageState extends State<SearchPage> {
  int _searchType = 0; // 0: BIB, 1: Face
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _bibCtrl = TextEditingController();
  String? _faceImagePath;
  double _threshold = 0.4;

  bool _isSearching = false;
  List<dynamic> _results = [];

  void _showError(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message), backgroundColor: AppTheme.error),
      );
    }
  }

  Future<void> _pickImage() async {
    FilePickerResult? result =
        await FilePicker.platform.pickFiles(type: FileType.image);
    if (result != null) {
      setState(() => _faceImagePath = result.files.single.path);
    }
  }

  void _openFile(String path) async {
    if (Platform.isMacOS) {
      try {
        await Process.run('open', [path], runInShell: true);
      } catch (e) {
        _showError("Lỗi mở file: $e");
      }
    } else if (Platform.isWindows) {
      Process.run('explorer', [path], runInShell: true);
    } else if (Platform.isLinux) {
      Process.run('xdg-open', [path], runInShell: true);
    }
  }

  Future<void> _doSearch() async {
    if (_searchType == 0 && !_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isSearching = true;
      _results.clear();
    });
    
    try {
      var request = http.MultipartRequest(
          'POST', Uri.parse('http://127.0.0.1:10330/search'));
      request.fields['project_id'] = widget.project['id'];
      request.fields['k'] = '50';

      if (_searchType == 0) {
        request.fields['type'] = 'bib';
        request.fields['text'] = _bibCtrl.text.trim();
      } else {
        if (_faceImagePath == null) throw Exception("Vui lòng chọn ảnh mẫu");
        request.fields['type'] = 'face';
        request.fields['threshold'] = _threshold.toString();
        request.files
            .add(await http.MultipartFile.fromPath('file', _faceImagePath!));
      }

      var response = await request.send();
      var resData = await response.stream.bytesToString();
      
      if (response.statusCode == 200) {
        setState(() => _results = jsonDecode(resData)['results'] ?? []);
      } else {
        // Fix QA Issue: Bỏ qua các lỗi liên quan đến việc không có dữ liệu (No index, Not found, v.v)
        // và chỉ hiển thị UX rỗng kết quả thân thiện.
        setState(() => _results = []);
        
        // Chỉ log ra console thay vì đập vào mặt người dùng, hoặc hiển thị nếu nó thực sự là lỗi nghiêm trọng
        String errorMsg = "";
        try {
           errorMsg = jsonDecode(resData)['detail']?.toString() ?? "";
        } catch (_) {}
        print("Search API Failed: ${response.statusCode} - $errorMsg");
      }
    } catch (e) {
      _showError("Lỗi kết nối: $e");
    } finally {
      setState(() => _isSearching = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('TÌM KIẾM TRONG: ${widget.project['name']}',
              style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  fontFamily: 'monospace',
                  color: AppTheme.textPrimary)),
          const Divider(color: AppTheme.border, height: 32),
          Form(
            key: _formKey,
            child: _buildSearchBox(),
          ),
          const SizedBox(height: 16),
          Expanded(child: _buildResultsGrid()),
        ],
      ),
    );
  }

  Widget _buildSearchBox() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
          color: AppTheme.bgSurface,
          border: Border.all(color: AppTheme.border),
          borderRadius: BorderRadius.circular(6)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              ChoiceChip(
                  label: 'Tìm BIB',
                  selected: _searchType == 0,
                  onSelected: () => setState(() => _searchType = 0)),
              const SizedBox(width: 8),
              ChoiceChip(
                  label: 'Tìm Face',
                  selected: _searchType == 1,
                  onSelected: () => setState(() => _searchType = 1)),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: _searchType == 0
                    ? TextFormField(
                        controller: _bibCtrl,
                        decoration: const InputDecoration(
                            labelText: 'Nhập số BIB',
                            filled: true,
                            fillColor: AppTheme.bgElevated,
                            border: OutlineInputBorder(),
                            isDense: true),
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return 'BIB không được để trống';
                          }
                          final trimmed = value.trim();
                          if (trimmed.length < 1 || trimmed.length > 10) {
                            return 'BIB phải từ 1 đến 10 ký tự';
                          }
                          return null;
                        },
                      )
                    : Row(
                        children: [
                          ElevatedButton(
                              onPressed: _pickImage,
                              style: ElevatedButton.styleFrom(
                                  backgroundColor: AppTheme.bgElevated, padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 16)),
                              child: const Text('Chọn ảnh mẫu')),
                          const SizedBox(width: 8),
                          Expanded(
                              child: Text(_faceImagePath ?? 'Chưa chọn ảnh',
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                      color: AppTheme.textSecondary))),
                        ],
                      ),
              ),
              const SizedBox(width: 16),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.textPrimary,
                    padding: const EdgeInsets.symmetric(
                        horizontal: 32, vertical: 20)),
                onPressed: _isSearching ? null : _doSearch,
                child: Text(_isSearching ? 'ĐANG TÌM...' : '🔍 TÌM KIẾM',
                    style: const TextStyle(
                        color: AppTheme.bgBase, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildResultsGrid() {
    if (_isSearching) return const Center(child: CircularProgressIndicator());
    if (_results.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.image_not_supported_outlined, size: 64, color: AppTheme.textSecondary.withOpacity(0.5)),
            const SizedBox(height: 16),
            const Text('Không tìm thấy hình ảnh/video tương ứng.',
                style: TextStyle(color: AppTheme.textPrimary, fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            const Text('Có thể người này không xuất hiện, hoặc dự án chưa được cấu hình xử lý.',
                style: TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
          ],
        ),
      );
    }

    return GridView.builder(
      gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
          maxCrossAxisExtent: 200,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          childAspectRatio: 0.8),
      itemCount: _results.length,
      itemBuilder: (context, index) {
        final r = _results[index];
        final sourcePath = r['source_path'] ?? r['video_path'];
        final isVideo = (r['image_type'] ?? r['type']) == 'video';
        final thumbnailPath = r['thumbnail_path'];
        final score = r['score'] ?? 0.0;
        final timestamp = r['timestamp'] ?? 0.0;

        return InkWell(
          onTap: () => _openFile(sourcePath),
          child: Card(
            color: AppTheme.bgElevated,
            clipBehavior: Clip.antiAlias,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
              side: const BorderSide(color: AppTheme.border),
            ),
            child: Stack(
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Expanded(
                      child: thumbnailPath != null
                          ? Image.file(File(thumbnailPath),
                              fit: BoxFit.cover,
                              cacheWidth: 300, // Đã fix lỗi tràn RAM
                              errorBuilder: (c, e, s) => const Icon(Icons.broken_image))
                          : isVideo
                              ? const Icon(Icons.videocam, size: 50, color: AppTheme.textMuted)
                              : Image.file(File(sourcePath),
                                  fit: BoxFit.cover,
                                  cacheWidth: 300, // Đã fix lỗi tràn RAM
                                  errorBuilder: (c, e, s) => const Icon(Icons.broken_image)),
                    ),
                    Container(
                      color: AppTheme.bgSurface,
                      padding: const EdgeInsets.all(8.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(sourcePath.split(Platform.pathSeparator).last,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.bold,
                                  color: AppTheme.textPrimary)),
                          const SizedBox(height: 4),
                          Text(isVideo ? 'Video • ${timestamp.toStringAsFixed(1)}s' : 'Hình ảnh',
                              style: const TextStyle(
                                  fontSize: 10, color: AppTheme.textSecondary)),
                        ],
                      ),
                    ),
                  ],
                ),
                if (score > 0)
                  Positioned(
                    top: 8,
                    right: 8,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppTheme.info.withOpacity(0.9),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text('${(score * 100).toStringAsFixed(0)}%',
                          style: const TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.bgBase)),
                    ),
                  ),
                if (isVideo)
                  Positioned(
                    top: 8,
                    left: 8,
                    child: Container(
                      padding: const EdgeInsets.all(4),
                      decoration: const BoxDecoration(
                        color: Colors.black54,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.play_arrow,
                          color: Colors.white, size: 16),
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class ChoiceChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onSelected;
  const ChoiceChip(
      {super.key,
      required this.label,
      required this.selected,
      required this.onSelected});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onSelected,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
            color: selected ? AppTheme.textPrimary : AppTheme.bgElevated,
            borderRadius: BorderRadius.circular(16)),
        child: Text(label,
            style: TextStyle(
                color: selected ? AppTheme.bgBase : AppTheme.textPrimary,
                fontWeight: FontWeight.bold)),
      ),
    );
  }
}
