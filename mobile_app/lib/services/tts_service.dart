///
/// TTS Service - Text-to-Speech for Voice Guidance
/// =================================================
///

import 'package:flutter_tts/flutter_tts.dart';
import '../models/alert_level.dart';
import '../utils/logger.dart';

class TtsService {
  final FlutterTts _tts = FlutterTts();
  DateTime? _lastSpeakTime;
  bool _ttsEnabled = true;
  String _language = 'tr-TR';
  double _speechRate = 0.5; // 0.5 = normal speed
  double _pitch = 1.0;
  bool _isInitialized = false;

  TtsService() {
    _initTts();
  }

  Future<void> _initTts() async {
    try {
      // Set language
      await _tts.setLanguage(_language);
      
      // Set speech rate (0.0 - 1.0)
      await _tts.setSpeechRate(_speechRate);
      
      // Set pitch (0.5 - 2.0)
      await _tts.setPitch(_pitch);
      
      // Set volume (0.0 - 1.0)
      await _tts.setVolume(1.0);
      
      _isInitialized = true;
      AppLogger.info('TTS Service initialized - Language: $_language');
    } catch (e) {
      AppLogger.error('Failed to initialize TTS', e);
      _isInitialized = false;
    }
  }

  bool get ttsEnabled => _ttsEnabled;
  String get language => _language;
  
  void setTtsEnabled(bool enabled) {
    _ttsEnabled = enabled;
    AppLogger.info('TTS ${enabled ? 'enabled' : 'disabled'}');
  }
  
  Future<void> setLanguage(String language) async {
    _language = language;
    await _tts.setLanguage(_language);
    AppLogger.info('TTS language set to: $language');
  }
  
  Future<void> setSpeechRate(double rate) async {
    _speechRate = rate.clamp(0.0, 1.0);
    await _tts.setSpeechRate(_speechRate);
  }
  
  Future<void> setPitch(double pitch) async {
    _pitch = pitch.clamp(0.5, 2.0);
    await _tts.setPitch(_pitch);
  }

  /// Speak alert message based on level and distance
  Future<void> speakAlert(AlertLevel level, double? distance) async {
    if (!_ttsEnabled || !_isInitialized) return;
    
    // Check cooldown (don't spam messages)
    final now = DateTime.now();
    if (_lastSpeakTime != null) {
      final elapsed = now.difference(_lastSpeakTime!);
      if (elapsed < const Duration(seconds: 3)) {
        return; // Skip if spoken recently
      }
    }
    
    final message = _buildMessage(level, distance);
    if (message.isEmpty) return;
    
    try {
      // Stop any ongoing speech
      await _tts.stop();
      
      // Speak the message
      await _tts.speak(message);
      
      _lastSpeakTime = now;
      AppLogger.debug('TTS: $message');
    } catch (e) {
      AppLogger.error('Failed to speak', e);
    }
  }

  /// Speak regional alert (left, center, right)
  Future<void> speakRegionalAlert({
    required String region,
    required String alertLevel,
    required double distance,
  }) async {
    if (!_ttsEnabled || !_isInitialized) return;
    if (alertLevel == 'SAFE') return;
    
    // Check cooldown
    final now = DateTime.now();
    if (_lastSpeakTime != null) {
      final elapsed = now.difference(_lastSpeakTime!);
      if (elapsed < const Duration(seconds: 3)) {
        return;
      }
    }
    
    final message = _buildRegionalMessage(region, alertLevel, distance);
    if (message.isEmpty) return;
    
    try {
      await _tts.stop();
      await _tts.speak(message);
      _lastSpeakTime = now;
      AppLogger.debug('TTS Regional: $message');
    } catch (e) {
      AppLogger.error('Failed to speak regional alert', e);
    }
  }

  /// Speak object detection result
  Future<void> speakObject({
    required String objectName,
    required String region,
    required double distance,
  }) async {
    if (!_ttsEnabled || !_isInitialized) return;
    
    // Check if critical object - shorter cooldown
    final isCritical = _isCriticalObject(objectName);
    final cooldownSeconds = isCritical ? 2 : 4;
    
    // Check cooldown
    final now = DateTime.now();
    if (_lastSpeakTime != null) {
      final elapsed = now.difference(_lastSpeakTime!);
      if (elapsed < Duration(seconds: cooldownSeconds)) {
        return;
      }
    }
    
    // Use smart contextual messages for known critical objects
    final message = _buildSmartObjectMessage(objectName, region, distance);
    if (message.isEmpty) return;
    
    try {
      await _tts.stop();
      await _tts.speak(message);
      _lastSpeakTime = now;
      AppLogger.debug('TTS Object: $message');
    } catch (e) {
      AppLogger.error('Failed to speak object detection', e);
    }
  }
  
  /// Build object detection message
  String _buildObjectMessage(String objectName, String region, double distance) {
    final distanceText = '${distance.toStringAsFixed(1)} metre';
    
    if (_language.startsWith('tr')) {
      // Turkish
      String regionText;
      
      switch (region) {
        case 'left':
          regionText = 'Sol tarafta';
          break;
        case 'right':
          regionText = 'Sağ tarafta';
          break;
        case 'center':
        default:
          regionText = 'Önünüzde';
      }
      
      return '$regionText $objectName var. $distanceText mesafede.';
    } else {
      // English
      String regionText;
      
      switch (region) {
        case 'left':
          regionText = 'On the left';
          break;
        case 'right':
          regionText = 'On the right';
          break;
        case 'center':
        default:
          regionText = 'Ahead';
      }
      
      return '$regionText, $objectName. $distanceText meters away.';
    }
  }

  /// Build regional message
  String _buildRegionalMessage(String region, String alertLevel, double distance) {
    final distanceText = '${distance.toStringAsFixed(1)} metre';
    
    if (_language.startsWith('tr')) {
      // Turkish
      String regionText;
      String action;
      
      switch (region) {
        case 'left':
          regionText = 'Sol tarafta';
          action = 'sağa dönün';
          break;
        case 'right':
          regionText = 'Sağ tarafta';
          action = 'sola dönün';
          break;
        case 'center':
        default:
          regionText = 'Önünüzde';
          action = 'durun';
      }
      
      switch (alertLevel) {
        case 'DANGER':
          return '$regionText tehlike! $distanceText mesafede. $action!';
        case 'NEAR':
          return '$regionText yakın engel. $distanceText mesafede. $action.';
        case 'MEDIUM':
          return '$regionText orta mesafede engel. $distanceText ileride.';
        default:
          return '';
      }
    } else {
      // English
      String regionText;
      String action;
      
      switch (region) {
        case 'left':
          regionText = 'On the left';
          action = 'turn right';
          break;
        case 'right':
          regionText = 'On the right';
          action = 'turn left';
          break;
        case 'center':
        default:
          regionText = 'Ahead';
          action = 'stop';
      }
      
      switch (alertLevel) {
        case 'DANGER':
          return '$regionText danger! $distanceText away. $action!';
        case 'NEAR':
          return '$regionText close obstacle. $distanceText away. $action.';
        case 'MEDIUM':
          return '$regionText medium distance. $distanceText ahead.';
        default:
          return '';
      }
    }
  }

  /// Build message based on alert level and distance
  String _buildMessage(AlertLevel level, double? distance) {
    final distanceText = distance != null 
        ? '${distance.toStringAsFixed(1)} metre'
        : '';
    
    if (_language.startsWith('tr')) {
      // Turkish messages
      switch (level) {
        case AlertLevel.danger:
          return 'TEHLİKE! Çok yakın engel! $distanceText mesafede. Durun!';
        case AlertLevel.near:
          return 'DİKKAT! Yakın engel. $distanceText mesafede.';
        case AlertLevel.medium:
          return 'Orta mesafede engel. $distanceText ileride.';
        case AlertLevel.far:
          return 'Uzak mesafede nesne tespit edildi.';
        case AlertLevel.safe:
          return ''; // Don't announce safe state
      }
    } else {
      // English messages
      switch (level) {
        case AlertLevel.danger:
          return 'DANGER! Very close obstacle! $distanceText away. Stop!';
        case AlertLevel.near:
          return 'WARNING! Close obstacle. $distanceText away.';
        case AlertLevel.medium:
          return 'Medium distance obstacle. $distanceText ahead.';
        case AlertLevel.far:
          return 'Far object detected.';
        case AlertLevel.safe:
          return ''; // Don't announce safe state
      }
    }
  }

  /// Check if an object is critical for safety
  bool _isCriticalObject(String objectName) {
    final critical = [
      // İnsanlar
      'insan', 'person', 
      // Yapılar
      'merdiven', 'stairs', 
      'duvar', 'wall', 
      'kapı', 'door',
      // Araçlar
      'araba', 'car', 
      'kamyon', 'truck',
      'otobüs', 'bus',
      'motosiklet', 'motorcycle',
      'bisiklet', 'bicycle',
      // Dış mekan engelleri
      'direk', 'pole',
      'yangın musluğu', 'fire hydrant',
      'bank', 'bench',
      'çit', 'fence',
      'sokak lambası', 'street light',
      'çöp kutusu', 'trash can',
    ];
    return critical.contains(objectName.toLowerCase());
  }

  /// Build smart contextual warning for detected objects
  String _buildSmartObjectMessage(String objectName, String region, double distance) {
    final distanceText = distance.toStringAsFixed(1);
    final objLower = objectName.toLowerCase();
    
    if (_language.startsWith('tr')) {
      // Turkish contextual warnings
      switch (objLower) {
        case 'insan':
        case 'person':
          if (distance < 1.0) return 'DİKKAT! Çok yakında insan var!';
          if (region.contains('center')) return 'Önünüzde insan var. Dikkatli yürüyün.';
          if (region.contains('left')) return 'Sol tarafınızda insan var. Sağa doğru ilerleyin.';
          if (region.contains('right')) return 'Sağ tarafınızda insan var. Sola doğru ilerleyin.';
          return 'İnsan tespit edildi. $distanceText metre mesafede.';
          
        case 'merdiven':
        case 'stairs':
          return 'MERDİVEN TESPİT EDİLDİ! Çok dikkatli olun! Elinizi korkuluğa koyun.';
          
        case 'araba':
        case 'car':
        case 'kamyon':
        case 'truck':
        case 'otobüs':
        case 'bus':
          if (distance < 2.0) return 'TEHLİKE! ARAÇ ÇOK YAKIN! GERİ ÇEKİLİN!';
          return 'Dikkat! Araç tespit edildi. $distanceText metre mesafede. Durun!';
          
        case 'motosiklet':
        case 'motorcycle':
          if (distance < 2.0) return 'TEHLİKE! MOTOSİKLET YAKIN! DİKKAT!';
          return 'Motosiklet tespit edildi. Dikkatli olun.';
          
        case 'bisiklet':
        case 'bicycle':
          return 'Bisiklet tespit edildi. Yoldan çekilin.';
          
        case 'duvar':
        case 'wall':
          if (region.contains('center')) return 'Önünüzde duvar var. Sağa veya sola dönün.';
          if (region.contains('left')) return 'Sol tarafta duvar. Sağa doğru ilerleyin.';
          if (region.contains('right')) return 'Sağ tarafta duvar. Sola doğru ilerleyin.';
          return 'Duvar tespit edildi. Yön değiştirin.';
          
        case 'kapı':
        case 'door':
          if (region.contains('center')) return 'Önünüzde kapı var. Kolunuzu uzatın.';
          if (region.contains('left')) return 'Sol tarafta kapı var.';
          if (region.contains('right')) return 'Sağ tarafta kapı var.';
          return 'Kapı tespit edildi.';
          
        // DIŞ MEKAN NESNELERİ
        case 'direk':
        case 'pole':
        case 'sokak lambası':
        case 'street light':
          if (region.contains('center')) return 'ÖNÜNÜZDE DİREK VAR! Sağa veya sola kaçının!';
          if (region.contains('left')) return 'Sol tarafta direk var. Sağdan geçin.';
          if (region.contains('right')) return 'Sağ tarafta direk var. Soldan geçin.';
          return 'Direk tespit edildi. Dikkatli geçin.';
          
        case 'yangın musluğu':
        case 'fire hydrant':
          if (region.contains('center')) return 'Önünüzde yangın musluğu var! Etrafından dolanın.';
          return 'Yangın musluğu tespit edildi. Takılmamaya dikkat edin.';
          
        case 'bank':
        case 'bench':
          if (region.contains('center')) return 'Önünüzde oturma bankı var. Etrafından dolanın.';
          if (region.contains('left')) return 'Sol tarafta bank var.';
          if (region.contains('right')) return 'Sağ tarafta bank var.';
          return 'Bank tespit edildi.';
          
        case 'çit':
        case 'fence':
          if (region.contains('center')) return 'Önünüzde çit var! Geçiş yolu arayın.';
          if (region.contains('left')) return 'Sol tarafta çit. Sağa dönün.';
          if (region.contains('right')) return 'Sağ tarafta çit. Sola dönün.';
          return 'Çit tespit edildi.';
          
        case 'çöp kutusu':
        case 'trash can':
          if (region.contains('center')) return 'Önünüzde çöp kutusu var. Etrafından dolanın.';
          return 'Çöp kutusu tespit edildi.';
          
        case 'trafik ışığı':
        case 'traffic light':
          return 'Trafik ışığı tespit edildi. Işıklara dikkat edin!';
          
        case 'dur işareti':
        case 'stop sign':
          return 'Dur işareti tespit edildi. Bekleyin!';
          
        case 'sandalye':
        case 'chair':
          if (region.contains('center')) return 'Önünüzde sandalye var. Etrafından dolaşın.';
          return 'Sandalye tespit edildi. Dikkatli geçin.';
          
        case 'masa':
        case 'dining table':
          return 'Masa tespit edildi. Kenarından dolaşın.';
          
        case 'koltuk':
        case 'couch':
          return 'Koltuk var. Dikkatli ilerleyin.';
        
        case 'köpek':
        case 'dog':
          return 'Köpek tespit edildi. Dikkatli olun!';
          
        case 'kedi':
        case 'cat':
          return 'Kedi tespit edildi.';
          
        default:
          return '$objectName tespit edildi. $distanceText metre mesafede.';
      }
    } else {
      // English contextual warnings
      switch (objLower) {
        case 'insan':
        case 'person':
          if (distance < 1.0) return 'WARNING! Person very close!';
          if (region.contains('center')) return 'Person ahead. Walk carefully.';
          if (region.contains('left')) return 'Person on your left. Move right.';
          if (region.contains('right')) return 'Person on your right. Move left.';
          return 'Person detected. $distanceText meters away.';
          
        case 'merdiven':
        case 'stairs':
          return 'STAIRS DETECTED! Be very careful! Hold the handrail.';
          
        case 'araba':
        case 'car':
        case 'kamyon':
        case 'truck':
        case 'otobüs':
        case 'bus':
          if (distance < 2.0) return 'DANGER! VEHICLE VERY CLOSE! STEP BACK!';
          return 'Warning! Vehicle detected. $distanceText meters away. Stop!';
          
        case 'motosiklet':
        case 'motorcycle':
          if (distance < 2.0) return 'DANGER! MOTORCYCLE CLOSE! WATCH OUT!';
          return 'Motorcycle detected. Be careful.';
          
        case 'bisiklet':
        case 'bicycle':
          return 'Bicycle detected. Step aside.';
          
        case 'duvar':
        case 'wall':
          if (region.contains('center')) return 'Wall ahead. Turn left or right.';
          if (region.contains('left')) return 'Wall on left. Move right.';
          if (region.contains('right')) return 'Wall on right. Move left.';
          return 'Wall detected. Change direction.';
          
        case 'kapı':
        case 'door':
          if (region.contains('center')) return 'Door ahead. Reach out your hand.';
          if (region.contains('left')) return 'Door on the left.';
          if (region.contains('right')) return 'Door on the right.';
          return 'Door detected.';
          
        // OUTDOOR OBJECTS
        case 'direk':
        case 'pole':
        case 'sokak lambası':
        case 'street light':
          if (region.contains('center')) return 'POLE AHEAD! Move left or right!';
          if (region.contains('left')) return 'Pole on the left. Pass on the right.';
          if (region.contains('right')) return 'Pole on the right. Pass on the left.';
          return 'Pole detected. Pass carefully.';
          
        case 'yangın musluğu':
        case 'fire hydrant':
          if (region.contains('center')) return 'Fire hydrant ahead! Walk around it.';
          return 'Fire hydrant detected. Watch your step.';
          
        case 'bank':
        case 'bench':
          if (region.contains('center')) return 'Bench ahead. Walk around it.';
          if (region.contains('left')) return 'Bench on the left.';
          if (region.contains('right')) return 'Bench on the right.';
          return 'Bench detected.';
          
        case 'çit':
        case 'fence':
          if (region.contains('center')) return 'Fence ahead! Find a passage.';
          if (region.contains('left')) return 'Fence on the left. Turn right.';
          if (region.contains('right')) return 'Fence on the right. Turn left.';
          return 'Fence detected.';
          
        case 'çöp kutusu':
        case 'trash can':
          if (region.contains('center')) return 'Trash can ahead. Walk around it.';
          return 'Trash can detected.';
          
        case 'trafik ışığı':
        case 'traffic light':
          return 'Traffic light detected. Watch the lights!';
          
        case 'dur işareti':
        case 'stop sign':
          return 'Stop sign detected. Wait!';
          
        case 'sandalye':
        case 'chair':
          if (region.contains('center')) return 'Chair ahead. Walk around it.';
          return 'Chair detected. Pass carefully.';
          
        case 'masa':
        case 'dining table':
          return 'Table detected. Walk around it.';
          
        case 'koltuk':
        case 'couch':
          return 'Couch detected. Walk carefully.';
        
        case 'köpek':
        case 'dog':
          return 'Dog detected. Be careful!';
          
        case 'kedi':
        case 'cat':
          return 'Cat detected.';
          
        default:
          return '$objectName detected. $distanceText meters away.';
      }
    }
  }

  /// Speak custom message
  Future<void> speak(String message) async {
    if (!_ttsEnabled || !_isInitialized) return;
    
    try {
      await _tts.stop();
      await _tts.speak(message);
    } catch (e) {
      AppLogger.error('Failed to speak custom message', e);
    }
  }

  /// Stop speaking
  Future<void> stop() async {
    try {
      await _tts.stop();
    } catch (e) {
      AppLogger.error('Failed to stop TTS', e);
    }
  }

  void dispose() {
    _tts.stop();
  }
}
