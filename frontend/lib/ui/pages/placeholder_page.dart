import 'package:flutter/material.dart';
import '../theme.dart';

class PlaceholderPage extends StatelessWidget {
  final String title;
  final String icon;

  const PlaceholderPage({super.key, required this.title, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(icon, style: const TextStyle(fontSize: 64)),
          const SizedBox(height: 16),
          Text(
            title,
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: AppTheme.textPrimary, fontFamily: 'monospace'),
          ),
          const SizedBox(height: 8),
          const Text('Coming Soon...', style: TextStyle(fontSize: 14, color: AppTheme.textSecondary)),
        ],
      ),
    );
  }
}
