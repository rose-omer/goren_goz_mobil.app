// Uygulama kökü ve bağımlılık kabı. Testler sahte servislerle [AppServices] kurar.

import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';

import 'core/speech_queue.dart';
import 'perception/frame_source.dart';
import 'screens/onboarding_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/walk_screen.dart';
import 'services/api_client.dart';
import 'services/feedback.dart';
import 'services/settings_store.dart';
import 'services/speech_input.dart';
import 'theme/app_theme.dart';

abstract interface class PermissionGate {
  Future<bool> cameraGranted();
  Future<bool> requestCamera();
  Future<void> openSettings();
}

class AppServices {
  AppServices({
    required this.settings,
    required this.speaker,
    required this.haptics,
    required this.sounds,
    required this.speechInput,
    required this.permissions,
    required this.frameSourceFactory,
    required this.apiFactory,
  }) : speech = SpeechQueue(speaker);

  final SettingsStore settings;
  final Speaker speaker;
  final SpeechQueue speech;
  final Haptics haptics;
  final Sounds sounds;
  final SpeechInput speechInput;
  final PermissionGate permissions;
  final FrameSource Function() frameSourceFactory;

  /// Sunucu adresi yoksa `null` döner.
  final AnalysisApi? Function(SettingsStore settings) apiFactory;
}

abstract final class Routes {
  static const onboarding = '/hosgeldin';
  static const walk = '/yuruyus';
  static const settings = '/ayarlar';
}

class GorenGozApp extends StatelessWidget {
  const GorenGozApp({super.key, required this.services});

  final AppServices services;

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider<AppServices>.value(value: services),
        ChangeNotifierProvider<SettingsStore>.value(value: services.settings),
      ],
      child: Selector<SettingsStore, Contrast>(
        selector: (_, s) => s.contrast,
        builder: (context, contrast, _) => MaterialApp(
          title: 'Gören Göz',
          debugShowCheckedModeBanner: false,
          theme: buildTheme(contrast),
          // Flutter 3.38+: dil ekran okuyucu sesini de belirler (plan 5.3).
          locale: const Locale('tr', 'TR'),
          supportedLocales: const [Locale('tr', 'TR')],
          localizationsDelegates: GlobalMaterialLocalizations.delegates,
          initialRoute: services.settings.onboarded ? Routes.walk : Routes.onboarding,
          routes: {
            Routes.onboarding: (_) => const OnboardingScreen(),
            Routes.walk: (_) => const WalkScreen(),
            Routes.settings: (_) => const SettingsScreen(),
          },
        ),
      ),
    );
  }
}
