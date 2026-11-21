// "Durumu söyle" bandının okuduğu kısa sahne özeti.
// Örnek: "Yol açık. Solda 2 insan, uzak."

import 'hazard_engine.dart';

class SceneObject {
  const SceneObject(this.nameTr, this.region, {this.proximityLabel});

  final String nameTr;
  final Region region;
  final String? proximityLabel;
}

String sceneSummary({
  required HazardResult hazard,
  required List<SceneObject> objects,
  required bool depthKnown,
  required bool detectorOk,
  DirectionStyle style = DirectionStyle.sides,
}) {
  final parts = <String>[];
  if (hazard.message.isNotEmpty) {
    parts.add(hazard.message);
  } else if (objects.isEmpty) {
    parts.add(switch ((detectorOk, depthKnown)) {
      (false, _) => 'Nesne tespiti çalışmıyor.',
      (true, true) => 'Yol açık.',
      (true, false) => 'Algılanan nesne yok.',
    });
  }

  for (final region in Region.values) {
    final inRegion = objects.where((o) => o.region == region).toList();
    if (inRegion.isEmpty) continue;
    final counts = <String, int>{};
    for (final o in inRegion) {
      counts[o.nameTr] = (counts[o.nameTr] ?? 0) + 1;
    }
    final names = counts.entries.map((e) => e.value > 1 ? '${e.value} ${e.key}' : e.key).join(', ');
    final labels = inRegion.map((o) => o.proximityLabel).whereType<String>().toSet();
    final distance = labels.length == 1 ? ', ${labels.first}' : '';
    parts.add('${capitalizeTr(directionWord(region, style))} $names$distance.');
  }
  return parts.join(' ');
}
