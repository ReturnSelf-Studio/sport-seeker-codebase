import 'package:flutter/material.dart';
import '../theme.dart';
import 'workspace/workspace_actions.dart';
import 'workspace/workspace_config_widget.dart';
import 'workspace/workspace_control_widget.dart';
import 'workspace/workspace_log_widget.dart';

class WorkspacePage extends StatefulWidget {
  final Map<String, dynamic> project;
  final ValueNotifier<bool> isProcessingNotifier;

  const WorkspacePage({super.key, required this.project, required this.isProcessingNotifier});

  @override
  State<WorkspacePage> createState() => _WorkspacePageState();
}

class _WorkspacePageState extends State<WorkspacePage> with AutomaticKeepAliveClientMixin {
  late WorkspaceActions _actions;

  @override
  bool get wantKeepAlive => true; 

  @override
  void initState() {
    super.initState();
    _actions = WorkspaceActions(
      projectId: widget.project['id'],
      isProcessingNotifier: widget.isProcessingNotifier, // Gắn Notifier vào Controller
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

    return Padding(
      padding: const EdgeInsets.all(32.0),
      child: ListenableBuilder(
        listenable: _actions,
        builder: (context, child) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              WorkspaceConfigWidget(
                pipelineMode: _actions.pipelineMode,
                frameInterval: _actions.frameInterval,
                isProcessing: _actions.isProcessing,
                onModeChanged: (v) => _actions.updateConfig(mode: v),
                onIntervalChanged: (v) => _actions.updateConfig(interval: v),
              ),
              const SizedBox(height: 16),
              WorkspaceControlWidget(
                isProcessing: _actions.isProcessing,
                status: _actions.status,
                progress: _actions.progress,
                onStart: _actions.startProcess,
              ),
              const SizedBox(height: 16),
              Expanded(
                child: WorkspaceLogWidget(logs: _actions.logs),
              ),
            ],
          );
        },
      ),
    );
  }
}
