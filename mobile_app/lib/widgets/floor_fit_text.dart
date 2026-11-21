// Sığmayan metni küçültür ama görünen boyu tabanın altına indirmez (plan 5.1: gövde ≥ 24 sp,
// düğme ≥ 28 sp). Eski FittedBox(scaleDown) sınırsız küçültüyordu.
//
// Sıra: tam boy → küçült (tabana kadar) → ek satırı at → tabanda satır sınırı ve üç nokta.
// Tam metin her zaman üstteki Semantics etiketinde kalır; ekran okuyucu kısalmayı duymaz.

import 'package:material_ui/material_ui.dart';

import '../theme/app_theme.dart';

class FloorFitText extends StatelessWidget {
  const FloorFitText(
    this.text, {
    super.key,
    required this.style,
    required this.minSize,
    this.secondary,
    this.secondaryStyle,
    this.align = TextAlign.start,
  });

  final String text;

  /// `fontSize` zorunlu: küçültme bu boydan yapılır.
  final TextStyle style;

  /// Ekranda görünen en küçük boy (yazı ölçeği uygulanmış, mantıksal piksel).
  final double minSize;

  /// Alt satır (ör. "Dinliyorum"). Küçültülmez; yer yoksa gösterilmez.
  final String? secondary;
  final TextStyle? secondaryStyle;
  final TextAlign align;

  static const _step = 0.05;
  static const _gap = Space.xs;

  @override
  Widget build(BuildContext context) {
    final scaler = MediaQuery.textScalerOf(context);
    final direction = Directionality.of(context);
    // Ölçüm, Text'in kullanacağı stille (tema yazı tipi dahil) yapılmalı.
    final inherited = DefaultTextStyle.of(context).style;
    final style = inherited.merge(this.style);
    final secondaryStyle = inherited.merge(this.secondaryStyle ?? this.style);
    final base = style.fontSize!;

    return LayoutBuilder(
      builder: (context, constraints) {
        double measure(String value, TextStyle s) {
          final painter = TextPainter(
            text: TextSpan(text: value, style: s),
            textDirection: direction,
            textScaler: scaler,
          )..layout(maxWidth: constraints.maxWidth);
          final height = painter.height;
          painter.dispose();
          return height;
        }

        final effectiveBase = scaler.scale(base);
        final floor = effectiveBase <= minSize ? 1.0 : minSize / effectiveBase;
        final secondaryHeight = secondary == null ? 0.0 : _gap + measure(secondary!, secondaryStyle);

        double? fit(double extra) {
          if (!constraints.maxHeight.isFinite) return 1;
          for (var s = 1.0; s >= floor - 1e-9; s -= _step) {
            if (measure(text, style.copyWith(fontSize: base * s)) + extra <= constraints.maxHeight) return s;
          }
          if (measure(text, style.copyWith(fontSize: base * floor)) + extra <= constraints.maxHeight) return floor;
          return null;
        }

        var showSecondary = secondary != null;
        var scale = showSecondary ? fit(secondaryHeight) : fit(0);
        if (scale == null && showSecondary) {
          showSecondary = false;
          scale = fit(0);
        }
        int? maxLines;
        if (scale == null) {
          scale = floor;
          final line = measure('A', style.copyWith(fontSize: base * floor));
          maxLines = (constraints.maxHeight / line).floor().clamp(1, 1 << 16);
        }

        final crossAxis = align == TextAlign.center ? CrossAxisAlignment.center : CrossAxisAlignment.start;
        final column = Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: crossAxis,
          children: [
            Text(
              text,
              textAlign: align,
              maxLines: maxLines,
              overflow: maxLines == null ? null : TextOverflow.ellipsis,
              style: style.copyWith(fontSize: base * scale),
            ),
            if (showSecondary) ...[
              const SizedBox(height: _gap),
              Text(secondary!, textAlign: align, style: secondaryStyle),
            ],
          ],
        );
        final alignment = align == TextAlign.center ? Alignment.center : Alignment.centerLeft;
        if (!constraints.maxHeight.isFinite) return Align(alignment: alignment, heightFactor: 1, child: column);
        // Tek satır bile sığmıyorsa taşma hatası yerine kırp.
        return ClipRect(
          child: OverflowBox(alignment: alignment, minHeight: 0, maxHeight: double.infinity, child: column),
        );
      },
    );
  }
}
