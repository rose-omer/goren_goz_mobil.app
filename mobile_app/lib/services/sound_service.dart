///
/// Sound Service - Alert Sound Playback
/// =====================================
///

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/services.dart';
import '../models/alert_level.dart';
import '../utils/constants.dart';
import '../utils/logger.dart';

class SoundService {
  final AudioPlayer _player = AudioPlayer();
  DateTime? _lastPlayTime;
  DateTime? _lastVibrationTime;
  bool _soundEnabled = true;
  bool _vibrationEnabled = true;
  
  SoundService() {
    _player.setReleaseMode(ReleaseMode.stop);
    AppLogger.info('SoundService initialized with haptic feedback support');
  }
  
  bool get soundEnabled => _soundEnabled;
  bool get vibrationEnabled => _vibrationEnabled;
  
  void setSoundEnabled(bool enabled) {
    _soundEnabled = enabled;
    AppLogger.info('Sound ${enabled ? 'enabled' : 'disabled'}');
  }
  
  void setVibrationEnabled(bool enabled) {
    _vibrationEnabled = enabled;
    AppLogger.info('Vibration ${enabled ? 'enabled' : 'disabled'}');
  }
  
  /// Play alert sound based on level
  Future<void> playAlert(AlertLevel level) async {
    if (level != AlertLevel.danger) return; // Only alert for DANGER
    
    final now = DateTime.now();
    
    // Play sound with cooldown check
    if (_soundEnabled) {
      bool shouldPlaySound = true;
      
      if (_lastPlayTime != null) {
        final elapsed = now.difference(_lastPlayTime!);
        if (elapsed < AppConfig.soundCooldown) {
          shouldPlaySound = false;
        }
      }
      
      if (shouldPlaySound) {
        try {
          await _player.play(AssetSource('sounds/beep.mp3'));
          _lastPlayTime = now;
          AppLogger.debug('Alert sound played for $level');
        } catch (e) {
          AppLogger.error('Failed to play sound', e);
        }
      }
    }
    
    // Vibrate for danger - Heavy impact pattern (repeated for urgency)
    if (_vibrationEnabled) {
      bool shouldVibrate = true;
      
      // Check vibration cooldown (shorter than sound)
      if (_lastVibrationTime != null) {
        final elapsed = now.difference(_lastVibrationTime!);
        if (elapsed < const Duration(milliseconds: 200)) {
          shouldVibrate = false;
        }
      }
      
      if (shouldVibrate) {
        try {
          // Trigger 3 rapid heavy vibrations for danger alert
          HapticFeedback.heavyImpact();
          await Future.delayed(const Duration(milliseconds: 100));
          HapticFeedback.heavyImpact();
          await Future.delayed(const Duration(milliseconds: 100));
          HapticFeedback.heavyImpact();
          
          _lastVibrationTime = now;
          AppLogger.debug('Haptic feedback triggered for $level');
        } catch (e) {
          AppLogger.error('Failed to trigger haptic feedback', e);
        }
      }
    }
  }
  
  void dispose() {
    _player.dispose();
  }
}
