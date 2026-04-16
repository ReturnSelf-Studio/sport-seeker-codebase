import 'package:flutter/material.dart';
import '../theme.dart';
import 'workspace_page.dart';
import 'search_page.dart';

class ProjectDetailPage extends StatelessWidget {
  final Map<String, dynamic> project;
  final VoidCallback onBack;

  const ProjectDetailPage({super.key, required this.project, required this.onBack});

  @override
  Widget build(BuildContext context) {
    bool hasIndex = project['has_index'] ?? false;

    return DefaultTabController(
      length: 2,
      initialIndex: hasIndex ? 1 : 0,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 24, 32, 0),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                IconButton(
                  icon: const Icon(Icons.arrow_back, color: AppTheme.textPrimary),
                  tooltip: 'Quay lại',
                  onPressed: onBack,
                ),
                const SizedBox(width: 8),
                Text(
                  'DỰ ÁN: ${project['name'].toString().toUpperCase()}',
                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, fontFamily: 'monospace', color: AppTheme.textPrimary),
                ),
                const Spacer(),
                Container(
                  height: 40,
                  decoration: BoxDecoration(
                    color: AppTheme.bgElevated,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: AppTheme.border),
                  ),
                  child: TabBar(
                    isScrollable: true,
                    dividerColor: Colors.transparent,
                    indicatorSize: TabBarIndicatorSize.tab,
                    indicator: BoxDecoration(
                      color: AppTheme.bgActive,
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: AppTheme.textPrimary.withOpacity(0.3)),
                    ),
                    labelColor: AppTheme.textPrimary,
                    unselectedLabelColor: AppTheme.textSecondary,
                    tabs: const [
                      Tab(child: Padding(padding: EdgeInsets.symmetric(horizontal: 16), child: Text('1. CẤU HÌNH & XỬ LÝ'))),
                      Tab(child: Padding(padding: EdgeInsets.symmetric(horizontal: 16), child: Text('2. TÌM KIẾM & TRÍCH XUẤT'))),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 32),
            child: Divider(color: AppTheme.border, height: 32),
          ),
          Expanded(
            child: TabBarView(
              physics: const NeverScrollableScrollPhysics(),
              children: [
                WorkspacePage(project: project),
                SearchPage(project: project),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
