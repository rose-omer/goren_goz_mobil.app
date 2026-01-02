///
/// Gören Göz Mobil - Main App Entry Point
/// ========================================
///

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'screens/splash_screen.dart';
import 'screens/camera_screen.dart';
import 'screens/settings_screen.dart';
import 'services/api_service.dart';
import 'services/sound_service.dart';
import 'services/tts_service.dart';
import 'utils/constants.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Lock orientation to portrait
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
  ]);
  
  // Set system UI overlay style
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
    ),
  );
  
  runApp(const GorenGozApp());
}

class GorenGozApp extends StatefulWidget {
  const GorenGozApp({super.key});

  @override
  State<GorenGozApp> createState() => _GorenGozAppState();
}

class _GorenGozAppState extends State<GorenGozApp> {
  ThemeMode _themeMode = ThemeMode.dark;
  bool _highContrast = false;

  @override
  void initState() {
    super.initState();
    _loadThemeSettings();
  }

  Future<void> _loadThemeSettings() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      final isDark = prefs.getBool('dark_mode') ?? true;
      _themeMode = isDark ? ThemeMode.dark : ThemeMode.light;
      _highContrast = prefs.getBool('high_contrast') ?? false;
    });
  }

  void updateTheme(bool isDark, bool highContrast) {
    setState(() {
      _themeMode = isDark ? ThemeMode.dark : ThemeMode.light;
      _highContrast = highContrast;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => ApiService()),
        Provider(create: (_) => SoundService()),
        Provider(create: (_) => TtsService()),
      ],
      child: MaterialApp(
        title: 'Gören Göz Mobil',
        debugShowCheckedModeBanner: false,
        themeMode: _themeMode,
        theme: _buildLightTheme(),
        darkTheme: _buildDarkTheme(),
        initialRoute: '/',
        routes: {
          '/': (context) => const SplashScreen(),
          '/camera': (context) => const CameraScreen(),
          '/settings': (context) => SettingsScreen(onThemeChanged: updateTheme),
        },
      ),
    );
  }

  ThemeData _buildLightTheme() {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      colorScheme: ColorScheme.fromSeed(
        seedColor: AppColors.primary,
        brightness: Brightness.light,
      ).copyWith(
        primary: _highContrast ? Colors.black : AppColors.primary,
        surface: _highContrast ? Colors.white : const Color(0xFFF5F5F5),
      ),
      textTheme: GoogleFonts.robotoTextTheme().apply(
        bodyColor: _highContrast ? Colors.black : Colors.black87,
        displayColor: _highContrast ? Colors.black : Colors.black87,
      ),
      scaffoldBackgroundColor: _highContrast ? Colors.white : const Color(0xFFF5F5F5),
      appBarTheme: AppBarTheme(
        backgroundColor: _highContrast ? Colors.white : const Color(0xFFF5F5F5),
        foregroundColor: _highContrast ? Colors.black : Colors.black87,
        elevation: 0,
      ),
      cardTheme: CardThemeData(
        color: _highContrast ? Colors.white : Colors.white,
        elevation: _highContrast ? 4 : 1,
      ),
    );
  }

  ThemeData _buildDarkTheme() {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: ColorScheme.fromSeed(
        seedColor: AppColors.primary,
        brightness: Brightness.dark,
      ).copyWith(
        primary: _highContrast ? Colors.white : AppColors.primary,
        surface: _highContrast ? Colors.black : const Color(0xFF1E1E1E),
      ),
      textTheme: GoogleFonts.robotoTextTheme().apply(
        bodyColor: _highContrast ? Colors.white : Colors.white70,
        displayColor: _highContrast ? Colors.white : Colors.white,
      ),
      scaffoldBackgroundColor: _highContrast ? Colors.black : Colors.black,
      appBarTheme: AppBarTheme(
        backgroundColor: _highContrast ? Colors.black : Colors.black,
        foregroundColor: _highContrast ? Colors.white : Colors.white,
        elevation: 0,
      ),
      cardTheme: CardThemeData(
        color: _highContrast ? Colors.black : const Color(0xFF2C2C2C),
        elevation: _highContrast ? 4 : 1,
      ),
    );
  }
}
