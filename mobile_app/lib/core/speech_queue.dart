// Konuşma kuyruğu (plan 4.4):
// - DANGER her şeyi keser.
// - Aynı nesne-yön mesajı 6 s içinde tekrar edilmez (seviye yükselmedikçe).
// - Kuyrukta en fazla 2 mesaj; eskiler atılır.

import 'dart:async';
import 'dart:collection';

import 'hazard_engine.dart';

/// TTS soyutlaması. [speak] konuşma bitince tamamlanır.
abstract interface class Speaker {
  Future<void> speak(String text);
  Future<void> stop();
}

class SpeechItem {
  const SpeechItem(this.text, this.level, this.key);

  final String text;
  final AlertLevel level;
  final String key;
}

class SpeechQueue {
  SpeechQueue(
    this._speaker, {
    DateTime Function()? clock,
    this.repeatWindow = const Duration(seconds: 6),
    this.maxQueued = 2,
  }) : _clock = clock ?? DateTime.now;

  final Speaker _speaker;
  final DateTime Function() _clock;
  final Duration repeatWindow;
  final int maxQueued;

  final Queue<SpeechItem> _queue = Queue<SpeechItem>();
  final Map<String, DateTime> _lastSpoken = {};
  final Map<String, AlertLevel> _lastLevel = {};
  SpeechItem? _current;

  bool get isSpeaking => _current != null;
  List<SpeechItem> get pending => List.unmodifiable(_queue);

  /// Mesajı sıraya alır. Boş metin ve 6 s içindeki tekrar atılır.
  /// [force] tekrar penceresini yok sayar (kullanıcı "Durumu söyle" dediğinde).
  void enqueue(String text, AlertLevel level, {String? key, bool force = false}) {
    if (text.trim().isEmpty) return;
    final itemKey = key ?? text;
    final now = _clock();
    final last = _lastSpoken[itemKey];
    // Seviye yükseldiyse (Dikkat → Dur) tekrar penceresi beklenmez.
    final escalated = level > (_lastLevel[itemKey] ?? AlertLevel.clear);
    if (!force && !escalated && last != null && now.difference(last) < repeatWindow) return;
    final duplicate = _queue.any((item) => item.key == itemKey) || _current?.key == itemKey;
    if (duplicate && !force && !escalated) return;
    _queue.removeWhere((item) => item.key == itemKey);

    final item = SpeechItem(text, level, itemKey);
    if (level == AlertLevel.danger || force) {
      _queue.clear();
      _queue.addFirst(item);
      if (_current != null) {
        unawaited(_speaker.stop());
        _current = null;
      }
    } else {
      _queue.addLast(item);
      while (_queue.length > maxQueued) {
        _queue.removeFirst();
      }
    }
    _pump();
  }

  /// Kuyruğu boşaltır ve konuşmayı keser (duraklat).
  Future<void> clear() async {
    _queue.clear();
    _current = null;
    await _speaker.stop();
  }

  void _pump() {
    if (_current != null || _queue.isEmpty) return;
    final item = _queue.removeFirst();
    _current = item;
    _lastSpoken[item.key] = _clock();
    _lastLevel[item.key] = item.level;
    _speaker.speak(item.text).whenComplete(() {
      if (identical(_current, item)) _current = null;
      _pump();
    });
  }
}
