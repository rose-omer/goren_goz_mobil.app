// Uyarı motoru: seviye kuralı, histerezis ve Türkçe mesaj.
// Backend'deki `services/alert_service.py` ile aynı kural (plan 4.4).

/// Uyarı seviyesi. Sıra önemli: sonraki = daha ciddi.
enum AlertLevel {
  clear('Yol açık'),
  info('Bilgi'),
  near('Dikkat'),
  danger('Dur');

  const AlertLevel(this.label);

  /// Ekranda ve ekran okuyucuda kullanılan kısa ad.
  final String label;

  bool operator >(AlertLevel other) => index > other.index;
  bool operator <(AlertLevel other) => index < other.index;

  static AlertLevel max(AlertLevel a, AlertLevel b) => a > b ? a : b;
  static AlertLevel min(AlertLevel a, AlertLevel b) => a < b ? a : b;

  /// Sunucu yanıtındaki adı çevirir. Bilinmeyen ad [info] sayılır.
  static AlertLevel parse(String? name) => switch (name) {
    'CLEAR' => AlertLevel.clear,
    'NEAR' => AlertLevel.near,
    'DANGER' => AlertLevel.danger,
    _ => AlertLevel.info,
  };
}

enum Region { left, center, right }

/// Yön anlatımı: "solda / önde / sağda" ya da saat yönü.
enum DirectionStyle { sides, clock }

String directionWord(Region region, DirectionStyle style) => switch ((style, region)) {
  (DirectionStyle.sides, Region.left) => 'solda',
  (DirectionStyle.sides, Region.center) => 'önde',
  (DirectionStyle.sides, Region.right) => 'sağda',
  (DirectionStyle.clock, Region.left) => 'saat 10 yönünde',
  (DirectionStyle.clock, Region.center) => 'saat 12 yönünde',
  (DirectionStyle.clock, Region.right) => 'saat 2 yönünde',
};

/// Türkçe ilk harf büyütme: "insan" -> "İnsan".
String capitalizeTr(String text) {
  if (text.isEmpty) return text;
  final first = switch (text[0]) {
    'i' => 'İ',
    'ı' => 'I',
    final c => c.toUpperCase(),
  };
  return first + text.substring(1);
}

class PerceivedObject {
  const PerceivedObject({
    required this.nameTr,
    required this.region,
    required this.priority,
    this.trackId,
    this.ttcS,
    this.distanceM,
  });

  final String nameTr;
  final Region region;
  final int priority;
  final String? trackId;
  final double? ttcS;
  final double? distanceM;

  /// Konuşma tekrarını engellemek için nesne-yön anahtarı.
  String get speechKey => '$nameTr/${region.name}';
}

class RegionReading {
  const RegionReading({required this.proximity, required this.label, this.closeArea = 0});

  /// 0 uzak, 1 yakın. Göreli; metre değildir.
  final double proximity;
  final double closeArea;
  final String label;
}

class HazardConfig {
  const HazardConfig({
    this.dangerTtcS = 2.0,
    this.nearTtcS = 4.0,
    this.dangerDistanceM = 1.0,
    this.nearDistanceM = 2.0,
    this.proximityDanger = 0.85,
    this.proximityAreaThreshold = 0.10,
    this.raiseAfterFrames = 2,
    this.lowerAfterFrames = 5,
  });

  final double dangerTtcS;
  final double nearTtcS;
  final double dangerDistanceM;
  final double nearDistanceM;
  final double proximityDanger;
  final double proximityAreaThreshold;
  final int raiseAfterFrames;
  final int lowerAfterFrames;
}

/// Tek nesnenin seviyesi. DANGER yalnız orta bölgede.
AlertLevel objectLevel(PerceivedObject obj, HazardConfig config) {
  final ttc = obj.ttcS;
  final dist = obj.distanceM;
  final danger = (ttc != null && ttc < config.dangerTtcS) || (dist != null && dist < config.dangerDistanceM);
  final near = (ttc != null && ttc < config.nearTtcS) || (dist != null && dist < config.nearDistanceM);
  if (danger && obj.region == Region.center) return AlertLevel.danger;
  if (danger || near) return AlertLevel.near;
  return AlertLevel.info;
}

class Assessment {
  const Assessment(this.level, this.top, {required this.depthClose});

  final AlertLevel level;
  final PerceivedObject? top;
  final bool depthClose;
}

Assessment assess(List<PerceivedObject> objects, Map<Region, RegionReading>? regions, HazardConfig config) {
  var level = AlertLevel.clear;
  PerceivedObject? top;
  for (final obj in objects) {
    final objLevel = objectLevel(obj, config);
    if (top == null || objLevel > level || (objLevel == level && obj.priority > top.priority)) {
      level = AlertLevel.max(level, objLevel);
      top = obj;
    }
  }
  final center = regions?[Region.center];
  final depthClose = center != null && center.closeArea >= config.proximityAreaThreshold;
  if (depthClose && level < AlertLevel.near) level = AlertLevel.near;
  return Assessment(level, top, depthClose: depthClose);
}

/// Önce eylem, sonra nesne, sonra yön: "Dur. İnsan, önde.".
String buildMessage(
  AlertLevel level,
  PerceivedObject? top, {
  required bool depthKnown,
  required bool depthClose,
  required bool detectorOk,
  DirectionStyle style = DirectionStyle.sides,
}) {
  if (top != null) {
    var subject = '${capitalizeTr(top.nameTr)}, ${directionWord(top.region, style)}';
    final distance = top.distanceM;
    if (distance != null) subject += ', ${spokenMeters(distance)}';
    return switch (level) {
      AlertLevel.danger => 'Dur. $subject.',
      AlertLevel.near => 'Dikkat. $subject.',
      _ => '$subject.',
    };
  }
  if (depthClose) return 'Dikkat. Önde engel.';
  // "Yol açık" yalnız tespit ve derinlik ikisi de temizse (plan 9). Biri yoksa sus: yanlış güven riski.
  if (detectorOk && depthKnown && level == AlertLevel.clear) return 'Yol açık.';
  return '';
}

String spokenMeters(double meters) {
  final rounded = meters.round();
  return rounded < 1 ? '1 metreden az' : '$rounded metre';
}

/// Seviye [raiseAfter] ardışık karede görülmeden yükselmez, [lowerAfter] karede düşmez.
class LevelHysteresis {
  LevelHysteresis({this.raiseAfter = 2, this.lowerAfter = 5});

  final int raiseAfter;
  final int lowerAfter;
  AlertLevel level = AlertLevel.clear;
  int _up = 0;
  int _down = 0;
  AlertLevel _upMin = AlertLevel.danger;
  AlertLevel _downMax = AlertLevel.clear;

  AlertLevel update(AlertLevel raw) {
    if (raw > level) {
      _down = 0;
      _up += 1;
      _upMin = _up > 1 ? AlertLevel.min(_upMin, raw) : raw;
      if (_up >= raiseAfter) {
        level = _upMin;
        _up = 0;
      }
    } else if (raw < level) {
      _up = 0;
      _down += 1;
      _downMax = _down > 1 ? AlertLevel.max(_downMax, raw) : raw;
      if (_down >= lowerAfter) {
        level = _downMax;
        _down = 0;
      }
    } else {
      _up = 0;
      _down = 0;
    }
    return level;
  }

  void reset() {
    level = AlertLevel.clear;
    _up = 0;
    _down = 0;
  }
}

class HazardResult {
  const HazardResult({required this.level, required this.rawLevel, required this.message, required this.top});

  static const idle = HazardResult(level: AlertLevel.clear, rawLevel: AlertLevel.clear, message: '', top: null);

  final AlertLevel level;
  final AlertLevel rawLevel;
  final String message;
  final PerceivedObject? top;
}

/// Kare başına çağrılır; durumu (histerezis) tutar.
class HazardEngine {
  HazardEngine({this.config = const HazardConfig()})
    : _hysteresis = LevelHysteresis(raiseAfter: config.raiseAfterFrames, lowerAfter: config.lowerAfterFrames);

  final HazardConfig config;
  final LevelHysteresis _hysteresis;

  HazardResult process(
    List<PerceivedObject> objects,
    Map<Region, RegionReading>? regions, {
    required bool detectorOk,
    DirectionStyle style = DirectionStyle.sides,
  }) {
    final raw = assess(objects, regions, config);
    final stable = _hysteresis.update(raw.level);
    final message = buildMessage(
      stable,
      raw.top,
      depthKnown: regions != null,
      depthClose: raw.depthClose,
      detectorOk: detectorOk,
      style: style,
    );
    return HazardResult(level: stable, rawLevel: raw.level, message: message, top: raw.top);
  }

  void reset() => _hysteresis.reset();
}
