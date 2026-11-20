// Uygulama logu. `print` yerine `debugPrint` (plan M12). Soru metni ve görüntü loglanmaz.

import 'package:flutter/foundation.dart';

class AppLogger {
  const AppLogger._();

  static void info(String message) => _log('BİLGİ', message);
  static void warning(String message) => _log('UYARI', message);
  static void error(String message, [Object? error]) =>
      _log('HATA', error == null ? message : '$message: ${error.runtimeType}');

  static void _log(String level, String message) {
    if (kReleaseMode) return;
    debugPrint('[$level] $message');
  }
}
