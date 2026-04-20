import 'package:flutter/material.dart';
import 'ui/theme.dart';
import 'ui/pages/splash_page.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const SportSeekerApp());
}

class SportSeekerApp extends StatelessWidget {
  const SportSeekerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Sport Seeker',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const SplashPage(),
    );
  }
}
