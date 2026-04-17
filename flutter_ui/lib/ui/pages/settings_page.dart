import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:file_picker/file_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/backend_manager.dart';
import '../../core/model_manager.dart';
import '../../core/env.dart';
import '../theme.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  bool _isEngineHealthy = false;
  bool _isLoading = false;

  String _modelsSize = "Đang tính...";
  String _ocrCacheSize = "Đang tính...";
  String _hfCacheSize = "Đang tính...";
  String _customModelPath = "";

  @override
  void initState() {
    super.initState();
    _loadPrefs();
    _refreshStatus();
  }

  Future<void> _loadPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _customModelPath = prefs.getString('custom_model_path') ?? '';
    });
  }

  String get _homePath {
    if (Platform.isWindows) {
      return Platform.environment['USERPROFILE'] ?? 'C:\\';
    }
    return Platform.environment['HOME'] ?? '/';
  }

  String get _currentModelsRoot {
    return _customModelPath.isNotEmpty
        ? _customModelPath
        : '$_homePath/SportSeeker/models';
  }

  Future<String> _getDirSize(String path) async {
    final dir = Directory(path);
    if (!await dir.exists()) return "0.0 MB";
    int totalSize = 0;
    try {
      await for (var file in dir.list(recursive: true, followLinks: false)) {
        if (file is File) totalSize += await file.length();
      }
    } catch (e) {
      return "Lỗi đọc file";
    }

    if (totalSize > 1024 * 1024 * 1024) {
      return "${(totalSize / (1024 * 1024 * 1024)).toStringAsFixed(2)} GB";
    }
    return "${(totalSize / (1024 * 1024)).toStringAsFixed(1)} MB";
  }

  Future<void> _calculateSizes() async {
    final modelsSize = await _getDirSize(_currentModelsRoot);
    final paddleSize1 = await _getDirSize('$_homePath/.paddlex');
    final paddleSize2 = await _getDirSize('$_homePath/.paddleocr');
    final paddleSize3 = await _getDirSize('$_homePath/.paddle');
    final hfSize = await _getDirSize('$_homePath/.cache/huggingface/hub');

    if (mounted) {
      setState(() {
        _modelsSize = modelsSize;
        _ocrCacheSize = "$paddleSize1 (+ $paddleSize2) (+ $paddleSize3)";
        _hfCacheSize = hfSize;
      });
    }
  }

  Future<bool> _showConfirmDialog(String title, String content) async {
    return await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            backgroundColor: AppTheme.bgSurface,
            title: Text(title,
                style: const TextStyle(color: AppTheme.textPrimary)),
            content: Text(content,
                style: const TextStyle(color: AppTheme.textSecondary)),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(false),
                child: const Text('Hủy',
                    style: TextStyle(color: AppTheme.textSecondary)),
              ),
              ElevatedButton(
                style:
                    ElevatedButton.styleFrom(backgroundColor: AppTheme.error),
                onPressed: () => Navigator.of(context).pop(true),
                child: const Text('Xác nhận',
                    style: TextStyle(color: Colors.white)),
              ),
            ],
          ),
        ) ??
        false;
  }

  Future<void> _changeModelPath() async {
    String? path = await FilePicker.platform
        .getDirectoryPath(dialogTitle: 'Chọn thư mục chứa models');
    if (path != null) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('custom_model_path', path);
      setState(() {
        _customModelPath = path;
      });
      _calculateSizes();
      _showMsg(
          "Đã lưu thư mục Model. Vui lòng Khởi động lại Engine để áp dụng.",
          isSuccess: true);
    }
  }

  Future<void> _resetModelPath() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('custom_model_path');
    setState(() {
      _customModelPath = "";
    });
    _calculateSizes();
    _showMsg("Đã khôi phục thư mục Model về Mặc định.", isSuccess: true);
  }

  Future<void> _refreshStatus() async {
    setState(() => _isLoading = true);
    await _calculateSizes();
    try {
      final res = await http
          .get(Uri.parse('http://127.0.0.1:10330/health'))
          .timeout(const Duration(seconds: 1));
      _isEngineHealthy = res.statusCode == 200;
    } catch (_) {
      _isEngineHealthy = false;
    }
    if (mounted) setState(() => _isLoading = false);
  }

  Future<void> _restartEngine() async {
    _showMsg("Đang gửi lệnh Shutdown tới Engine...");
    try {
      await http
          .post(Uri.parse('http://127.0.0.1:10330/shutdown'))
          .timeout(const Duration(seconds: 1));
    } catch (_) {}

    _showMsg("Đang khởi động lại...");
    await BackendManager().startBackend();
    await _refreshStatus();
    _showMsg("Đã khởi động lại AI Engine thành công!", isSuccess: true);
  }

  Future<void> _forceKillEngine() async {
    final confirm = await _showConfirmDialog(
      "CẢNH BÁO: Force Kill Engine",
      "Hành động này sẽ ép dừng ngay lập tức toàn bộ tiến trình AI ngầm. Dữ liệu đang xử lý dở dang có thể bị mất. Bạn có chắc chắn không?",
    );
    if (!confirm) return;

    _showMsg("Đang ép dừng toàn bộ tiến trình AI ngầm...");
    try {
      if (Platform.isWindows) {
        await Process.run(
            'taskkill', ['/F', '/IM', 'SportSeekerAPI.exe', '/T']);
        await Process.run('cmd', [
          '/c',
          'for /f "tokens=5" %a in (\'netstat -aon ^| findstr :10330\') do taskkill /F /PID %a'
        ]);
      } else if (Platform.isMacOS) {
        await Process.run('pkill', ['-9', '-f', 'SportSeekerAPI']);
        await Process.run('sh', ['-c', 'lsof -t -i :10330 | xargs kill -9']);
      }
      _isEngineHealthy = false;
      setState(() {});
      _showMsg("Đã ép dừng tiến trình thành công!", isSuccess: true);
    } catch (e) {
      _showMsg("Lỗi ép dừng: $e");
    }
  }

  Future<void> _deleteDirectory(String title, List<String> paths) async {
    final confirm = await _showConfirmDialog(
      "Xác nhận dọn dẹp",
      "Bạn chuẩn bị xóa $title. Các models sẽ phải tải lại ở lần chạy tiếp theo. Tiếp tục?",
    );
    if (!confirm) return;

    _showMsg("Đang xoá $title...");
    bool hasError = false;
    for (String path in paths) {
      final dir = Directory(path);
      if (await dir.exists()) {
        try {
          await dir.delete(recursive: true);
        } catch (e) {
          hasError = true;
        }
      }
    }
    await _calculateSizes();
    if (hasError) {
      _showMsg("Có lỗi xảy ra khi xoá một số file đang được sử dụng.");
    } else {
      _showMsg("Đã dọn dẹp $title thành công!", isSuccess: true);
    }
  }

  void _showMsg(String msg, {bool isSuccess = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: isSuccess ? AppTheme.success : AppTheme.error,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('CÀI ĐẶT HỆ THỐNG',
                  style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      fontFamily: 'monospace',
                      color: AppTheme.textPrimary)),
              IconButton(
                icon: const Icon(Icons.refresh, color: AppTheme.info),
                onPressed: _refreshStatus,
                tooltip: 'Làm mới trạng thái',
              ),
            ],
          ),
          const Divider(color: AppTheme.border, height: 32),
          Expanded(
            child: ListView(
              children: [
                _buildAboutCard(),
                const SizedBox(height: 24),
                _buildSectionTitle('2. QUẢN LÝ TIẾN TRÌNH AI (ENGINE)'),
                _buildCard(
                  child: Column(
                    children: [
                      ListTile(
                        leading: Container(
                          width: 12,
                          height: 12,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: _isEngineHealthy
                                ? AppTheme.success
                                : AppTheme.error,
                          ),
                        ),
                        title: const Text('Kết nối Backend (Port 10330)',
                            style: TextStyle(
                                color: AppTheme.textPrimary,
                                fontWeight: FontWeight.bold)),
                        subtitle: Text(
                            _isEngineHealthy
                                ? 'Đang hoạt động bình thường'
                                : 'Mất kết nối hoặc đang tắt',
                            style: const TextStyle(
                                color: AppTheme.textSecondary, fontSize: 12)),
                        trailing: ElevatedButton(
                          style: ElevatedButton.styleFrom(
                              backgroundColor: AppTheme.bgActive),
                          onPressed: _isLoading ? null : _restartEngine,
                          child: const Text('Khởi động lại Engine',
                              style: TextStyle(color: AppTheme.textPrimary)),
                        ),
                      ),
                      const Divider(color: AppTheme.border),
                      ListTile(
                        leading: const Icon(Icons.warning_amber_rounded,
                            color: AppTheme.warning),
                        title: const Text('Ép dừng (Force Kill)',
                            style: TextStyle(
                                color: AppTheme.textPrimary,
                                fontWeight: FontWeight.bold)),
                        subtitle: const Text(
                            'Dùng khi app bị treo cứng, không thể xử lý ảnh/video',
                            style: TextStyle(
                                color: AppTheme.textSecondary, fontSize: 12)),
                        trailing: ElevatedButton(
                          style: ElevatedButton.styleFrom(
                              backgroundColor:
                                  AppTheme.error.withValues(alpha: 0.2)),
                          onPressed: _forceKillEngine,
                          child: const Text('Force Kill',
                              style: TextStyle(color: AppTheme.error)),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),
                _buildSectionTitle('3. QUẢN LÝ AI MODELS OFFLINE'),
                _buildCard(
                  child: Column(
                    children: [
                      ListTile(
                        leading: const Icon(Icons.cloud_download,
                            color: AppTheme.info),
                        title: const Text('Kho Dữ Liệu AI Models',
                            style: TextStyle(
                                color: AppTheme.textPrimary,
                                fontWeight: FontWeight.bold)),
                        subtitle: ValueListenableBuilder<String>(
                          valueListenable: ModelManager().statusMessage,
                          builder: (context, msg, child) {
                            return Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('Trạng thái: $msg',
                                    style: const TextStyle(
                                        color: AppTheme.textSecondary,
                                        fontSize: 12)),
                                const SizedBox(height: 8),
                                ValueListenableBuilder<double?>(
                                  valueListenable:
                                      ModelManager().downloadProgress,
                                  builder: (context, progress, child) {
                                    if (progress == null) {
                                      return const SizedBox.shrink();
                                    }
                                    return LinearProgressIndicator(
                                      value: progress,
                                      backgroundColor: AppTheme.bgElevated,
                                      color: AppTheme.success,
                                      minHeight: 6,
                                    );
                                  },
                                ),
                              ],
                            );
                          },
                        ),
                        trailing: ValueListenableBuilder<String>(
                          valueListenable: ModelManager().statusMessage,
                          builder: (context, msg, child) {
                            bool isDownloading = ModelManager().isDownloading;
                            return ElevatedButton.icon(
                              style: ElevatedButton.styleFrom(
                                backgroundColor: isDownloading
                                    ? AppTheme.warning
                                    : AppTheme.bgActive,
                                foregroundColor: AppTheme.textPrimary,
                              ),
                              onPressed: () {
                                if (isDownloading) {
                                  ModelManager().pauseDownload();
                                } else {
                                  ModelManager().checkAndDownloadModels();
                                }
                              },
                              icon: Icon(
                                  isDownloading ? Icons.pause : Icons.download,
                                  size: 18),
                              label: Text(isDownloading
                                  ? 'Tạm Dừng'
                                  : 'Tải / Cập Nhật Models'),
                            );
                          },
                        ),
                      ),
                      const Divider(color: AppTheme.border),
                      ListTile(
                        leading: const Icon(Icons.folder, color: AppTheme.info),
                        title: const Text('Vị trí thư mục lưu Models',
                            style: TextStyle(
                                color: AppTheme.textPrimary,
                                fontWeight: FontWeight.bold)),
                        subtitle: Text(
                            _customModelPath.isEmpty
                                ? 'Mặc định: ~/SportSeeker/models'
                                : _customModelPath,
                            style: const TextStyle(
                                color: AppTheme.textSecondary, fontSize: 12)),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            if (_customModelPath.isNotEmpty)
                              TextButton(
                                onPressed: _resetModelPath,
                                child: const Text('Về Mặc Định',
                                    style: TextStyle(
                                        color: AppTheme.textSecondary)),
                              ),
                            OutlinedButton(
                              onPressed: _changeModelPath,
                              child: const Text('Thay Đổi',
                                  style:
                                      TextStyle(color: AppTheme.textPrimary)),
                            ),
                          ],
                        ),
                      ),
                      const Divider(color: AppTheme.border),
                      ListTile(
                        leading:
                            const Icon(Icons.storage, color: AppTheme.info),
                        title: const Text(
                            'Dữ liệu InsightFace & Các Models khác',
                            style: TextStyle(
                                color: AppTheme.textPrimary,
                                fontWeight: FontWeight.bold)),
                        subtitle: Text('Dung lượng đang chiếm: $_modelsSize',
                            style: const TextStyle(
                                color: AppTheme.textSecondary, fontSize: 12)),
                        trailing: OutlinedButton(
                          onPressed: () => _deleteDirectory(
                              'Toàn bộ Models Offline', [_currentModelsRoot]),
                          child: const Text('Dọn Dẹp',
                              style: TextStyle(color: AppTheme.error)),
                        ),
                      ),
                      const Divider(color: AppTheme.border),
                      ListTile(
                        leading:
                            const Icon(Icons.text_fields, color: AppTheme.info),
                        title: const Text('PaddleOCR Cache',
                            style: TextStyle(
                                color: AppTheme.textPrimary,
                                fontWeight: FontWeight.bold)),
                        subtitle: Text('Dung lượng: $_ocrCacheSize',
                            style: const TextStyle(
                                color: AppTheme.textSecondary, fontSize: 12)),
                        trailing: OutlinedButton(
                          onPressed: () => _deleteDirectory('PaddleOCR Cache', [
                            '$_homePath/.paddlex',
                            '$_homePath/.paddleocr',
                            '$_homePath/.paddle'
                          ]),
                          child: const Text('Xoá Cache OCR',
                              style: TextStyle(color: AppTheme.error)),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAboutCard() {
    return _buildCard(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Row(
          children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                color: AppTheme.bgActive,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppTheme.border),
                image: const DecorationImage(
                  image: AssetImage('assets/icons/app_icon.png'),
                  fit: BoxFit.cover,
                ),
              ),
            ),
            const SizedBox(width: 20),
            const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Sport Seeker',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.textPrimary,
                    letterSpacing: 0.5,
                  ),
                ),
                SizedBox(height: 4),
                Text(
                  'Phiên bản v${Env.fullVersion}',
                  style: TextStyle(
                      fontSize: 12,
                      color: AppTheme.textMuted,
                      fontFamily: 'monospace'),
                ),
                SizedBox(height: 8),
                Text(
                  'Giải pháp nhận diện khuôn mặt và số BIB offline.\nPowered By AIBUS 🚀',
                  style: TextStyle(
                      fontSize: 13, color: AppTheme.textSecondary, height: 1.4),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0, left: 4.0),
      child: Text(
        title,
        style: const TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.bold,
            fontFamily: 'monospace',
            letterSpacing: 1.5,
            color: AppTheme.textMuted),
      ),
    );
  }

  Widget _buildCard({required Widget child}) {
    return Container(
      decoration: BoxDecoration(
        color: AppTheme.bgSurface,
        border: Border.all(color: AppTheme.border),
        borderRadius: BorderRadius.circular(8),
      ),
      child: child,
    );
  }
}
