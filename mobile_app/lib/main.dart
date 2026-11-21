// Gören Göz: görme engelliler için sesli engel uyarısı ve Türkçe soru-cevap.

import 'package:flutter/services.dart';
import 'package:material_ui/material_ui.dart';
import 'package:permission_handler/permission_handler.dart';

import 'app.dart';
import 'perception/frame_source.dart';
import 'services/api_client.dart';
import 'services/feedback.dart';
import 'services/settings_store.dart';
import 'services/speech_input.dart';

class DevicePermissions implements PermissionGate {
  @override
  Future<bool> cameraGranted() => Permission.camera.isGranted;

  @override
  Future<bool> requestCamera() async => (await Permission.camera.request()).isGranted;

  @override
  Future<void> openSettings() async {
    await openAppSettings();
  }
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);

  final settings = await SettingsStore.load();
  final speaker = TtsSpeaker();
  await speaker.configure(rate: settings.speechRate, volume: settings.volume);
  ApiClient? client;

  runApp(
    GorenGozApp(
      services: AppServices(
        settings: settings,
        speaker: speaker,
        haptics: DeviceHaptics(enabled: () => settings.vibration),
        sounds: AssetSounds(),
        speechInput: DeviceSpeechInput(),
        permissions: DevicePermissions(),
        frameSourceFactory: CameraFrameSource.new,
        apiFactory: (s) {
          if (!s.hasServer) return null;
          client ??= ApiClient(baseUrl: s.serverUrl, apiKey: s.apiKey);
          return client!..configure(baseUrl: s.serverUrl, apiKey: s.apiKey);
        },
      ),
    ),
  );
}
