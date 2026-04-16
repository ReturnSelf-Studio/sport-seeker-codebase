import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter/material.dart';

import '../../core/backend_manager.dart';
import '../theme.dart';
import '../pages/project_manager_page.dart';
import '../pages/project_detail_page.dart';
import '../pages/placeholder_page.dart';
import '../pages/settings_page.dart';

class AppLayout extends StatefulWidget {
  const AppLayout({super.key});

  @override
  State<AppLayout> createState() => _AppLayoutState();
}

class _AppLayoutState extends State<AppLayout> {
  int _selectedIndex = 1;
  Map<String, dynamic>? _currentProject;

  String _modelStatus = 'loading';
  String _modelMessage = 'Đang kết nối AI Engine...';
  Timer? _statusTimer;

  final List<String> _menus = [
    'Dashboard',
    'Quản lý Dự án',
    'Cài đặt Hệ thống',
  ];

  final List<IconData> _menuIcons = [
    Icons.dashboard,
    Icons.folder,
    Icons.settings,
  ];

  @override
  void initState() {
    super.initState();
    _checkModelStatus();
    _statusTimer =
        Timer.periodic(const Duration(seconds: 2), (_) => _checkModelStatus());
  }

  @override
  void dispose() {
    _statusTimer?.cancel();
    super.dispose();
  }

  Future<void> _checkModelStatus() async {
    try {
      final res = await http
          .get(Uri.parse('http://127.0.0.1:10330/models/status'))
          .timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        final status = data['status'];
        final msg = data['message'] ?? '';

        if (mounted && (status != _modelStatus || msg != _modelMessage)) {
          setState(() {
            _modelStatus = status;
            _modelMessage = msg;
          });
        }
        if (status == 'ready' || status == 'error') {
          _statusTimer?.cancel();
        }
      }
    } catch (_) {}
  }

  void _openProject(Map<String, dynamic> project) {
    setState(() {
      _currentProject = project;
      _selectedIndex = 3; // Index ẩn dành riêng cho Chi tiết dự án
    });
  }

  void _closeProject() {
    setState(() {
      _currentProject = null;
      _selectedIndex = 1; // Quay về Quản lý dự án
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          _buildSidebar(),
          Expanded(
            child: _buildBodyWrapper(),
          ),
        ],
      ),
    );
  }

  Widget _buildBodyWrapper() {
    return Column(
      children: [
        if (_modelStatus == 'loading')
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 24),
            color: AppTheme.info.withOpacity(0.15),
            child: Row(
              children: [
                const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(
                      strokeWidth: 2, color: AppTheme.info),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      ValueListenableBuilder<double?>(
                        valueListenable: BackendManager().modelDownloadProgress,
                        builder: (context, progress, child) {
                          if (progress != null) {
                            return Text(
                              'Hệ thống đang tải dữ liệu AI Models (${(progress * 100).toInt()}%). Vui lòng đợi...',
                              style: const TextStyle(color: AppTheme.info, fontSize: 13, fontWeight: FontWeight.bold),
                            );
                          }
                          return Text(
                            '$_modelMessage (Chạy 1 lần duy nhất lúc khởi động)',
                            style: const TextStyle(color: AppTheme.info, fontSize: 13, fontWeight: FontWeight.bold),
                          );
                        },
                      ),
                      const SizedBox(height: 4),
                      ValueListenableBuilder<String>(
                        valueListenable: BackendManager().latestLog,
                        builder: (context, log, child) {
                          return Text(
                            '>_ $log',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(color: AppTheme.textSecondary, fontSize: 11, fontFamily: 'monospace'),
                          );
                        },
                      ),
                    ],
                  ),
                ),
                TextButton.icon(
                  onPressed: () {
                    setState(() => _selectedIndex = 2); // Tab Settings
                  },
                  icon: const Icon(Icons.settings,
                      color: AppTheme.info, size: 16),
                  label: const Text('Cấu hình',
                      style: TextStyle(color: AppTheme.info)),
                )
              ],
            ),
          ),
        if (_modelStatus == 'error')
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 24),
            color: AppTheme.error.withOpacity(0.15),
            child: Row(
              children: [
                const Icon(Icons.error_outline,
                    color: AppTheme.error, size: 18),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    '$_modelMessage. Vui lòng vào Cài đặt hệ thống để khởi động lại Engine.',
                    style: const TextStyle(color: AppTheme.error, fontSize: 13),
                  ),
                ),
              ],
            ),
          ),
        Expanded(
          child: Container(
            color: AppTheme.bgBase,
            child: _buildBody(),
          ),
        ),
      ],
    );
  }

  Widget _buildBody() {
    return IndexedStack(
      index: _selectedIndex,
      children: [
        const PlaceholderPage(title: 'DASHBOARD', icon: '📊'), // index 0
        ProjectManagerPage(onOpenProject: _openProject), // index 1
        const SettingsPage(), // index 2
        if (_currentProject != null) // index 3 (Hidden)
          ProjectDetailPage(
            key: ValueKey(_currentProject!['id']),
            project: _currentProject!,
            onBack: _closeProject,
          )
        else
          const SizedBox.shrink(),
      ],
    );
  }

  Widget _buildSidebar() {
    return Container(
      width: 220,
      color: AppTheme.bgSidebar,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 24, 16, 16),
            child: Row(
              children: [
                Image.asset('assets/icons/app_icon.png', width: 28, height: 28),
                const SizedBox(width: 12),
                const Expanded(
                  child: Text(
                    'Sport Seeker',
                    style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 0.5,
                        fontFamily: 'monospace',
                        color: AppTheme.textPrimary),
                  ),
                ),
              ],
            ),
          ),
          const Divider(color: AppTheme.border, height: 1),
          const SizedBox(height: 16),
          ...List.generate(_menus.length, (index) {
            return _buildNavItem(
                _menus[index], _menuIcons[index], index == _selectedIndex, () {
              setState(() {
                _selectedIndex = index;
                if (index != 3) {
                  _currentProject = null;
                }
              });
            });
          }),
          const Spacer(),
          const Padding(
            padding: EdgeInsets.all(16.0),
            child: Text.rich(
              TextSpan(
                children: [
                  TextSpan(
                      text: 'v1.0.0-beta\n',
                      style:
                          TextStyle(color: AppTheme.textMuted, fontSize: 11)),
                  TextSpan(
                      text: 'Powered by ',
                      style: TextStyle(
                          color: AppTheme.textSecondary, fontSize: 11)),
                  TextSpan(
                      text: 'AIBus',
                      style: TextStyle(
                          color: AppTheme.info,
                          fontSize: 11,
                          fontWeight: FontWeight.bold)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNavItem(
      String title, IconData icon, bool isActive, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      hoverColor: AppTheme.bgHover,
      child: Container(
        decoration: BoxDecoration(
          color: isActive ? AppTheme.bgActive : Colors.transparent,
          border: Border(
              left: BorderSide(
                  color: isActive ? AppTheme.textPrimary : Colors.transparent,
                  width: 3)),
        ),
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
        child: Row(
          children: [
            Icon(icon,
                size: 18,
                color:
                    isActive ? AppTheme.textPrimary : AppTheme.textSecondary),
            const SizedBox(width: 12),
            Text(title,
                style: TextStyle(
                    color: isActive
                        ? AppTheme.textPrimary
                        : AppTheme.textSecondary,
                    fontSize: 13,
                    fontWeight:
                        isActive ? FontWeight.w600 : FontWeight.normal)),
          ],
        ),
      ),
    );
  }
}
