import 'package:flutter/material.dart';
import '../../theme.dart';

class WorkspaceControlWidget extends StatelessWidget {
  final bool isProcessing;
  final String status;
  final double progress;
  final VoidCallback onStart;

  const WorkspaceControlWidget({
    super.key,
    required this.isProcessing,
    required this.status,
    required this.progress,
    required this.onStart,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
          color: AppTheme.bgSurface,
          border: Border.all(color: AppTheme.border),
          borderRadius: BorderRadius.circular(6)),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  if (isProcessing) ...[
                    const SizedBox(
                      width: 14,
                      height: 14,
                      child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.warning),
                    ),
                    const SizedBox(width: 8),
                  ],
                  Text(
                    'Trạng thái: $status${isProcessing && progress > 0 ? ' (${(progress * 100).toStringAsFixed(1)}%)' : ''}',
                    style: TextStyle(
                        color: status == "HOÀN TẤT" ? AppTheme.success : AppTheme.warning,
                        fontWeight: FontWeight.bold),
                  ),
                ],
              ),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: isProcessing ? AppTheme.border : AppTheme.textPrimary,
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                ),
                onPressed: isProcessing ? null : onStart,
                child: Text(isProcessing ? '⏳ ĐANG XỬ LÝ...' : '▶ BẮT ĐẦU XỬ LÝ',
                    style: TextStyle(
                        color: isProcessing ? AppTheme.textSecondary : AppTheme.bgBase,
                        fontWeight: FontWeight.bold)),
              ),
            ],
          ),
          const SizedBox(height: 16),
          LinearProgressIndicator(
              value: (isProcessing && progress == 0.0) ? null : progress,
              backgroundColor: AppTheme.bgElevated,
              color: AppTheme.success,
              minHeight: 6),
        ],
      ),
    );
  }
}
