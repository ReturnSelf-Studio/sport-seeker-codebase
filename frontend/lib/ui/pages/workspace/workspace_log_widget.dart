import 'package:flutter/material.dart';
import '../../theme.dart';

class WorkspaceLogWidget extends StatelessWidget {
  final List<String> logs;

  const WorkspaceLogWidget({super.key, required this.logs});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
          color: Colors.black,
          border: Border.all(color: AppTheme.border),
          borderRadius: BorderRadius.circular(6)),
      child: ListView.builder(
        itemCount: logs.length,
        itemBuilder: (context, index) {
          return Text(logs[index],
              style: const TextStyle(
                  color: Colors.greenAccent,
                  fontFamily: 'monospace',
                  fontSize: 12));
        },
      ),
    );
  }
}
