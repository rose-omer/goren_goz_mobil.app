// Konuşma tanıma. Dil tr_TR (plan 4.6). Mikrofon izni ilk soru anında istenir (plan M11).

import 'dart:async';

import 'package:permission_handler/permission_handler.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

import '../utils/logger.dart';

enum ListenFailure { permissionDenied, unavailable, nothingHeard }

abstract interface class SpeechInput {
  /// Dinlemeyi başlatır. Hata varsa nedenini döner.
  Future<ListenFailure?> start();

  /// Dinlemeyi bitirir ve tanınan metni döner.
  Future<String> finish();

  Future<void> cancel();
}

class DeviceSpeechInput implements SpeechInput {
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _initialized = false;
  String _text = '';
  Completer<void>? _final;

  static const locale = 'tr_TR';

  @override
  Future<ListenFailure?> start() async {
    final permission = await Permission.microphone.request();
    if (!permission.isGranted) return ListenFailure.permissionDenied;
    if (!_initialized) {
      _initialized = await _speech.initialize(
        onError: (error) => AppLogger.warning('Konuşma tanıma hatası: ${error.errorMsg}'),
      );
      if (!_initialized) return ListenFailure.unavailable;
    }
    _text = '';
    _final = Completer<void>();
    await _speech.listen(
      onResult: (result) {
        _text = result.recognizedWords;
        if (result.finalResult && !(_final?.isCompleted ?? true)) _final!.complete();
      },
      listenOptions: stt.SpeechListenOptions(
        localeId: locale,
        listenFor: const Duration(seconds: 20),
        pauseFor: const Duration(seconds: 4),
        partialResults: true,
        cancelOnError: true,
      ),
    );
    return null;
  }

  @override
  Future<String> finish() async {
    await _speech.stop();
    // Son sonuç kısa bir gecikmeyle gelir.
    await _final?.future.timeout(const Duration(milliseconds: 800), onTimeout: () {});
    return _text.trim();
  }

  @override
  Future<void> cancel() async {
    _text = '';
    await _speech.cancel();
  }
}
