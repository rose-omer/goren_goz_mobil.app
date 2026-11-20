// Yardımcı görünümü katmanı: kutular, Türkçe etiket, bölge çizgileri (plan 5.2.5).
// Yalnız gören yardımcı ve jüri içindir; ekran okuyucu bu katmanı okumaz.

import 'package:material_ui/material_ui.dart';

import '../services/api_client.dart';
import '../theme/app_theme.dart';

class DetectionOverlay extends StatelessWidget {
  const DetectionOverlay({super.key, required this.analysis});

  final FrameAnalysis? analysis;

  @override
  Widget build(BuildContext context) {
    final p = Palette.of(context);
    return ExcludeSemantics(
      child: CustomPaint(
        painter: _OverlayPainter(analysis, edge: p.near, label: p.onNear, danger: p.danger),
        size: Size.infinite,
      ),
    );
  }
}

class _OverlayPainter extends CustomPainter {
  _OverlayPainter(this.analysis, {required this.edge, required this.label, required this.danger});

  final FrameAnalysis? analysis;
  final Color edge;
  final Color label;
  final Color danger;

  @override
  void paint(Canvas canvas, Size size) {
    final guide = Paint()
      ..color = edge.withValues(alpha: 0.35)
      ..strokeWidth = 1;
    for (final x in [size.width / 3, size.width * 2 / 3]) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), guide);
    }

    final data = analysis;
    if (data == null || data.imageWidth == 0) return;
    // Önizleme kareyi "cover" ile doldurur; ölçek kısa kenara göre.
    final scale = size.width / data.imageWidth > size.height / data.imageHeight
        ? size.width / data.imageWidth
        : size.height / data.imageHeight;
    final dx = (size.width - data.imageWidth * scale) / 2;
    final dy = (size.height - data.imageHeight * scale) / 2;

    for (final o in data.objects) {
      final rect = Rect.fromLTRB(
        dx + o.bbox[0] * scale,
        dy + o.bbox[1] * scale,
        dx + o.bbox[2] * scale,
        dy + o.bbox[3] * scale,
      );
      final color = o.isApproaching ? danger : edge;
      canvas.drawRect(
        rect,
        Paint()
          ..color = color
          ..style = PaintingStyle.stroke
          ..strokeWidth = 3,
      );
      final parts = [
        o.nameTr,
        if (o.distanceM != null) '${o.distanceM!.toStringAsFixed(1)} m',
        if (o.ttcS != null) 'TTC ${o.ttcS!.toStringAsFixed(1)} s',
      ];
      final painter = TextPainter(
        text: TextSpan(
          text: parts.join(', '),
          style: TextStyle(color: label, fontSize: TypeScale.small, fontWeight: FontWeight.w700),
        ),
        textDirection: TextDirection.ltr,
      )..layout(maxWidth: size.width);
      final top = (rect.top - painter.height - 4).clamp(0.0, size.height - painter.height);
      final tag = Rect.fromLTWH(rect.left, top, painter.width + 12, painter.height + 4);
      canvas.drawRect(tag, Paint()..color = color);
      painter.paint(canvas, Offset(tag.left + 6, tag.top + 2));
    }
  }

  @override
  bool shouldRepaint(_OverlayPainter old) => old.analysis != analysis || old.edge != edge;
}
