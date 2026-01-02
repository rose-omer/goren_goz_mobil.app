///
/// Constants and Configuration
/// ============================
///

import 'package:flutter/material.dart';

class AppConfig {
  // API Configuration
  static const String defaultApiUrl = 'http://192.168.25.155:8000';  // Laptop WiFi IP (telefon hotspot kullanıyor)
  static const String productionApiUrl = 'https://your-production-url.com';
  
  // Current environment
  static bool isDevelopment = true;
  
  static String get apiUrl => isDevelopment ? defaultApiUrl : productionApiUrl;
  
  // API Endpoints
  static const String analyzeEndpoint = '/api/analyze';
  static const String healthEndpoint = '/health';
  
  // Request configuration - OPTIMIZED
  static const Duration requestTimeout = Duration(seconds: 60);  // VLM için uzun timeout
  static const int maxRetries = 2;
  
  // Camera configuration - OPTIMIZED for real-time detection
  static const Duration frameInterval = Duration(milliseconds: 250); // 1 FPS → 4 FPS
  static const int jpegQuality = 70;  // 85% → 70% (faster upload)
  
  // Sound configuration
  static const Duration soundCooldown = Duration(milliseconds: 500);
}

class AppColors {
  // Primary colors
  static const Color primary = Color(0xFF2196F3);
  static const Color secondary = Color(0xFF03DAC6);
  
  // Alert colors
  static const Color safe = Color(0xFF4CAF50);      // Green
  static const Color far = Color(0xFFFFEB3B);       // Yellow
  static const Color medium = Color(0xFFFF9800);    // Orange
  static const Color near = Color(0xFFFF5722);      // Deep Orange
  static const Color danger = Color(0xFFF44336);    // Red
  static const Color accent = Color(0xFFE91E63);    // Pink (for VLM button)
  
  // UI colors
  static const Color background = Colors.black;
  static const Color surface = Color(0xFF1E1E1E);
  static const Color text = Colors.white;
  static const Color textSecondary = Color(0xFFBDBDBD);
}

class AppStrings {
  static const String appName = 'Gören Göz Mobil';
  static const String appDescription = 'Görme engelliler için yapay zeka destekli engel algılama sistemi';
  
  // Alert messages
  static const String alertDanger = 'TEHLİKE! Çok yakın nesne';
  static const String alertNear = 'DİKKAT! Yakın nesne';
  static const String alertMedium = 'UYARI! Orta mesafe';
  static const String alertFar = 'Uzak nesne';
  static const String alertSafe = 'Güvenli';
  
  // Error messages
  static const String errorCamera = 'Kamera erişim hatası';
  static const String errorNetwork = 'Bağlantı hatası';
  static const String errorServer = 'Sunucu hatası';
  static const String errorUnknown = 'Bilinmeyen hata';
  
  // UI labels
  static const String labelDistance = 'Mesafe';
  static const String labelFPS = 'FPS';
  static const String labelStatus = 'Durum';
  static const String labelSettings = 'Ayarlar';
}

class AppDimensions {
  static const double paddingSmall = 8.0;
  static const double paddingMedium = 16.0;
  static const double paddingLarge = 24.0;
  
  static const double borderRadiusSmall = 8.0;
  static const double borderRadiusMedium = 12.0;
  static const double borderRadiusLarge = 16.0;
  
  static const double iconSizeSmall = 16.0;
  static const double iconSizeMedium = 24.0;
  static const double iconSizeLarge = 32.0;
}
