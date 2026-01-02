import 'package:speech_to_text/speech_to_text.dart' as stt;
import '../utils/logger.dart';

class SpeechRecognitionService {
  late stt.SpeechToText _speechToText;
  bool _isListening = false;
  bool _isInitialized = false;
  String _recognizedText = '';

  SpeechRecognitionService() {
    _speechToText = stt.SpeechToText();
  }

  bool get isListening => _isListening;
  bool get isInitialized => _isInitialized;
  String get recognizedText => _recognizedText;

  /// Initialize speech recognition (only once)
  Future<bool> initialize() async {
    if (_isInitialized) {
      AppLogger.info('Speech recognition already initialized');
      return true;
    }
    
    try {
      AppLogger.info('Initializing speech recognition (first time)...');
      
      final available = await _speechToText.initialize(
        onError: (error) {
          AppLogger.error('Speech recognition error: ${error.errorMsg}');
          _isListening = false;
        },
        onStatus: (status) {
          AppLogger.info('Speech recognition status: $status');
        },
      );
      
      if (!available) {
        AppLogger.warning('Speech recognition not available on device');
        return false;
      }
      
      // Get available locales
      try {
        final locales = await _speechToText.locales();
        AppLogger.info('Available locales: ${locales.map((l) => l.localeId).toList()}');
      } catch (e) {
        AppLogger.warning('Could not fetch locales: $e');
      }
      
      _isInitialized = true;
      AppLogger.info('Speech recognition initialized successfully');
      return true;
    } catch (e) {
      AppLogger.error('Failed to initialize speech recognition', e);
      return false;
    }
  }

  /// Start listening for speech
  Future<void> startListening({
    String languageCode = 'en_US',
    Function(String)? onResult,
  }) async {
    if (_isListening) {
      AppLogger.warning('Already listening');
      return;
    }

    if (!_speechToText.isAvailable) {
      AppLogger.error('Speech recognition not available');
      return;
    }

    try {
      _isListening = true;
      _recognizedText = '';

      // Use default system language if not specified
      String locale = languageCode;
      
      // Try requested locale, fallback to system default if not available
      try {
        final locales = await _speechToText.locales();
        final availableLocales = locales.map((l) => l.localeId).toList();
        
        if (!availableLocales.contains(locale)) {
          AppLogger.warning('Requested locale $locale not available. Using first available.');
          locale = availableLocales.isNotEmpty ? availableLocales.first : languageCode;
        }
        
        AppLogger.info('Using locale: $locale (Available: $availableLocales)');
      } catch (e) {
        AppLogger.warning('Could not check locales, using requested: $locale - $e');
      }
      
      await _speechToText.listen(
        onResult: (result) {
          _recognizedText = result.recognizedWords;
          AppLogger.info('Recognized: $_recognizedText (${result.confidence})');
          
          if (result.finalResult) {
            _isListening = false;
            AppLogger.info('Final result: $_recognizedText');
          }
          
          onResult?.call(_recognizedText);
        },
        listenFor: const Duration(seconds: 60),
        pauseFor: const Duration(seconds: 5),
        partialResults: true,
        localeId: locale,
      );
      
      AppLogger.info('Started listening with locale: $locale');
    } catch (e) {
      AppLogger.error('Error starting speech recognition', e);
      _isListening = false;
    }
  }

  /// Stop listening
  Future<void> stopListening() async {
    try {
      await _speechToText.stop();
      _isListening = false;
      AppLogger.info('Stopped listening. Final text: $_recognizedText');
    } catch (e) {
      AppLogger.error('Error stopping speech recognition', e);
    }
  }

  /// Cancel listening
  Future<void> cancel() async {
    try {
      await _speechToText.cancel();
      _isListening = false;
      _recognizedText = '';
      AppLogger.info('Speech recognition cancelled');
    } catch (e) {
      AppLogger.error('Error cancelling speech recognition', e);
    }
  }

  /// Get recognized text
  String getRecognizedText() {
    return _recognizedText;
  }

  /// Clear recognized text
  void clearRecognizedText() {
    _recognizedText = '';
  }
}
