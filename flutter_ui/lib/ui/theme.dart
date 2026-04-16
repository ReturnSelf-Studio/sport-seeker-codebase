import 'package:flutter/material.dart';

class AppTheme {
  static const Color bgBase = Color(0xFF0F0F0F);
  static const Color bgSidebar = Color(0xFF161616);
  static const Color bgSurface = Color(0xFF1C1C1C);
  static const Color bgElevated = Color(0xFF242424);
  static const Color bgHover = Color(0xFF2A2A2A);
  static const Color bgActive = Color(0xFF303030);

  static const Color border = Color(0xFF2E2E2E);
  static const Color borderMid = Color(0xFF3A3A3A);
  static const Color borderFocus = Color(0xFF6A6A6A);

  static const Color textPrimary = Color(0xFFE8E8E8);
  static const Color textSecondary = Color(0xFF888888);
  static const Color textMuted = Color(0xFF555555);

  static const Color success = Color(0xFF4CAF7D);
  static const Color warning = Color(0xFFE6A817);
  static const Color error = Color(0xFFE05252);
  static const Color info = Color(0xFF5B9BD5);

  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: bgBase,
      fontFamily: 'SF Pro Display', // Sẽ map sang Roboto/system default nếu không có
      colorScheme: const ColorScheme.dark(
        primary: textPrimary,
        surface: bgSurface,
        background: bgBase,
        error: error,
      ),
      textTheme: const TextTheme(
        bodyMedium: TextStyle(color: textPrimary, fontSize: 13),
        bodySmall: TextStyle(color: textSecondary, fontSize: 12),
      ),
    );
  }
}
