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
        await Process.run(
          'open',
          [path],
          runInShell: true,
        );
      } catch (e) {
        _showError("Lỗi mở file: $e");
      }
    } else if (Platform.isWindows) {
      Process.run('explorer $path', [], runInShell: true);
    } else if (Platform.isLinux) {
      Process.run('xdg-open $path', [], runInShell: true);
    }
  }

  Future<void> _doSearch() async {
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
        if (_bibCtrl.text.isEmpty) throw Exception("Vui lòng nhập BIB");
        request.fields['type'] = 'bib';
        request.fields['text'] = _bibCtrl.text;
      } else {
        if (_faceImagePath == null) throw Exception("Vui lòng chọn ảnh mẫu");
        request.fields['type'] = 'face';
        request.fields['threshold'] = _threshold.toString();
        request.files
            .add(await http.MultipartFile.fromPath('file', _faceImagePath!));
      }

      var response = await request.send();
      if (response.statusCode == 200) {
        var resData = await response.stream.bytesToString();
        setState(() => _results = jsonDecode(resData)['results']);
      } else {
        throw Exception("Server báo lỗi HTTP ${response.statusCode}");
      }
    } catch (e) {
      _showError("Lỗi tìm kiếm: $e");
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
          _buildSearchBox(),
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
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(
                child: _searchType == 0
                    ? TextField(
                        controller: _bibCtrl,
                        decoration: const InputDecoration(
                            labelText: 'Nhập số BIB',
                            filled: true,
                            fillColor: AppTheme.bgElevated,
                            border: OutlineInputBorder()))
                    : Row(
                        children: [
                          ElevatedButton(
                              onPressed: _pickImage,
                              style: ElevatedButton.styleFrom(
                                  backgroundColor: AppTheme.bgElevated),
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
      return const Center(
          child: Text('Không có kết quả.',
              style: TextStyle(color: AppTheme.textSecondary)));
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
                              errorBuilder: (c, e, s) => const Icon(Icons.broken_image))
                          : isVideo
                              ? const Icon(Icons.videocam, size: 50, color: AppTheme.textMuted)
                              : Image.file(File(sourcePath),
                                  fit: BoxFit.cover,
                                  errorBuilder: (c, e, s) => const Icon(Icons.broken_image)),
                    ),
                    Container(
                      color: AppTheme.bgSurface,
                      padding: const EdgeInsets.all(8.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(sourcePath.split('/').last,
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
