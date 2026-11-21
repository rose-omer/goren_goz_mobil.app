// Üst durum şeridi. Seviye metinle ("Dur", "Dikkat") ve şekille verilir; renk tek başına anlam taşımaz.
// liveRegion: seviye değişince ekran okuyucu okur (plan 5.2).

import 'package:material_ui/material_ui.dart';

import '../core/hazard_engine.dart';
import '../theme/app_theme.dart';
import 'floor_fit_text.dart';

class StatusStrip extends StatelessWidget {
  const StatusStrip({super.key, required this.level, required this.text, required this.liveMessage});

  final AlertLevel level;
  final String text;
  final String liveMessage;

  @override
  Widget build(BuildContext context) {
    final p = Palette.of(context);
    final (background, foreground) = p.forLevel(level);
    final outlined = level == AlertLevel.clear || level == AlertLevel.info;

    return Semantics(
      liveRegion: true,
      container: true,
      label: liveMessage,
      excludeSemantics: true,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: Space.l, vertical: Space.m),
        decoration: BoxDecoration(
          color: background,
          borderRadius: BorderRadius.circular(Shape.radius),
          border: outlined ? Border.all(color: p.edge.withValues(alpha: 0.5), width: 1) : null,
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            _LevelMark(level: level, color: foreground),
            const SizedBox(width: Space.m),
            Expanded(
              // Gövde boyu 24 sp altına inmez (plan 5.1); tam metin liveRegion etiketinde.
              child: FloorFitText(
                text,
                minSize: TypeScale.body,
                style: TextStyle(
                  fontSize: TypeScale.status,
                  fontWeight: FontWeight.w600,
                  color: foreground,
                  height: 1.25,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Seviyeye göre farklı biçim: el (Dur), üçgen (Dikkat), bilgi ve halka (diğer).
class _LevelMark extends StatelessWidget {
  const _LevelMark({required this.level, required this.color});

  final AlertLevel level;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final icon = switch (level) {
      AlertLevel.danger => Icons.pan_tool,
      AlertLevel.near => Icons.warning_rounded,
      AlertLevel.info => Icons.info_outline,
      AlertLevel.clear => Icons.radio_button_unchecked,
    };
    return Icon(icon, size: 36, color: color);
  }
}
