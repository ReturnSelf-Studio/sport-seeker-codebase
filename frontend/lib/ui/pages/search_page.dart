import 'package:flutter/material.dart';
import '../theme.dart';
import 'search/search_actions.dart';
import 'search/search_form_widget.dart';
import 'search/search_results_widget.dart';

class SearchPage extends StatefulWidget {
  final Map<String, dynamic> project;
  final ValueNotifier<bool> isProcessingNotifier;

  const SearchPage({super.key, required this.project, required this.isProcessingNotifier});

  @override
  State<SearchPage> createState() => _SearchPageState();
}

class _SearchPageState extends State<SearchPage> with AutomaticKeepAliveClientMixin {
  late SearchActions _actions;
  final _formKey = GlobalKey<FormState>();

  @override
  bool get wantKeepAlive => true; 

  @override
  void initState() {
    super.initState();
    _actions = SearchActions(
      projectId: widget.project['id'],
      onError: _showError,
    );
  }

  void _showError(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message), backgroundColor: AppTheme.error),
      );
    }
  }

  @override
  void dispose() {
    _actions.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    super.build(context); 
    
    // Vẫn giữ logic KHÓA TAB của Ticket 30
    return ValueListenableBuilder<bool>(
      valueListenable: widget.isProcessingNotifier,
      builder: (context, isProcessing, child) {
        if (isProcessing) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const CircularProgressIndicator(strokeWidth: 3, color: AppTheme.warning),
                const SizedBox(height: 24),
                const Text('HỆ THỐNG ĐANG XỬ LÝ DỮ LIỆU...', 
                    style: TextStyle(fontSize: 18, color: AppTheme.warning, fontWeight: FontWeight.bold, fontFamily: 'monospace')),
                const SizedBox(height: 8),
                const Text('Không thể truy vấn thông tin trong lúc này.', 
                    style: TextStyle(color: AppTheme.textPrimary, fontSize: 14)),
                const SizedBox(height: 4),
                Text('Vui lòng đợi quá trình xử lý ở tab "1. CẤU HÌNH & XỬ LÝ" hoàn tất.', 
                    style: TextStyle(color: AppTheme.textSecondary.withOpacity(0.8), fontSize: 13)),
              ],
            ),
          );
        }

        return Padding(
          padding: const EdgeInsets.all(32.0),
          child: ListenableBuilder(
            listenable: _actions,
            builder: (context, child) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('TÌM KIẾM TRONG: ${widget.project['name']}',
                      style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          fontFamily: 'monospace',
                          color: AppTheme.textPrimary)),
                  const Divider(color: AppTheme.border, height: 32),
                  // Bọc FormKey bên ngoài Widget
                  Form(
                    key: _formKey,
                    child: SearchFormWidget(
                      searchType: _actions.searchType,
                      bibCtrl: _actions.bibCtrl,
                      faceImagePath: _actions.faceImagePath,
                      isSearching: _actions.isSearching,
                      onSearchTypeChanged: _actions.setSearchType,
                      onPickImage: _actions.pickImage,
                      onSearch: () {
                        // Kích hoạt hàm Validate Form khi ấn nút tìm kiếm
                        final isValid = _formKey.currentState?.validate() ?? false;
                        _actions.doSearch(isValid);
                      },
                    ),
                  ),
                  const SizedBox(height: 16),
                  Expanded(
                    child: SearchResultsWidget(
                      isSearching: _actions.isSearching,
                      results: _actions.results,
                      onOpenFile: _actions.openFile,
                    )
                  ),
                ],
              );
            },
          ),
        );
      },
    );
  }
}
