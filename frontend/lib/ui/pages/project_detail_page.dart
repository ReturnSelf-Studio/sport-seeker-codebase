import 'package:flutter/material.dart';
import '../../core/tracking_service.dart';
import '../theme.dart';
import 'workspace_page.dart';
import 'search_page.dart';

class ProjectDetailPage extends StatefulWidget {
  final Map<String, dynamic> project;
  final VoidCallback onBack;

  const ProjectDetailPage({super.key, required this.project, required this.onBack});

  @override
  State<ProjectDetailPage> createState() => _ProjectDetailPageState();
}

class _ProjectDetailPageState extends State<ProjectDetailPage>
    with SingleTickerProviderStateMixin {
  late Map<String, dynamic> project;
  late TabController _tabController;

  // Biến State quản lý trạng thái xử lý chung cho toàn bộ dự án
  final ValueNotifier<bool> _isProcessingNotifier = ValueNotifier<bool>(false);

  @override
  void initState() {
    super.initState();
    project = Map.from(widget.project);
    final hasIndex = project['has_index'] ?? false;
    _tabController = TabController(
      length: 2,
      initialIndex: hasIndex ? 1 : 0,
      vsync: this,
    )..addListener(_onTabChanged);
    _trackCurrentTab();
  }

  @override
  void dispose() {
    _tabController.removeListener(_onTabChanged);
    _tabController.dispose();
    _isProcessingNotifier.dispose(); // Giải phóng RAM khi đóng dự án
    super.dispose();
  }

  void _onTabChanged() {
    if (_tabController.indexIsChanging) return;
    _trackCurrentTab();
  }

  void _trackCurrentTab() {
    final tabIndex = _tabController.index;
    TrackingService.instance.trackScreen(
      tabIndex == 0 ? 'workspace' : 'search',
      properties: {
        'project_id': project['id'],
        'project_name': project['name'],
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 24, 32, 0),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                IconButton(
                  icon: const Icon(Icons.arrow_back, color: AppTheme.textPrimary),
                  tooltip: 'Quay lại',
                  onPressed: widget.onBack,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'GIẢI CHẠY: ${project['name'].toString().toUpperCase()}',
                        style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, fontFamily: 'monospace', color: AppTheme.textPrimary),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          const Icon(Icons.folder_open, size: 16, color: AppTheme.textSecondary),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              project['source_dir'] ?? 'Chưa cấu hình thư mục đầu vào',
                              style: const TextStyle(fontSize: 13, color: AppTheme.textSecondary, fontFamily: 'monospace'),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 16),
                Container(
                  height: 40,
                  decoration: BoxDecoration(
                    color: AppTheme.bgElevated,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: AppTheme.border),
                  ),
                  child: TabBar(
                    controller: _tabController,
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
              controller: _tabController,
              physics: const NeverScrollableScrollPhysics(),
              children: [
                // Truyền cờ isProcessingNotifier xuống cho 2 tab
                WorkspacePage(project: project, isProcessingNotifier: _isProcessingNotifier),
                SearchPage(project: project, isProcessingNotifier: _isProcessingNotifier),
              ],
            ),
          ),
        ],
    );
  }
}
