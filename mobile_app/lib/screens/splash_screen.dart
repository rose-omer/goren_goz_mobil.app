///
/// Splash Screen
/// =============
///

import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';
import '../utils/constants.dart';
import '../utils/logger.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _initialize();
  }

  Future<void> _initialize() async {
    await Future.delayed(const Duration(seconds: 2));
    
    // Request permissions
    final cameraStatus = await Permission.camera.request();
    final micStatus = await Permission.microphone.request();
    
    if (!mounted) return;
    
    if (cameraStatus.isGranted && micStatus.isGranted) {
      Navigator.of(context).pushReplacementNamed('/camera');
    } else {
      _showPermissionDialog(cameraStatus, micStatus);
    }
  }

  void _showPermissionDialog(PermissionStatus cameraStatus, PermissionStatus micStatus) {
    String missingPermissions = '';
    
    if (!cameraStatus.isGranted) {
      missingPermissions += '• Kamera\n';
    }
    if (!micStatus.isGranted) {
      missingPermissions += '• Mikrofon\n';
    }
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('İzinler Gerekli'),
        content: Text(
          'Uygulamanın çalışması için aşağıdaki izinler gereklidir:\n\n$missingPermissions\nLütfen ayarlardan izin verin.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('İptal'),
          ),
          TextButton(
            onPressed: () {
              openAppSettings();
              Navigator.of(context).pop();
            },
            child: const Text('Ayarlar'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              AppColors.primary.withOpacity(0.8),
              AppColors.background,
            ],
          ),
        ),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.remove_red_eye,
                size: 100,
                color: AppColors.text,
              ),
              const SizedBox(height: 24),
              Text(
                AppStrings.appName,
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      color: AppColors.text,
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const SizedBox(height: 16),
              Text(
                AppStrings.appDescription,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: AppColors.textSecondary,
                    ),
              ),
              const SizedBox(height: 48),
              const CircularProgressIndicator(
                valueColor: AlwaysStoppedAnimation<Color>(AppColors.secondary),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
