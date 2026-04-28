import 'package:flutter/material.dart';
import '../../theme.dart';

/// Widget hiển thị kết quả pre-scan.
/// Mặc định show summary. Có nút "Xem chi tiết" để expand table.
class WorkspacePrescanWidget extends StatefulWidget {
  final Map<String, dynamic> prescanData;
  final bool isProcessing;
  final VoidCallback onStartPending;
  final VoidCallback onStartRescanAll;

  const WorkspacePrescanWidget({
    super.key,
    required this.prescanData,
    required this.isProcessing,
    required this.onStartPending,
    required this.onStartRescanAll,
  });

  @override
  State<WorkspacePrescanWidget> createState() => _WorkspacePrescanWidgetState();
}

class _WorkspacePrescanWidgetState extends State<WorkspacePrescanWidget> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final summary = widget.prescanData['summary'] as Map<String, dynamic>;
    final videos = widget.prescanData['videos'] as List<dynamic>;
    final overLimit = widget.prescanData['over_limit'] as bool;
    final maxVideos = widget.prescanData['max_videos'] as int;

    final total = summary['total'] as int;
    final done = summary['done'] as int;
    final pending = summary['pending'] as int;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.bgSurface,
        border: Border.all(color: overLimit ? AppTheme.error : AppTheme.border),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Header ──
          Row(
            children: [
              Icon(
                overLimit ? Icons.warning_amber_rounded : Icons.video_library_outlined,
                color: overLimit ? AppTheme.error : AppTheme.info,
                size: 18,
              ),
              const SizedBox(width: 8),
              Text(
                'Tổng quan dự án',
                style: const TextStyle(
                  color: AppTheme.textPrimary,
                  fontWeight: FontWeight.bold,
                  fontSize: 13,
                ),
              ),
              const Spacer(),
              TextButton.icon(
                onPressed: () => setState(() => _expanded = !_expanded),
                icon: Icon(
                  _expanded ? Icons.expand_less : Icons.expand_more,
                  size: 16,
                  color: AppTheme.textSecondary,
                ),
                label: Text(
                  _expanded ? 'Thu gọn' : 'Xem chi tiết',
                  style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // ── Summary chips ──
          Wrap(
            spacing: 12,
            runSpacing: 8,
            children: [
              _StatChip(
                label: 'Tổng video',
                value: total.toString(),
                color: AppTheme.info,
              ),
              _StatChip(
                label: 'Đã quét',
                value: done.toString(),
                color: AppTheme.success,
              ),
              _StatChip(
                label: 'Chưa quét',
                value: pending.toString(),
                color: pending > 0 ? AppTheme.warning : AppTheme.textSecondary,
              ),
            ],
          ),

          if (overLimit) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: AppTheme.error.withOpacity(0.1),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                '⚠ Vượt giới hạn $maxVideos video. Vui lòng chia nhỏ dự án.',
                style: const TextStyle(color: AppTheme.error, fontSize: 12),
              ),
            ),
          ],

          // ── Action buttons ──
          if (!overLimit) ...[
            const SizedBox(height: 16),
            Row(
              children: [
                if (pending > 0)
                  Expanded(
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.textPrimary,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      onPressed: widget.isProcessing ? null : widget.onStartPending,
                      child: Text(
                        '▶ Quét $pending video chưa quét',
                        style: const TextStyle(
                          color: AppTheme.bgBase,
                          fontWeight: FontWeight.bold,
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ),
                if (pending > 0 && done > 0) const SizedBox(width: 8),
                if (done > 0)
                  Expanded(
                    child: OutlinedButton(
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: AppTheme.border),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      onPressed: widget.isProcessing ? null : widget.onStartRescanAll,
                      child: const Text(
                        '🔄 Quét lại tất cả',
                        style: TextStyle(
                          color: AppTheme.textSecondary,
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ),
                if (pending == 0 && done == 0)
                  const Text(
                    'Không tìm thấy video nào trong thư mục.',
                    style: TextStyle(color: AppTheme.textSecondary, fontSize: 12),
                  ),
              ],
            ),
          ],

          // ── Expandable detail table ──
          if (_expanded && videos.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Divider(color: AppTheme.border),
            const SizedBox(height: 8),
            _buildTable(videos),
          ],
        ],
      ),
    );
  }

  Widget _buildTable(List<dynamic> videos) {
    return ConstrainedBox(
      constraints: const BoxConstraints(maxHeight: 280),
      child: SingleChildScrollView(
        child: Table(
          columnWidths: const {
            0: FlexColumnWidth(3),
            1: FlexColumnWidth(1.5),
            2: FixedColumnWidth(90),
          },
          border: TableBorder.all(color: AppTheme.border, width: 0.5),
          children: [
            // Header
            TableRow(
              decoration: const BoxDecoration(color: AppTheme.bgElevated),
              children: ['Tên file', 'Thời lượng', 'Trạng thái']
                  .map((h) => Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                        child: Text(h,
                            style: const TextStyle(
                                color: AppTheme.textSecondary,
                                fontSize: 11,
                                fontWeight: FontWeight.bold)),
                      ))
                  .toList(),
            ),
            // Rows
            ...videos.map((v) {
              final vMap = v as Map<String, dynamic>;
              final scanStatus = vMap['scan_status'] as String;
              final duration = vMap['duration_seconds'];
              final durationStr = duration != null
                  ? _formatDuration((duration as num).toInt())
                  : '—';

              return TableRow(
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                    child: Text(
                      vMap['name'] as String,
                      style: const TextStyle(
                          color: AppTheme.textPrimary,
                          fontSize: 11,
                          fontFamily: 'monospace'),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                    child: Text(durationStr,
                        style: const TextStyle(
                            color: AppTheme.textSecondary, fontSize: 11)),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                    child: _StatusBadge(status: scanStatus),
                  ),
                ],
              );
            }),
          ],
        ),
      ),
    );
  }

  String _formatDuration(int seconds) {
    final h = seconds ~/ 3600;
    final m = (seconds % 3600) ~/ 60;
    final s = seconds % 60;
    if (h > 0) return '${h}h ${m}m';
    if (m > 0) return '${m}m ${s}s';
    return '${s}s';
  }
}

class _StatChip extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _StatChip({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(value,
              style: TextStyle(
                  color: color, fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(width: 6),
          Text(label,
              style: const TextStyle(color: AppTheme.textSecondary, fontSize: 11)),
        ],
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final String status;
  const _StatusBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    Color color;
    String label;
    switch (status) {
      case 'done':
        color = AppTheme.success;
        label = '✓ Đã quét';
        break;
      case 'scanning':
        color = AppTheme.warning;
        label = '⏳ Đang quét';
        break;
      default:
        color = AppTheme.textMuted;
        label = '— Chưa quét';
    }
    return Text(label,
        style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w500));
  }
}
