///
/// Settings Screen
/// ===============
///

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_service.dart';
import '../services/sound_service.dart';
import '../services/tts_service.dart';
import '../utils/constants.dart';

class SettingsScreen extends StatefulWidget {
  final Function(bool isDark, bool highContrast)? onThemeChanged;
  
  const SettingsScreen({super.key, this.onThemeChanged});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _apiUrlController;
  bool _soundEnabled = true;
  bool _vibrationEnabled = true;
  bool _ttsEnabled = true;
  double _soundVolume = 1.0;
  double _vibrationIntensity = 1.0;
  double _speechRate = 0.5;
  int _frameRate = 1;
  bool _isDarkMode = true;
  bool _isHighContrast = false;
  String _language = 'TR';
  
  // Distance thresholds (meters)
  double _dangerThreshold = 0.5;
  double _nearThreshold = 1.0;
  double _mediumThreshold = 2.0;
  double _farThreshold = 3.0;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    final apiService = context.read<ApiService>();
    final soundService = context.read<SoundService>();
    final ttsService = context.read<TtsService>();

    setState(() {
      _apiUrlController = TextEditingController(text: apiService.apiUrl);
      _soundEnabled = soundService.soundEnabled;
      _vibrationEnabled = soundService.vibrationEnabled;
      _ttsEnabled = ttsService.ttsEnabled;
      _soundVolume = prefs.getDouble('sound_volume') ?? 1.0;
      _vibrationIntensity = prefs.getDouble('vibration_intensity') ?? 1.0;
      _speechRate = prefs.getDouble('speech_rate') ?? 0.5;
      _frameRate = prefs.getInt('frame_rate') ?? 1;
      _isDarkMode = prefs.getBool('dark_mode') ?? true;
      _isHighContrast = prefs.getBool('high_contrast') ?? false;
      _language = prefs.getString('language') ?? 'TR';
      
      _dangerThreshold = prefs.getDouble('danger_threshold') ?? 0.5;
      _nearThreshold = prefs.getDouble('near_threshold') ?? 1.0;
      _mediumThreshold = prefs.getDouble('medium_threshold') ?? 2.0;
      _farThreshold = prefs.getDouble('far_threshold') ?? 3.0;
    });
  }

  Future<void> _saveSettings() async {
    final prefs = await SharedPreferences.getInstance();
    final apiService = context.read<ApiService>();
    final soundService = context.read<SoundService>();

    // Save API settings
    apiService.setApiUrl(_apiUrlController.text);
    
    // Save sound and vibration settings
    soundService.setSoundEnabled(_soundEnabled);
    soundService.setVibrationEnabled(_vibrationEnabled);
    await prefs.setDouble('sound_volume', _soundVolume);
    await prefs.setDouble('vibration_intensity', _vibrationIntensity);
    
    // Save TTS settings
    final ttsService = context.read<TtsService>();
    ttsService.setTtsEnabled(_ttsEnabled);
    ttsService.setSpeechRate(_speechRate);
    ttsService.setLanguage(_language == 'TR' ? 'tr-TR' : 'en-US');
    await prefs.setDouble('speech_rate', _speechRate);
    
    // Save camera settings
    await prefs.setInt('frame_rate', _frameRate);
    
    // Save theme settings
    await prefs.setBool('dark_mode', _isDarkMode);
    await prefs.setBool('high_contrast', _isHighContrast);
    await prefs.setString('language', _language);
    
    // Update theme immediately
    if (widget.onThemeChanged != null) {
      widget.onThemeChanged!(_isDarkMode, _isHighContrast);
    }
    
    // Save distance thresholds
    await prefs.setDouble('danger_threshold', _dangerThreshold);
    await prefs.setDouble('near_threshold', _nearThreshold);
    await prefs.setDouble('medium_threshold', _mediumThreshold);
    await prefs.setDouble('far_threshold', _farThreshold);

    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(_language == 'TR' ? 'Ayarlar kaydedildi' : 'Settings saved'),
        backgroundColor: Colors.green,
      ),
    );
  }
  
  Future<void> _resetSettings() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
    await _loadSettings();
    
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(_language == 'TR' ? 'Ayarlar sıfırlandı' : 'Settings reset'),
        backgroundColor: Colors.orange,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_language == 'TR' ? 'Ayarlar' : 'Settings'),
        actions: [
          IconButton(
            icon: const Icon(Icons.restore),
            tooltip: _language == 'TR' ? 'Sıfırla' : 'Reset',
            onPressed: () {
              showDialog(
                context: context,
                builder: (context) => AlertDialog(
                  title: Text(_language == 'TR' ? 'Ayarları Sıfırla' : 'Reset Settings'),
                  content: Text(_language == 'TR' 
                    ? 'Tüm ayarlar varsayılan değerlere döndürülecek. Emin misiniz?'
                    : 'All settings will be reset to defaults. Are you sure?'),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: Text(_language == 'TR' ? 'İptal' : 'Cancel'),
                    ),
                    TextButton(
                      onPressed: () {
                        Navigator.pop(context);
                        _resetSettings();
                      },
                      child: Text(_language == 'TR' ? 'Sıfırla' : 'Reset'),
                    ),
                  ],
                ),
              );
            },
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        children: [
          // Language Selection
          _buildSectionTitle(_language == 'TR' ? '🌐 Dil Seçimi' : '🌐 Language'),
          Card(
            child: ListTile(
              title: Text(_language == 'TR' ? 'Dil' : 'Language'),
              trailing: DropdownButton<String>(
                value: _language,
                items: [
                  DropdownMenuItem(value: 'TR', child: Text('🇹🇷 Türkçe')),
                  DropdownMenuItem(value: 'EN', child: Text('🇬🇧 English')),
                ].toList(),
                onChanged: (value) => setState(() => _language = value!),
              ),
            ),
          ),
          const SizedBox(height: 24),

          // Distance Thresholds
          _buildSectionTitle(_language == 'TR' ? '📏 Mesafe Eşikleri' : '📏 Distance Thresholds'),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  _buildSlider(
                    label: _language == 'TR' ? 'TEHLİKE' : 'DANGER',
                    value: _dangerThreshold,
                    min: 0.3,
                    max: 1.0,
                    divisions: 7,
                    color: AppColors.danger,
                    onChanged: (v) => setState(() => _dangerThreshold = v),
                  ),
                  _buildSlider(
                    label: _language == 'TR' ? 'YAKIN' : 'NEAR',
                    value: _nearThreshold,
                    min: 0.5,
                    max: 2.0,
                    divisions: 15,
                    color: AppColors.near,
                    onChanged: (v) => setState(() => _nearThreshold = v),
                  ),
                  _buildSlider(
                    label: _language == 'TR' ? 'ORTA' : 'MEDIUM',
                    value: _mediumThreshold,
                    min: 1.0,
                    max: 3.0,
                    divisions: 20,
                    color: AppColors.medium,
                    onChanged: (v) => setState(() => _mediumThreshold = v),
                  ),
                  _buildSlider(
                    label: _language == 'TR' ? 'UZAK' : 'FAR',
                    value: _farThreshold,
                    min: 2.0,
                    max: 5.0,
                    divisions: 30,
                    color: AppColors.far,
                    onChanged: (v) => setState(() => _farThreshold = v),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          // Sound & Vibration & TTS Settings
          _buildSectionTitle(_language == 'TR' ? '🔊 Ses, Titreşim ve Konuşma' : '🔊 Sound, Vibration & Speech'),
          Card(
            child: Column(
              children: [
                SwitchListTile(
                  title: Text(_language == 'TR' ? 'Sesli Uyarı' : 'Sound Alert'),
                  subtitle: Text(_language == 'TR' ? 'Tehlike durumunda ses çal' : 'Play sound on danger'),
                  value: _soundEnabled,
                  onChanged: (v) => setState(() => _soundEnabled = v),
                ),
                if (_soundEnabled)
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: _buildSlider(
                      label: _language == 'TR' ? 'Ses Seviyesi' : 'Sound Volume',
                      value: _soundVolume,
                      min: 0.0,
                      max: 1.0,
                      divisions: 10,
                      color: Colors.blue,
                      onChanged: (v) => setState(() => _soundVolume = v),
                    ),
                  ),
                const Divider(),
                SwitchListTile(
                  title: Text(_language == 'TR' ? 'Titreşim' : 'Vibration'),
                  subtitle: Text(_language == 'TR' ? 'Tehlike durumunda titreşim' : 'Vibrate on danger'),
                  value: _vibrationEnabled,
                  onChanged: (v) => setState(() => _vibrationEnabled = v),
                ),
                if (_vibrationEnabled)
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: _buildSlider(
                      label: _language == 'TR' ? 'Titreşim Yoğunluğu' : 'Vibration Intensity',
                      value: _vibrationIntensity,
                      min: 0.3,
                      max: 1.0,
                      divisions: 7,
                      color: Colors.purple,
                      onChanged: (v) => setState(() => _vibrationIntensity = v),
                    ),
                  ),
                const Divider(),
                SwitchListTile(
                  title: Text(_language == 'TR' ? '🗣️ Sesli Yönlendirme (TTS)' : '🗣️ Voice Guidance (TTS)'),
                  subtitle: Text(_language == 'TR' 
                    ? 'Mesafe bilgilerini sesli anlat' 
                    : 'Announce distance information verbally'),
                  value: _ttsEnabled,
                  onChanged: (v) => setState(() => _ttsEnabled = v),
                ),
                if (_ttsEnabled)
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: _buildSlider(
                      label: _language == 'TR' ? 'Konuşma Hızı' : 'Speech Rate',
                      value: _speechRate,
                      min: 0.3,
                      max: 1.0,
                      divisions: 14,
                      color: Colors.green,
                      onChanged: (v) => setState(() => _speechRate = v),
                    ),
                  ),
                if (_ttsEnabled)
                  Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Text(
                      _language == 'TR'
                        ? '💡 Örnek: "TEHLİKE! Çok yakın engel! 0.8 metre mesafede. Durun!"'
                        : '💡 Example: "DANGER! Very close obstacle! 0.8 meters away. Stop!"',
                      style: const TextStyle(
                        fontSize: 12,
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Theme Settings
          _buildSectionTitle(_language == 'TR' ? '🎨 Görünüm' : '🎨 Appearance'),
          Card(
            child: Column(
              children: [
                SwitchListTile(
                  title: Text(_language == 'TR' ? 'Karanlık Mod' : 'Dark Mode'),
                  subtitle: Text(_language == 'TR' ? 'Koyu tema kullan' : 'Use dark theme'),
                  value: _isDarkMode,
                  onChanged: (v) => setState(() => _isDarkMode = v),
                ),
                const Divider(),
                SwitchListTile(
                  title: Text(_language == 'TR' ? 'Yüksek Kontrast' : 'High Contrast'),
                  subtitle: Text(_language == 'TR' ? 'Daha belirgin renkler' : 'More distinct colors'),
                  value: _isHighContrast,
                  onChanged: (v) => setState(() => _isHighContrast = v),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Camera Settings
          _buildSectionTitle(_language == 'TR' ? '📷 Kamera' : '📷 Camera'),
          Card(
            child: Column(
              children: [
                ListTile(
                  title: Text(_language == 'TR' ? 'Frame Rate (Kare Hızı)' : 'Frame Rate'),
                  subtitle: Text(_language == 'TR' 
                    ? 'Saniyede $_frameRate analiz' 
                    : '$_frameRate analyses per second'),
                  trailing: DropdownButton<int>(
                    value: _frameRate,
                    items: [1, 2, 3, 5, 10].map((rate) {
                      return DropdownMenuItem(
                        value: rate,
                        child: Text('$rate FPS'),
                      );
                    }).toList(),
                    onChanged: (value) => setState(() => _frameRate = value!),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Text(
                    _language == 'TR'
                      ? '⚠️ Yüksek FPS daha fazla batarya ve işlemci kullanır'
                      : '⚠️ Higher FPS uses more battery and CPU',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.orange,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // API Settings
          _buildSectionTitle(_language == 'TR' ? '🌐 Sunucu Bağlantısı' : '🌐 Server Connection'),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: TextField(
                controller: _apiUrlController,
                decoration: InputDecoration(
                  labelText: 'API URL',
                  hintText: 'http://192.168.1.100:8000',
                  border: const OutlineInputBorder(),
                  prefixIcon: const Icon(Icons.link),
                ),
              ),
            ),
          ),
          const SizedBox(height: 32),

          // Save Button
          ElevatedButton.icon(
            onPressed: _saveSettings,
            icon: const Icon(Icons.save),
            label: Text(_language == 'TR' ? 'Kaydet' : 'Save'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.all(16),
              backgroundColor: Colors.green,
            ),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        title,
        style: const TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _buildSlider({
    required String label,
    required double value,
    required double min,
    required double max,
    required int divisions,
    required Color color,
    required ValueChanged<double> onChanged,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: const TextStyle(fontWeight: FontWeight.w500)),
            Text('${value.toStringAsFixed(2)}m', 
              style: TextStyle(color: color, fontWeight: FontWeight.bold)),
          ],
        ),
        Slider(
          value: value,
          min: min,
          max: max,
          divisions: divisions,
          activeColor: color,
          onChanged: onChanged,
        ),
      ],
    );
  }

  @override
  void dispose() {
    _apiUrlController.dispose();
    super.dispose();
  }
}
