import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../../theme.dart';

class ProjectCreateFormWidget extends StatelessWidget {
  final TextEditingController nameCtrl;
  final TextEditingController sourceCtrl;
  final Function(String) onSourcePicked;
  final VoidCallback onCreate;
  final bool Function(String) checkDuplicate;
  final Function(String) onError;

  const ProjectCreateFormWidget({
    super.key,
    required this.nameCtrl,
    required this.sourceCtrl,
    required this.onSourcePicked,
    required this.onCreate,
    required this.checkDuplicate,
    required this.onError,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: AppTheme.bgSurface, border: Border.all(color: AppTheme.border), borderRadius: BorderRadius.circular(6)),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Tên Dự án *', style: TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                const SizedBox(height: 4),
                TextFormField(
                  controller: nameCtrl,
                  style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
                  decoration: const InputDecoration(
                      filled: true, 
                      fillColor: AppTheme.bgElevated, 
                      border: OutlineInputBorder(), 
                      isDense: true, 
                      hintText: '2-50 ký tự, không khoảng trắng', 
                      hintStyle: TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Tên dự án không được để trống';
                    }
                    final trimmed = value.trim();
                    if (trimmed.length < 2 || trimmed.length > 50) {
                      return 'Tên dự án phải từ 2 đến 50 ký tự';
                    }
                    if (trimmed.contains(' ')) {
                      return 'Không chứa khoảng trắng (Dùng _ hoặc -)';
                    }
                    // --- BẮT ĐẦU FIX TICKET 27 ---
                    if (checkDuplicate(trimmed)) {
                      return 'Tên dự án đã tồn tại. Vui lòng chọn tên khác!';
                    }
                    // --- KẾT THÚC FIX TICKET 27 ---
                    return null;
                  },
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
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: sourceCtrl,
                        readOnly: true,
                        style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
                        decoration: const InputDecoration(filled: true, fillColor: AppTheme.bgElevated, border: OutlineInputBorder(), isDense: true),
                      ),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: AppTheme.bgActive, padding: const EdgeInsets.symmetric(vertical: 16)),
                      onPressed: () async {
                        try {
                          String? path = await FilePicker.platform.getDirectoryPath(
                            dialogTitle: 'Chọn thư mục Nguồn dự án',
                          );
                          if (path != null) {
                            onSourcePicked(path);
                          }
                        } catch (e) {
                          onError('Lỗi mở thư mục: $e');
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
          Padding(
            padding: const EdgeInsets.only(top: 19),
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: AppTheme.textPrimary, padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16)),
              onPressed: onCreate,
              child: const Text('+ Tạo Mới', style: TextStyle(color: AppTheme.bgBase, fontWeight: FontWeight.bold)),
            ),
          ),
        ],
      ),
    );
  }
}
