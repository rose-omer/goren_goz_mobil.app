import 'package:flutter_test/flutter_test.dart';
import 'package:goren_goz_mobil/core/hazard_engine.dart';
import 'package:goren_goz_mobil/core/scene_summary.dart';
import 'package:goren_goz_mobil/services/api_client.dart';
import 'package:goren_goz_mobil/services/feedback.dart';
import 'package:goren_goz_mobil/walk/walk_controller.dart';

import 'fakes.dart';

Future<(TestHarness, WalkController)> setup({Map<String, Object> prefs = serverPrefs}) async {
  final h = await TestHarness.create(prefs: prefs);
  final c = WalkController(
    settings: h.settings,
    frames: h.frames,
    apiProvider: () => h.services.apiFactory(h.settings),
    speech: h.services.speech,
    haptics: h.haptics,
    sounds: h.sounds,
    speechInput: h.speechInput,
  );
  return (h, c);
}

Future<void> settle() => Future<void>.delayed(Duration.zero);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('sunucu yoksa ayar ister ve kamerayı açmaz', () async {
    final (h, c) = await setup(prefs: const {'onboarded': true});
    await c.start();
    expect(c.status, WalkStatus.needsServer);
    expect(h.frames.started, isFalse);
    expect(h.speaker.spoken.single, contains('Sunucu adresi gerekli'));
    c.dispose();
  });

  test('yaklaşan insan: iki karede DANGER, ses, titreşim ve "Dur" konuşması', () async {
    final (h, c) = await setup();
    await c.start();
    h.api.queue.addAll([
      analysis(objects: [person(ttc: 1.5)]),
      analysis(objects: [person(ttc: 1.2)]),
    ]);
    await h.frames.emit();
    expect(c.hazard.level, AlertLevel.clear, reason: 'tek kare yükseltmez');
    await h.frames.emit();
    await settle();
    expect(c.hazard.level, AlertLevel.danger);
    expect(h.sounds.played, contains(Cue.danger));
    expect(h.haptics.played, contains(HapticPattern.danger));
    expect(h.speaker.spoken.last, 'Dur. İnsan, önde.');
    c.dispose();
  });

  test('bağlantı kopunca bir kez uyarır, geri gelince haber verir', () async {
    final (h, c) = await setup();
    await c.start();
    h.api.failure = const ApiFailure('OFFLINE', 'x');
    await h.frames.emit();
    await h.frames.emit();
    expect(c.status, WalkStatus.offline);
    expect(h.haptics.played.where((p) => p == HapticPattern.disconnected).length, 1);
    h.api.failure = null;
    await h.frames.emit();
    await settle();
    expect(c.status, WalkStatus.running);
    expect(h.speaker.spoken, contains('Bağlantı geri geldi.'));
    c.dispose();
  });

  test('tek zaman aşımı kopma sayılmaz, ikincisi sayılır', () async {
    final (h, c) = await setup();
    await c.start();
    h.api.failure = const ApiFailure('TIMEOUT', 'x');
    await h.frames.emit();
    expect(c.status, WalkStatus.running);
    expect(h.speaker.spoken.where((s) => s.startsWith('Bağlantı koptu')), isEmpty);
    await h.frames.emit();
    expect(c.status, WalkStatus.offline);
    expect(h.speaker.spoken.where((s) => s.startsWith('Bağlantı koptu')).length, 1);
    c.dispose();
  });

  test('sunucuda tespit yoksa "Yol açık" denmez ve kullanıcı bir kez bilgilenir', () async {
    final (h, c) = await setup();
    await c.start();
    for (var i = 0; i < 4; i++) {
      h.api.queue.add(analysis(detectorOk: false));
    }
    for (var i = 0; i < 4; i++) {
      await h.frames.emit();
    }
    await settle();
    expect(h.speaker.spoken, isNot(contains('Yol açık.')));
    expect(h.speaker.spoken.where((s) => s.startsWith('Sunucuda nesne tespiti çalışmıyor')).length, 1);
    await c.sayStatus();
    expect(h.speaker.spoken.last, 'Nesne tespiti çalışmıyor.');
    c.dispose();
  });

  test('eski sunucu detector_ok göndermezse tespit çalışıyor sayılmaz', () {
    final json = {
      'processing_time_ms': 1.0,
      'data': {'objects': <Object>[], 'regions': null},
    };
    expect(FrameAnalysis.fromJson(json, width: 1, height: 1).detectorOk, isFalse);
  });

  test('TalkBack açıkken bilgi mesajı TTS yerine liveRegion\'a gider', () async {
    final (h, c) = await setup();
    c.screenReaderOn = true;
    await c.start();
    h.speaker.spoken.clear();
    h.api.queue.addAll([
      analysis(objects: [person(region: 'left')]),
      analysis(objects: [person(region: 'left')]),
    ]);
    await h.frames.emit();
    await h.frames.emit();
    await settle();
    expect(h.speaker.spoken, isEmpty);
    expect(c.liveMessage, 'İnsan, solda.');
    c.dispose();
  });

  test('soru akışı: dinle, sor, cevabı oku', () async {
    final (h, c) = await setup();
    await c.start();
    await c.beginQuestion();
    expect(c.askState, AskState.listening);
    expect(h.sounds.played, contains(Cue.listenStart));
    await c.finishQuestion();
    await settle();
    expect(h.api.questions, ['Önümde ne var?']);
    expect(c.askState, AskState.idle);
    expect(h.speaker.spoken.last, startsWith('Önünüzde bir kapı var.'));
    expect(h.haptics.played, contains(HapticPattern.answer));
    c.dispose();
  });

  test('VLM yoksa tehlike döngüsü sürer ve kullanıcı bilgilenir', () async {
    final (h, c) = await setup();
    await c.start();
    h.api.askFailure = const ApiFailure('VLM_UNAVAILABLE', 'x');
    await c.ask('Merdiven var mı?');
    await settle();
    expect(h.speaker.spoken.last, 'Cevap alınamadı. Tehlike uyarıları açık.');
    expect(c.status, WalkStatus.running);
    c.dispose();
  });

  test('duraklat ve devam et sesle söylenir', () async {
    final (h, c) = await setup();
    await c.start();
    await c.togglePause();
    expect(c.isPaused, isTrue);
    expect(h.frames.started, isFalse);
    expect(h.speaker.spoken.last, 'Algılama duraklatıldı.');
    await c.togglePause();
    expect(c.status, WalkStatus.running);
    c.dispose();
  });

  test('sahne özeti', () {
    const hazard = HazardResult(level: AlertLevel.clear, rawLevel: AlertLevel.clear, message: 'Yol açık.', top: null);
    final text = sceneSummary(
      hazard: hazard,
      objects: const [
        SceneObject('insan', Region.left, proximityLabel: 'uzak'),
        SceneObject('insan', Region.left, proximityLabel: 'uzak'),
      ],
      depthKnown: true,
      detectorOk: true,
    );
    expect(text, 'Yol açık. Solda 2 insan, uzak.');
  });
}
