///
/// Logger Utility
/// ==============
///

import 'package:flutter/foundation.dart';

class AppLogger {
  static const String _tag = 'GorenGoz';
  
  static void debug(String message, [Object? data]) {
    if (kDebugMode) {
      print('[$_tag] DEBUG: $message ${data ?? ''}');
    }
  }
  
  static void info(String message, [Object? data]) {
    if (kDebugMode) {
      print('[$_tag] INFO: $message ${data ?? ''}');
    }
  }
  
  static void warning(String message, [Object? data]) {
    if (kDebugMode) {
      print('[$_tag] WARNING: $message ${data ?? ''}');
    }
  }
  
  static void error(String message, [Object? error, StackTrace? stackTrace]) {
    if (kDebugMode) {
      print('[$_tag] ERROR: $message');
      if (error != null) print('Error: $error');
      if (stackTrace != null) print('StackTrace: $stackTrace');
    }
  }
}
