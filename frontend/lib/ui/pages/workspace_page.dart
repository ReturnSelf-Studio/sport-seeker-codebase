import 'package:flutter/material.dart';
import 'package:window_manager/window_manager.dart';
import '../theme.dart';
import 'workspace/workspace_actions.dart';
import 'workspace/workspace_config_widget.dart';
import 'workspace/workspace_control_widget.dart';
import 'workspace/workspace_log_widget.dart';
import 'workspace/workspace_prescan_widget.dart';

class WorkspacePage extends StatefulWidget {
  final Map<String, dynamic> project;
  final ValueNotifier<bool> isProcessingNotifier;

  const WorkspacePage({
    super.key,
    required this.project,
    required this.isProcessingNotifier,
  });

  @override
  State<WorkspacePage> createState() => _WorkspacePageState();
}

class _WorkspacePageState extends State<WorkspacePage>
    with AutomaticKeepAliveClientMixin, WindowListener {
  late WorkspaceActions _actions;

  @override
  bool get wantKeepAlive => true;

  @override
  void initState() {
    super.initState();
    _actions = WorkspaceActions(
      projectId: widget.project['id'],
      isProcessingNotifier: widget.isProcessingNotifier,
      onError: _showError,
    );
    windowManager.addListener(this);
    // Load prescan ngay khi mở workspace
    WidgetsBinding.instance.addPostFrameCallback((_) => _actions.loadPrescan());
  }

  @override
  void dispose() {
    windowManager.removeListener(this);
    _actions.dispose();
    super.dispose();
  }

  // ── Window close intercept ───────────────────────────────────────────────

  @override
  void onWindowClose() async {
    if (_actions.isProcessing) {
      final choice = await _showCloseWarningDialog();
      if (choice == _CloseChoice.cancel) {
        // Hủy + rollback rồi thoát
        await _actions.cancelAndRollback();
        await windowManager.destroy();
      } else if (choice == _CloseChoice.minimize) {
        await windowManager.minimize();
      }
      // null = user đóng dialog, không làm gì
    } else {
      await windowManager.destroy();
    }
  }

  Future<_CloseChoice?> _showCloseWarningDialog() {
    return showDialog<_CloseChoice>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.bgSurface,
        title: const Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: AppTheme.warning, size: 20),
            SizedBox(width: 8),
            Text('Đang có tiến trình chạy',
                style: TextStyle(color: AppTheme.textPrimary, fontSize: 16)),
          ],
        ),
        content: const Text(
          'Hệ thống đang xử lý video. Nếu thoát, dữ liệu đang quét sẽ bị hủy '
          'và index sẽ được khôi phục về trạng thái trước.\n\n'
          'Bạn muốn làm gì?',
          style: TextStyle(color: AppTheme.textSecondary, fontSize: 13, height: 1.5),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(null),
            child: const Text('Tiếp tục chờ',
                style: TextStyle(color: AppTheme.textSecondary)),
          ),
          OutlinedButton.icon(
            style: OutlinedButton.styleFrom(
                side: const BorderSide(color: AppTheme.border)),
            onPressed: () => Navigator.of(ctx).pop(_CloseChoice.minimize),
            icon: const Icon(Icons.minimize, size: 16, color: AppTheme.textPrimary),
            label: const Text('Thu nhỏ',
                style: TextStyle(color: AppTheme.textPrimary)),
          ),
          ElevatedButton.icon(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.error),
            onPressed: () => Navigator.of(ctx).pop(_CloseChoice.cancel),
            icon: const Icon(Icons.cancel_outlined, size: 16, color: Colors.white),
            label: const Text('Hủy & Thoát',
                style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }

  // ── Helpers ──────────────────────────────────────────────────────────────

  void _showError(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message), backgroundColor: AppTheme.error),
      );
    }
  }

  // ── Build ────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    super.build(context);

    return Padding(
      padding: const EdgeInsets.all(32.0),
      child: ListenableBuilder(
        listenable: _actions,
        builder: (context, child) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Config (pipeline mode + frame interval)
              WorkspaceConfigWidget(
                pipelineMode: _actions.pipelineMode,
                frameInterval: _actions.frameInterval,
                isProcessing: _actions.isProcessing,
                onModeChanged: (v) => _actions.updateConfig(mode: v),
                onIntervalChanged: (v) => _actions.updateConfig(interval: v),
              ),
              const SizedBox(height: 16),

              // Pre-scan section
              _buildPrescanSection(),
              const SizedBox(height: 16),

              // Status bar (chỉ show khi đang xử lý hoặc có status)
              if (_actions.isProcessing ||
                  _actions.status == "HOÀN TẤT" ||
                  _actions.status == "LỖI" ||
                  _actions.status == "ĐÃ DỪNG" ||
                  _actions.status == "ĐÃ HỦY") ...[
                WorkspaceControlWidget(
                  isProcessing: _actions.isProcessing,
                  status: _actions.status,
                  progress: _actions.progress,
                  onStart: () {},  // Nút Start đã chuyển vào prescan widget
                ),
                const SizedBox(height: 16),
              ],

              // Log
              Expanded(
                child: WorkspaceLogWidget(logs: _actions.logs),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildPrescanSection() {
    if (_actions.isPrescanLoading) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppTheme.bgSurface,
          border: Border.all(color: AppTheme.border),
          borderRadius: BorderRadius.circular(6),
        ),
        child: const Row(
          children: [
            SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.info),
            ),
            SizedBox(width: 12),
            Text('Đang quét danh sách video...',
                style: TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
          ],
        ),
      );
    }

    if (_actions.prescanData == null) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppTheme.bgSurface,
          border: Border.all(color: AppTheme.border),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Row(
          children: [
            const Text('Chưa có thông tin video.',
                style: TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
            const Spacer(),
            TextButton.icon(
              onPressed: _actions.loadPrescan,
              icon: const Icon(Icons.refresh, size: 16, color: AppTheme.info),
              label: const Text('Làm mới',
                  style: TextStyle(color: AppTheme.info, fontSize: 12)),
            ),
          ],
        ),
      );
    }

    return WorkspacePrescanWidget(
      prescanData: _actions.prescanData!,
      isProcessing: _actions.isProcessing,
      onStartPending: () => _actions.startProcess(rescanAll: false),
      onStartRescanAll: () => _actions.startProcess(rescanAll: true),
    );
  }
}

enum _CloseChoice { cancel, minimize }
