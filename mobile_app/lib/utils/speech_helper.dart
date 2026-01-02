///
/// Speech Helper - Text-to-Speech for VLM Answers
/// =================================================
///

import 'package:flutter_tts/flutter_tts.dart';
import 'logger.dart';

class SpeechHelper {
  static final SpeechHelper _instance = SpeechHelper._internal();
  factory SpeechHelper() => _instance;
  SpeechHelper._internal();

  final FlutterTts _flutterTts = FlutterTts();
  bool _isInitialized = false;

  /// Initialize TTS engine
  Future<void> initialize() async {
    if (_isInitialized) return;

    try {
      // Configure TTS
      await _flutterTts.setLanguage('tr-TR'); // Turkish
      await _flutterTts.setSpeechRate(0.5); // Normal speed
      await _flutterTts.setVolume(1.0); // Full volume
      await _flutterTts.setPitch(1.0); // Normal pitch

      // Check if Turkish is available
      final languages = await _flutterTts.getLanguages;
      final hasTurkish = languages.toString().contains('tr');
      
      if (!hasTurkish) {
        AppLogger.warning('Turkish language not available for TTS');
      } else {
        AppLogger.info('TTS initialized with Turkish language');
      }

      _isInitialized = true;
    } catch (e) {
      AppLogger.error('Failed to initialize TTS: $e');
    }
  }

  /// Speak text
  Future<void> speak(String text) async {
    if (!_isInitialized) {
      await initialize();
    }

    try {
      AppLogger.info('Speaking: ${text.substring(0, text.length > 50 ? 50 : text.length)}...');
      await _flutterTts.speak(text);
    } catch (e) {
      AppLogger.error('Failed to speak text: $e');
    }
  }

  /// Stop speaking
  Future<void> stop() async {
    try {
      await _flutterTts.stop();
    } catch (e) {
      AppLogger.error('Failed to stop TTS: $e');
    }
  }

  /// Check if currently speaking
  Future<bool> isSpeaking() async {
    try {
      final status = await _flutterTts.awaitSpeakCompletion(false);
      return status;
    } catch (e) {
      return false;
    }
  }

  /// Set speech rate (0.0 to 1.0, default 0.5)
  Future<void> setSpeechRate(double rate) async {
    try {
      await _flutterTts.setSpeechRate(rate.clamp(0.0, 1.0));
    } catch (e) {
      AppLogger.error('Failed to set speech rate: $e');
    }
  }

  /// Set volume (0.0 to 1.0)
  Future<void> setVolume(double volume) async {
    try {
      await _flutterTts.setVolume(volume.clamp(0.0, 1.0));
    } catch (e) {
      AppLogger.error('Failed to set volume: $e');
    }
  }

  /// Dispose TTS engine
  void dispose() {
    _flutterTts.stop();
    _isInitialized = false;
  }
}
