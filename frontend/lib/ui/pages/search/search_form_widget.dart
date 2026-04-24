import 'package:flutter/material.dart';
import 'package:flutter/services.dart'; // Bắt buộc để dùng inputFormatters
import '../../theme.dart';

class SearchFormWidget extends StatelessWidget {
  final int searchType;
  final TextEditingController bibCtrl;
  final String? faceImagePath;
  final bool isSearching;
  final Function(int) onSearchTypeChanged;
  final VoidCallback onPickImage;
  final VoidCallback onSearch;

  const SearchFormWidget({
    super.key,
    required this.searchType,
    required this.bibCtrl,
    required this.faceImagePath,
    required this.isSearching,
    required this.onSearchTypeChanged,
    required this.onPickImage,
    required this.onSearch,
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
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _ChoiceChip(
                  label: 'Tìm BIB',
                  selected: searchType == 0,
                  onSelected: () => onSearchTypeChanged(0)),
              const SizedBox(width: 8),
              _ChoiceChip(
                  label: 'Tìm Face',
                  selected: searchType == 1,
                  onSelected: () => onSearchTypeChanged(1)),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: searchType == 0
                    ? TextFormField(
                        controller: bibCtrl,
                        // --- START FIX TICKET 29 ---
                        keyboardType: TextInputType.number, // Hiển thị bàn phím số
                        inputFormatters: [
                          FilteringTextInputFormatter.digitsOnly, // Chặn nhập chữ/kí tự lạ
                        ],
                        // --- END FIX TICKET 29 ---
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
                              onPressed: onPickImage,
                              style: ElevatedButton.styleFrom(
                                  backgroundColor: AppTheme.bgElevated, 
                                  padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 16)),
                              child: const Text('Chọn ảnh mẫu')),
                          const SizedBox(width: 8),
                          Expanded(
                              child: Text(faceImagePath ?? 'Chưa chọn ảnh',
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
                    padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 20)),
                onPressed: isSearching ? null : onSearch,
                child: Text(isSearching ? 'ĐANG TÌM...' : '🔍 TÌM KIẾM',
                    style: const TextStyle(
                        color: AppTheme.bgBase, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// Widget Private dùng chung cho màn hình Form này
class _ChoiceChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onSelected;
  const _ChoiceChip({required this.label, required this.selected, required this.onSelected});

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
