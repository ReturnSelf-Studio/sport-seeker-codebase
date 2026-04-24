import 'package:flutter/material.dart';
import '../../theme.dart';

class WorkspaceConfigWidget extends StatelessWidget {
  final String pipelineMode;
  final int frameInterval;
  final bool isProcessing;
  final Function(String) onModeChanged;
  final Function(int) onIntervalChanged;

  const WorkspaceConfigWidget({
    super.key,
    required this.pipelineMode,
    required this.frameInterval,
    required this.isProcessing,
    required this.onModeChanged,
    required this.onIntervalChanged,
  });

  @override
  Widget build(BuildContext context) {
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
                    style: TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  value: pipelineMode,
                  dropdownColor: AppTheme.bgElevated,
                  style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
                  decoration: const InputDecoration(
                      filled: true,
                      fillColor: AppTheme.bgElevated,
                      border: OutlineInputBorder(),
                      isDense: true),
                  items: const [
                    DropdownMenuItem(value: 'face_bib', child: Text('Kết hợp (Face & BIB)')),
                    DropdownMenuItem(value: 'face_only', child: Text('Chỉ khuôn mặt (Face)')),
                    DropdownMenuItem(value: 'bib_only', child: Text('Chỉ số BIB')),
                  ],
                  onChanged: isProcessing ? null : (v) => onModeChanged(v!),
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
                    style: TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                const SizedBox(height: 8),
                DropdownButtonFormField<int>(
                  value: frameInterval,
                  dropdownColor: AppTheme.bgElevated,
                  style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
                  decoration: const InputDecoration(
                      filled: true,
                      fillColor: AppTheme.bgElevated,
                      border: OutlineInputBorder(),
                      isDense: true),
                  items: const [
                    DropdownMenuItem(value: 60, child: Text('Quét rất nhanh (Thưa khung hình)')),
                    DropdownMenuItem(value: 30, child: Text('Quét trung bình (Cân bằng)')),
                    DropdownMenuItem(value: 10, child: Text('Quét kỹ - Chậm (Dày khung hình)')),
                  ],
                  onChanged: isProcessing ? null : (v) => onIntervalChanged(v!),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
