// Kalıcı kullanıcı ayarları (SharedPreferences). Sunucu adresi ve anahtarı da burada (plan M9).

import 'package:flutter/foundation.dart' show kDebugMode;
import 'package:material_ui/material_ui.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/hazard_engine.dart';

enum Verbosity { dangerOnly, all }

enum Contrast { darkSignal, lightInk }

class SettingsStore extends ChangeNotifier {
  SettingsStore(this._prefs);

  final SharedPreferences _prefs;

  static Future<SettingsStore> load() async => SettingsStore(await SharedPreferences.getInstance());

  static const _kRate = 'speech_rate';
  static const _kVolume = 'speech_volume';
  static const _kVibration = 'vibration';
  static const _kDirection = 'direction_style';
  static const _kVerbosity = 'verbosity';
  static const _kServerUrl = 'server_url';
  static const _kApiKey = 'api_key';
  static const _kServerAnalysis = 'server_analysis';
  static const _kAssistantView = 'assistant_view';
  static const _kContrast = 'contrast';
  static const _kOnboarded = 'onboarded';
  static const _kSafetyHeard = 'safety_heard';
  static const _kFocal = 'focal_px_640';

  /// Varsayılan yok: adres ilk açılışta ayarlardan girilir (plan G8, 7.1).
  static const defaultServerUrl = '';

  double get speechRate => _prefs.getDouble(_kRate) ?? 0.6;
  double get volume => _prefs.getDouble(_kVolume) ?? 1.0;
  bool get vibration => _prefs.getBool(_kVibration) ?? true;
  DirectionStyle get directionStyle => DirectionStyle.values[_prefs.getInt(_kDirection) ?? 0];
  Verbosity get verbosity => Verbosity.values[_prefs.getInt(_kVerbosity) ?? Verbosity.all.index];
  String get serverUrl => _prefs.getString(_kServerUrl) ?? defaultServerUrl;
  String get apiKey => _prefs.getString(_kApiKey) ?? '';
  bool get serverAnalysis => _prefs.getBool(_kServerAnalysis) ?? true;
  bool get assistantView => _prefs.getBool(_kAssistantView) ?? false;
  Contrast get contrast => Contrast.values[_prefs.getInt(_kContrast) ?? 0];
  bool get onboarded => _prefs.getBool(_kOnboarded) ?? false;
  bool get safetyHeard => _prefs.getBool(_kSafetyHeard) ?? false;

  /// 640 px uzun kenarlı gönderim karesinde odak uzaklığı. Kalibre edilmediyse `null`.
  double? get focalPx => _prefs.getDouble(_kFocal);

  bool get hasServer => serverUrl.isNotEmpty;

  Future<void> setSpeechRate(double value) => _set(() => _prefs.setDouble(_kRate, value.clamp(0.3, 1.0)));
  Future<void> setVolume(double value) => _set(() => _prefs.setDouble(_kVolume, value.clamp(0.0, 1.0)));
  Future<void> setVibration(bool value) => _set(() => _prefs.setBool(_kVibration, value));
  Future<void> setDirectionStyle(DirectionStyle value) => _set(() => _prefs.setInt(_kDirection, value.index));
  Future<void> setVerbosity(Verbosity value) => _set(() => _prefs.setInt(_kVerbosity, value.index));
  Future<void> setServerUrl(String value) => _set(() => _prefs.setString(_kServerUrl, value.trim()));
  Future<void> setApiKey(String value) => _set(() => _prefs.setString(_kApiKey, value.trim()));
  Future<void> setServerAnalysis(bool value) => _set(() => _prefs.setBool(_kServerAnalysis, value));
  Future<void> setAssistantView(bool value) => _set(() => _prefs.setBool(_kAssistantView, value));
  Future<void> setContrast(Contrast value) => _set(() => _prefs.setInt(_kContrast, value.index));
  Future<void> setOnboarded(bool value) => _set(() => _prefs.setBool(_kOnboarded, value));
  Future<void> setSafetyHeard(bool value) => _set(() => _prefs.setBool(_kSafetyHeard, value));

  Future<void> _set(Future<bool> Function() write) async {
    await write();
    notifyListeners();
  }
}

/// Düz HTTP yalnız debug sürümünde açık. Release ve profile sürümünde
/// `res/xml/network_security_config.xml` düz HTTP'yi işletim sistemi düzeyinde kapatır;
/// Android IP aralığı için istisna tanımlayamaz (plan G8).
const bool localHttpAllowed = kDebugMode;

String _exampleUrl(bool allowHttp) => allowHttp ? 'http://192.168.1.20:8110' : 'https://sunucu.ornek.com';

/// Ayar alanının altındaki yardım metni; sürümün kabul ettiği adres biçimini söyler.
String serverUrlHelp({bool allowHttp = localHttpAllowed}) => allowHttp
    ? 'Örnek: ${_exampleUrl(true)}. Ağ dışı sunucu için https.'
    : 'Örnek: ${_exampleUrl(false)}. Bu sürüm yalnız https adresine bağlanır.';

/// Sunucu adresi doğrulaması. Debug sürümünde yerel ağ IP'lerine düz HTTP izni var (plan G8).
String? validateServerUrl(String raw, {bool allowHttp = localHttpAllowed}) {
  final value = raw.trim();
  if (value.isEmpty) return 'Sunucu adresini yazın. Örnek: ${_exampleUrl(allowHttp)}';
  final uri = Uri.tryParse(value);
  final schemeHint = allowHttp ? 'Adres http:// ya da https:// ile başlamalı.' : 'Adres https:// ile başlamalı.';
  if (uri == null || !uri.hasScheme || uri.host.isEmpty) return schemeHint;
  if (uri.scheme == 'https') return null;
  if (uri.scheme != 'http') return schemeHint;
  if (!allowHttp) return 'Bu sürüm http:// adresine bağlanamaz. Sunucuyu https:// ile açın.';
  if (!isLocalHost(uri.host)) return 'Yerel ağ dışındaki sunucu için https:// kullanın.';
  return null;
}

bool isLocalHost(String host) {
  if (host == 'localhost' || host == '127.0.0.1') return true;
  final parts = host.split('.').map(int.tryParse).toList();
  if (parts.length != 4 || parts.any((p) => p == null || p < 0 || p > 255)) return false;
  final a = parts[0]!, b = parts[1]!;
  return a == 10 || (a == 192 && b == 168) || (a == 172 && b >= 16 && b <= 31);
}
