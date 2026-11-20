// Ses, titreşim ve TTS uygulamaları. Arayüzler testte sahte sınıfla değiştirilir.

import 'dart:async';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:vibration/vibration.dart';

import '../core/hazard_engine.dart';
import '../core/speech_queue.dart';
import '../utils/logger.dart';

/// Titreşim desenleri, ms (plan 5.4).
enum HapticPattern {
  danger([0, 120, 60, 120, 60, 120], 255),
  near([0, 80, 120, 80], 180),
  info([0, 40], 100),
  listenStart([0, 30], 120),
  answer([0, 30, 80, 30], 120),
  disconnected([0, 300], 200);

  const HapticPattern(this.pattern, this.amplitude);

  final List<int> pattern;
  final int amplitude;

  static HapticPattern? forLevel(AlertLevel level) => switch (level) {
    AlertLevel.danger => HapticPattern.danger,
    AlertLevel.near => HapticPattern.near,
    AlertLevel.info => HapticPattern.info,
    AlertLevel.clear => null,
  };
}

enum Cue {
  danger('sounds/danger.wav'),
  near('sounds/near.wav'),
  info('sounds/info.wav'),
  listenStart('sounds/listen_start.wav'),
  listenEnd('sounds/listen_end.wav'),
  tick('sounds/tick.wav');

  const Cue(this.asset);

  final String asset;

  static Cue? forLevel(AlertLevel level) => switch (level) {
    AlertLevel.danger => Cue.danger,
    AlertLevel.near => Cue.near,
    AlertLevel.info => Cue.info,
    AlertLevel.clear => null,
  };
}

abstract interface class Haptics {
  Future<void> play(HapticPattern pattern);
}

abstract interface class Sounds {
  Future<void> play(Cue cue);
}

class DeviceHaptics implements Haptics {
  DeviceHaptics({required this.enabled});

  bool Function() enabled;
  bool? _hasAmplitude;

  @override
  Future<void> play(HapticPattern pattern) async {
    if (!enabled()) return;
    try {
      _hasAmplitude ??= await Vibration.hasAmplitudeControl();
      final amplitudes = _hasAmplitude!
          ? [for (var i = 0; i < pattern.pattern.length; i++) i.isOdd ? pattern.amplitude : 0]
          : const <int>[];
      await Vibration.vibrate(pattern: pattern.pattern, intensities: amplitudes);
    } on Exception catch (error) {
      AppLogger.warning('Titreşim çalmadı: $error');
    }
  }
}

class AssetSounds implements Sounds {
  final Map<Cue, AudioPlayer> _players = {};

  @override
  Future<void> play(Cue cue) async {
    final player = _players.putIfAbsent(cue, () => AudioPlayer()..setPlayerMode(PlayerMode.lowLatency));
    try {
      await player.stop();
      await player.play(AssetSource(cue.asset));
    } on Exception catch (error) {
      AppLogger.warning('Ses çalmadı: $error');
    }
  }

  Future<void> dispose() async {
    for (final player in _players.values) {
      await player.dispose();
    }
  }
}

/// flutter_tts tabanlı konuşmacı. Dil tr-TR; [speak] konuşma bitince tamamlanır.
class TtsSpeaker implements Speaker {
  TtsSpeaker() {
    _ready = _init();
  }

  final FlutterTts _tts = FlutterTts();
  late final Future<void> _ready;

  Future<void> _init() async {
    await _tts.setLanguage('tr-TR');
    await _tts.awaitSpeakCompletion(true);
    // Uyarı kısa süreli ses odağı ister; müzik kısılır, sonra geri gelir (plan 5.3).
    await _tts.setAudioAttributesForNavigation();
  }

  Future<void> configure({required double rate, required double volume}) async {
    await _ready;
    await _tts.setSpeechRate(rate);
    await _tts.setVolume(volume);
  }

  @override
  Future<void> speak(String text) async {
    try {
      await _ready;
      await _tts.speak(text);
    } on Exception catch (error) {
      AppLogger.warning('TTS konuşmadı: $error');
    }
  }

  @override
  Future<void> stop() async {
    try {
      await _tts.stop();
    } on Exception catch (error) {
      AppLogger.warning('TTS durmadı: $error');
    }
  }
}
