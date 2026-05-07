import 'package:flutter/material.dart';
import 'package:window_manager/window_manager.dart';

import 'core/tracking_service.dart';
import 'ui/pages/splash_page.dart';
import 'ui/theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await windowManager.ensureInitialized();
  await TrackingService.instance.init();
  runApp(const SportSeekerApp());
}

class SportSeekerApp extends StatefulWidget {
  const SportSeekerApp({super.key});

  @override
  State<SportSeekerApp> createState() => _SportSeekerAppState();
}

class _SportSeekerAppState extends State<SportSeekerApp>
    with WidgetsBindingObserver, WindowListener {
  bool _exitTracked = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    windowManager.addListener(this);
    TrackingService.instance.trackScreen('splash');
  }

  @override
  void dispose() {
    windowManager.removeListener(this);
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      TrackingService.instance.markVisible();
      return;
    }

    if (state == AppLifecycleState.hidden || state == AppLifecycleState.paused) {
      TrackingService.instance.markHidden();
      return;
    }

    if (state == AppLifecycleState.detached) {
      TrackingService.instance.markHidden();
      _trackExitOnce('lifecycle_detached');
    }
  }

  @override
  void onWindowFocus() {
    TrackingService.instance.markVisible();
  }

  @override
  void onWindowBlur() {
    TrackingService.instance.markHidden();
  }

  @override
  void onWindowMinimize() {
    TrackingService.instance.markHidden();
  }

  Future<void> _trackExitOnce(String reason) async {
    if (_exitTracked) return;
    _exitTracked = true;
    await TrackingService.instance.endSession(reason: reason);
  }

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
