import 'package:flutter_test/flutter_test.dart';
import 'package:goren_goz_mobil/core/hazard_engine.dart';

PerceivedObject obj({
  Region region = Region.center,
  double? ttc,
  double? dist,
  String name = 'insan',
  int priority = 10,
}) => PerceivedObject(nameTr: name, region: region, priority: priority, ttcS: ttc, distanceM: dist);

const config = HazardConfig();
const clearRegions = {
  Region.left: RegionReading(proximity: 0.2, label: 'uzak'),
  Region.center: RegionReading(proximity: 0.2, label: 'uzak'),
  Region.right: RegionReading(proximity: 0.2, label: 'uzak'),
};

void main() {
  group('objectLevel', () {
    final cases = <String, (PerceivedObject, AlertLevel)>{
      'TTC < 2 s, orta': (obj(ttc: 1.5), AlertLevel.danger),
      'mesafe < 1 m, orta': (obj(dist: 0.8), AlertLevel.danger),
      'yanda tehlike NEAR olur': (obj(region: Region.left, ttc: 1.5), AlertLevel.near),
      'TTC < 4 s': (obj(ttc: 3), AlertLevel.near),
      'mesafe < 2 m': (obj(dist: 1.5), AlertLevel.near),
      'uzak': (obj(ttc: 8, dist: 5), AlertLevel.info),
      'sinyal yok': (obj(), AlertLevel.info),
    };
    cases.forEach((name, c) {
      test(name, () => expect(objectLevel(c.$1, config), c.$2));
    });
  });

  test('mesaj önce eylem, sonra nesne, sonra yön', () {
    final danger = assess([obj(ttc: 1)], null, config);
    expect(
      buildMessage(danger.level, danger.top, depthKnown: false, depthClose: false, detectorOk: true),
      'Dur. İnsan, önde.',
    );

    final near = assess([obj(region: Region.right, ttc: 3, name: 'direk')], null, config);
    expect(
      buildMessage(near.level, near.top, depthKnown: false, depthClose: false, detectorOk: true),
      'Dikkat. Direk, sağda.',
    );

    final withDistance = assess([obj(dist: 1.9)], null, config);
    expect(
      buildMessage(withDistance.level, withDistance.top, depthKnown: false, depthClose: false, detectorOk: true),
      'Dikkat. İnsan, önde, 2 metre.',
    );
  });

  test('saat yönü anlatımı', () {
    final a = assess([obj(region: Region.left, ttc: 3)], null, config);
    expect(
      buildMessage(a.level, a.top, depthKnown: false, depthClose: false, detectorOk: true, style: DirectionStyle.clock),
      'Dikkat. İnsan, saat 10 yönünde.',
    );
  });

  test('"Yol açık" yalnız derinlik biliniyorsa söylenir', () {
    expect(buildMessage(AlertLevel.clear, null, depthKnown: true, depthClose: false, detectorOk: true), 'Yol açık.');
    expect(buildMessage(AlertLevel.clear, null, depthKnown: false, depthClose: false, detectorOk: true), isEmpty);
  });

  test('tespit modeli yoksa derinlik temiz olsa da "Yol açık" denmez', () {
    expect(buildMessage(AlertLevel.clear, null, depthKnown: true, depthClose: false, detectorOk: false), isEmpty);
    final engine = HazardEngine();
    for (var i = 0; i < 3; i++) {
      expect(engine.process(const [], clearRegions, detectorOk: false).message, isEmpty);
    }
  });

  test('ortada yakın derinlik NEAR verir', () {
    const regions = {
      Region.left: RegionReading(proximity: 0.2, label: 'uzak'),
      Region.center: RegionReading(proximity: 0.95, label: 'çok yakın', closeArea: 0.3),
      Region.right: RegionReading(proximity: 0.2, label: 'uzak'),
    };
    final result = assess(const [], regions, config);
    expect(result.level, AlertLevel.near);
    expect(
      buildMessage(result.level, null, depthKnown: true, depthClose: result.depthClose, detectorOk: true),
      'Dikkat. Önde engel.',
    );
  });

  group('histerezis', () {
    test('2 karede yükselir, 5 karede düşer', () {
      final h = LevelHysteresis();
      expect(h.update(AlertLevel.danger), AlertLevel.clear);
      expect(h.update(AlertLevel.danger), AlertLevel.danger);
      for (var i = 0; i < 4; i++) {
        expect(h.update(AlertLevel.clear), AlertLevel.danger);
      }
      expect(h.update(AlertLevel.clear), AlertLevel.clear);
    });

    test('tek karelik sıçrama yok sayılır', () {
      final h = LevelHysteresis();
      h.update(AlertLevel.danger);
      expect(h.update(AlertLevel.clear), AlertLevel.clear);
    });
  });

  test('kayıtlı 10 kare dizisi: DANGER kaçmaz, titreşim sayısı sınırlı', () {
    final engine = HazardEngine();
    final frames = <List<PerceivedObject>>[
      [],
      [obj(ttc: 6)],
      [obj(ttc: 4.5)],
      [obj(ttc: 3.5)],
      [obj(ttc: 2.5)],
      [obj(ttc: 1.8)],
      [obj(ttc: 1.2)],
      [obj(ttc: 0.9)],
      [],
      [],
    ];
    final levels = [for (final f in frames) engine.process(f, clearRegions, detectorOk: true).level];
    expect(levels.contains(AlertLevel.danger), isTrue);
    expect(levels.indexOf(AlertLevel.danger), 6); // 2. ardışık karede yükselir
    expect(levels.last, AlertLevel.danger); // 5 kare dolmadan düşmez
  });

  test('capitalizeTr', () {
    expect(capitalizeTr('insan'), 'İnsan');
    expect(capitalizeTr('ışık'), 'Işık');
    expect(capitalizeTr('araç'), 'Araç');
  });

  test('AlertLevel.parse', () {
    expect(AlertLevel.parse('DANGER'), AlertLevel.danger);
    expect(AlertLevel.parse('bilinmez'), AlertLevel.info);
  });
}
