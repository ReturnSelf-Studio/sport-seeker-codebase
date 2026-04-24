import 'package:flutter/material.dart';
import '../theme.dart';
import 'project_manager/project_manager_actions.dart';
import 'project_manager/project_create_form_widget.dart';
import 'project_manager/project_list_widget.dart';

class ProjectManagerPage extends StatefulWidget {
  final Function(Map<String, dynamic>) onOpenProject;
  const ProjectManagerPage({super.key, required this.onOpenProject});

  @override
  State<ProjectManagerPage> createState() => _ProjectManagerPageState();
}

class _ProjectManagerPageState extends State<ProjectManagerPage> {
  late ProjectManagerActions _actions;
  final _formKey = GlobalKey<FormState>();

  @override
  void initState() {
    super.initState();
    // Khởi tạo Actions và truyền các hàm tương tác UI (Error, Dialog) vào
    _actions = ProjectManagerActions(
      onError: _showError,
      onShowConfirm: _showConfirmDialog,
    );
  }

  void _showError(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message), backgroundColor: AppTheme.error),
      );
    }
  }

  Future<bool> _showConfirmDialog(String title, String content) async {
    return await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppTheme.bgSurface,
        title: Text(title, style: const TextStyle(color: AppTheme.textPrimary)),
        content: Text(content, style: const TextStyle(color: AppTheme.textSecondary)),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Hủy', style: TextStyle(color: AppTheme.textSecondary)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.error),
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Xác nhận', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    ) ?? false;
  }

  @override
  void dispose() {
    _actions.dispose(); // Dọn dẹp RAM
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32.0),
      // ListenableBuilder lắng nghe State từ _actions
      child: ListenableBuilder(
        listenable: _actions,
        builder: (context, child) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('QUẢN LÝ DỰ ÁN', 
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, fontFamily: 'monospace', color: AppTheme.textPrimary)),
              const Divider(color: AppTheme.border, height: 32),
              
              Form(
                key: _formKey,
                child: ProjectCreateFormWidget(
                  nameCtrl: _actions.nameCtrl,
                  sourceCtrl: _actions.sourceCtrl,
                  onSourcePicked: _actions.setSourceDir,
                  checkDuplicate: _actions.isNameDuplicate, // Truyền hàm check trùng vào Form
                  onError: _showError,
                  onCreate: () {
                    // Trigger validate và gọi API tạo mới
                    final isValid = _formKey.currentState?.validate() ?? false;
                    _actions.createProject(isValid);
                  },
                ),
              ),
              const SizedBox(height: 24),
              
              const Text('DANH SÁCH DỰ ÁN', 
                style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, fontFamily: 'monospace', letterSpacing: 1.5, color: AppTheme.textMuted)),
              const SizedBox(height: 8),
              
              Expanded(
                child: ProjectListWidget(
                  projects: _actions.projects,
                  isLoading: _actions.isLoading,
                  onOpenProject: widget.onOpenProject,
                  onDeleteProject: _actions.deleteProject,
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
