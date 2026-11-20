// Tasarım tokenleri ve tema (plan 5.1).
// Ana tema: siyah zemin, sarı #FFD600 metin ve kenar (≈ 14:1). İkinci tema: beyaz zemin, siyah metin.
// Renk tek başına anlam taşımaz; her seviye metin, ses ve titreşimle de verilir.

import 'package:material_ui/material_ui.dart';

import '../core/hazard_engine.dart';
import '../services/settings_store.dart';

@immutable
class Palette extends ThemeExtension<Palette> {
  const Palette({
    required this.ground,
    required this.ink,
    required this.inkMuted,
    required this.edge,
    required this.pressed,
    required this.danger,
    required this.onDanger,
    required this.near,
    required this.onNear,
    required this.focus,
  });

  /// Siyah-sarı. Kontrast: sarı/siyah 14.6:1, krem/siyah 17:1, mercan/siyah 7.6:1.
  static const signal = Palette(
    ground: Color(0xFF000000),
    ink: Color(0xFFFFD600),
    inkMuted: Color(0xFFF3ECCB),
    edge: Color(0xFFFFD600),
    pressed: Color(0xFF2E2700),
    danger: Color(0xFFFF7A66),
    onDanger: Color(0xFF000000),
    near: Color(0xFFFFD600),
    onNear: Color(0xFF000000),
    focus: Color(0xFFFFFFFF),
  );

  /// Beyaz-siyah. Kontrast: siyah/beyaz 21:1, gri/beyaz 9.7:1, beyaz/koyu kırmızı 7.3:1.
  static const paper = Palette(
    ground: Color(0xFFFFFFFF),
    ink: Color(0xFF000000),
    inkMuted: Color(0xFF3D3A30),
    edge: Color(0xFF000000),
    pressed: Color(0xFFFFF3B0),
    danger: Color(0xFFA51C12),
    onDanger: Color(0xFFFFFFFF),
    near: Color(0xFFFFD600),
    onNear: Color(0xFF000000),
    focus: Color(0xFF0050C8),
  );

  final Color ground;
  final Color ink;
  final Color inkMuted;
  final Color edge;
  final Color pressed;
  final Color danger;
  final Color onDanger;
  final Color near;
  final Color onNear;
  final Color focus;

  static Palette of(BuildContext context) => Theme.of(context).extension<Palette>()!;

  /// Durum şeridinin dolgu ve yazı rengi. Bilgi ve temiz yol dolgusuzdur.
  (Color background, Color foreground) forLevel(AlertLevel level) => switch (level) {
    AlertLevel.danger => (danger, onDanger),
    AlertLevel.near => (near, onNear),
    _ => (ground, ink),
  };

  @override
  Palette copyWith() => this;

  @override
  Palette lerp(Palette? other, double t) => t < 0.5 ? this : (other ?? this);
}

/// Tip ölçeği (sp). Sistem yazı ölçeğine uyar; gövde en az 24, düğme etiketi en az 28.
abstract final class TypeScale {
  static const band = 30.0;
  static const status = 26.0;
  static const title = 28.0;
  static const body = 24.0;
  static const small = 20.0;

  /// Tam bant etiketinin sığdırmada inebileceği en küçük görünen boy.
  static const buttonMin = 28.0;
}

abstract final class Space {
  static const xs = 4.0;
  static const s = 8.0;
  static const m = 16.0;
  static const l = 24.0;
  static const xl = 32.0;
}

abstract final class Shape {
  static const radius = 12.0;
  static const edge = 2.0;
  static const focusEdge = 4.0;
}

ThemeData buildTheme(Contrast contrast) {
  final p = contrast == Contrast.darkSignal ? Palette.signal : Palette.paper;
  final brightness = contrast == Contrast.darkSignal ? Brightness.dark : Brightness.light;
  final scheme = ColorScheme(
    brightness: brightness,
    primary: p.ink,
    onPrimary: p.ground,
    secondary: p.ink,
    onSecondary: p.ground,
    error: p.danger,
    onError: p.onDanger,
    surface: p.ground,
    onSurface: p.ink,
    onSurfaceVariant: p.inkMuted,
    outline: p.edge,
  );
  final text = TextTheme(
    headlineSmall: TextStyle(fontSize: TypeScale.title, fontWeight: FontWeight.w700, color: p.ink, height: 1.2),
    titleLarge: TextStyle(fontSize: TypeScale.band, fontWeight: FontWeight.w700, color: p.ink, height: 1.15),
    titleMedium: TextStyle(fontSize: TypeScale.body, fontWeight: FontWeight.w600, color: p.ink, height: 1.3),
    bodyLarge: TextStyle(fontSize: TypeScale.body, color: p.inkMuted, height: 1.4),
    bodyMedium: TextStyle(fontSize: TypeScale.body, color: p.inkMuted, height: 1.4),
    bodySmall: TextStyle(fontSize: TypeScale.small, color: p.inkMuted, height: 1.35),
    labelLarge: const TextStyle(fontSize: TypeScale.band, fontWeight: FontWeight.w700, height: 1.1),
  );
  final edge = BorderSide(color: p.edge, width: Shape.edge);
  final rounded = RoundedRectangleBorder(borderRadius: BorderRadius.circular(Shape.radius));

  return ThemeData(
    useMaterial3: true,
    brightness: brightness,
    colorScheme: scheme,
    scaffoldBackgroundColor: p.ground,
    textTheme: text,
    extensions: [p],
    focusColor: p.pressed,
    splashFactory: NoSplash.splashFactory,
    highlightColor: p.pressed,
    materialTapTargetSize: MaterialTapTargetSize.padded,
    visualDensity: VisualDensity.standard,
    appBarTheme: AppBarTheme(
      backgroundColor: p.ground,
      foregroundColor: p.ink,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
      titleTextStyle: text.headlineSmall,
      toolbarHeight: 72,
    ),
    dividerTheme: DividerThemeData(color: p.edge.withValues(alpha: 0.45), thickness: 1, space: Space.l),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: p.ink,
        foregroundColor: p.ground,
        minimumSize: const Size.fromHeight(72),
        textStyle: const TextStyle(fontSize: TypeScale.band, fontWeight: FontWeight.w700),
        shape: rounded,
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: p.ink,
        side: edge,
        minimumSize: const Size.fromHeight(64),
        textStyle: const TextStyle(fontSize: TypeScale.body, fontWeight: FontWeight.w600),
        shape: rounded,
      ),
    ),
    switchTheme: SwitchThemeData(
      thumbColor: WidgetStateProperty.resolveWith((s) => s.contains(WidgetState.selected) ? p.ground : p.ink),
      trackColor: WidgetStateProperty.resolveWith((s) => s.contains(WidgetState.selected) ? p.ink : p.ground),
      trackOutlineColor: WidgetStatePropertyAll(p.edge),
    ),
    radioTheme: RadioThemeData(fillColor: WidgetStatePropertyAll(p.ink)),
    sliderTheme: SliderThemeData(
      activeTrackColor: p.ink,
      inactiveTrackColor: p.edge.withValues(alpha: 0.35),
      thumbColor: p.ink,
      overlayColor: p.pressed,
      trackHeight: 6,
      valueIndicatorTextStyle: TextStyle(color: p.ground, fontSize: TypeScale.small),
    ),
    inputDecorationTheme: InputDecorationTheme(
      labelStyle: TextStyle(color: p.ink, fontSize: TypeScale.body),
      helperStyle: TextStyle(color: p.inkMuted, fontSize: TypeScale.small),
      helperMaxLines: 3,
      errorStyle: TextStyle(color: p.danger, fontSize: TypeScale.small, fontWeight: FontWeight.w600),
      errorMaxLines: 3,
      contentPadding: const EdgeInsets.all(Space.m),
      enabledBorder: OutlineInputBorder(borderSide: edge, borderRadius: BorderRadius.circular(Shape.radius)),
      focusedBorder: OutlineInputBorder(
        borderSide: BorderSide(color: p.focus, width: Shape.focusEdge),
        borderRadius: BorderRadius.circular(Shape.radius),
      ),
      errorBorder: OutlineInputBorder(
        borderSide: BorderSide(color: p.danger, width: Shape.edge),
        borderRadius: BorderRadius.circular(Shape.radius),
      ),
      focusedErrorBorder: OutlineInputBorder(
        borderSide: BorderSide(color: p.danger, width: Shape.focusEdge),
        borderRadius: BorderRadius.circular(Shape.radius),
      ),
    ),
    textSelectionTheme: TextSelectionThemeData(
      cursorColor: p.ink,
      selectionColor: p.ink.withValues(alpha: 0.35),
      selectionHandleColor: p.ink,
    ),
    // Hareket yok: sayfa geçişi anında (plan 5.1).
    pageTransitionsTheme: const PageTransitionsTheme(
      builders: {TargetPlatform.android: _InstantTransitions(), TargetPlatform.iOS: _InstantTransitions()},
    ),
  );
}

class _InstantTransitions extends PageTransitionsBuilder {
  const _InstantTransitions();

  @override
  Widget buildTransitions<T>(
    PageRoute<T> route,
    BuildContext context,
    Animation<double> animation,
    Animation<double> secondaryAnimation,
    Widget child,
  ) => child;
}
