import 'package:flutter/material.dart';
import '../../core/backend_manager.dart';
import '../layout/app_layout.dart';
import '../theme.dart';

class SplashPage extends StatefulWidget {
  const SplashPage({super.key});

  @override
  State<SplashPage> createState() => _SplashPageState();
}

class _SplashPageState extends State<SplashPage> {
  String _statusMessage = "Đang chuẩn bị hệ thống...";

  @override
  void initState() {
    super.initState();
    _initBackend();
  }

  Future<void> _initBackend() async {
    try {
      await BackendManager().startBackend(onProgress: (msg) {
        if (mounted) setState(() => _statusMessage = msg);
      });

      if (mounted) {
        if (BackendManager().isReady) {
          Navigator.of(context).pushReplacement(
            PageRouteBuilder(
              pageBuilder: (context, animation1, animation2) => const AppLayout(),
              transitionDuration: Duration.zero,
              reverseTransitionDuration: Duration.zero,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _statusMessage = "Lỗi nghiêm trọng:\n$e";
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgBase,
      body: SafeArea(
        child: Stack(
          children: [
            Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('SPORT SEEKER',
                      style: TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 4,
                          fontFamily: 'monospace',
                          color: AppTheme.textPrimary)),
                  const SizedBox(height: 32),
                  const SizedBox(
                    width: 24,
                    height: 24,
                    child: CircularProgressIndicator(
                        color: AppTheme.textPrimary, strokeWidth: 2),
                  ),
                  const SizedBox(height: 24),
                  Text(_statusMessage,
                      style: const TextStyle(
                          color: AppTheme.textSecondary, fontSize: 14)),
                  const SizedBox(height: 8),
                  const Text(
                      'Vui lòng không đóng ứng dụng trong quá trình này.',
                      style:
                          TextStyle(color: AppTheme.textMuted, fontSize: 12)),
                ],
              ),
            ),
            const Align(
              alignment: Alignment.bottomCenter,
              child: Padding(
                padding: EdgeInsets.only(bottom: 24.0),
                child: Text.rich(
                  TextSpan(
                    children: [
                      TextSpan(
                          text: 'Powered By ',
                          style: TextStyle(
                              color: AppTheme.textSecondary, fontSize: 12)),
                      TextSpan(
                          text: 'AIBUS 🚀',
                          style: TextStyle(
                              color: AppTheme.info,
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 1.0)),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
