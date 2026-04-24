import 'package:flutter/material.dart';
import '../../theme.dart';

class ProjectListWidget extends StatelessWidget {
  final List<dynamic> projects;
  final bool isLoading;
  final Function(Map<String, dynamic>) onOpenProject;
  final Function(String, String) onDeleteProject;

  const ProjectListWidget({
    super.key,
    required this.projects,
    required this.isLoading,
    required this.onOpenProject,
    required this.onDeleteProject,
  });

  @override
  Widget build(BuildContext context) {
    if (isLoading) return const Center(child: CircularProgressIndicator());
    if (projects.isEmpty) return const Center(child: Text('Chưa có dự án nào.', style: TextStyle(color: AppTheme.textSecondary)));

    return ListView.builder(
      itemCount: projects.length,
      itemBuilder: (context, index) {
        final p = projects[index];
        final hasIndex = p['has_index'] ?? false;
        
        return Card(
          color: AppTheme.bgSurface,
          margin: const EdgeInsets.only(bottom: 8),
          shape: RoundedRectangleBorder(side: const BorderSide(color: AppTheme.border), borderRadius: BorderRadius.circular(4)),
          child: ListTile(
            title: Text(p['name'], style: const TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.bold)),
            subtitle: Text(p['source_dir'], style: const TextStyle(color: AppTheme.textMuted, fontSize: 11)),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(color: hasIndex ? AppTheme.bgActive : AppTheme.bgBase, borderRadius: BorderRadius.circular(2)),
                  child: Text(hasIndex ? 'Đã Index' : 'Chưa Index', style: TextStyle(color: hasIndex ? AppTheme.textPrimary : AppTheme.textSecondary, fontSize: 11)),
                ),
                const SizedBox(width: 16),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: AppTheme.bgActive),
                  onPressed: () => onOpenProject(p),
                  child: const Text('Mở', style: TextStyle(color: AppTheme.textPrimary)),
                ),
                const SizedBox(width: 8),
                IconButton(
                  icon: const Icon(Icons.delete, color: AppTheme.error, size: 20),
                  onPressed: () => onDeleteProject(p['id'], p['name']),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
