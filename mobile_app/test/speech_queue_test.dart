import 'package:flutter_test/flutter_test.dart';
import 'package:goren_goz_mobil/core/hazard_engine.dart';
import 'package:goren_goz_mobil/core/speech_queue.dart';

import 'fakes.dart';

void main() {
  late FakeSpeaker speaker;
  late DateTime now;
  late SpeechQueue queue;

  setUp(() {
    speaker = FakeSpeaker()..hold = true;
    now = DateTime(2026, 11, 20, 12);
    queue = SpeechQueue(speaker, clock: () => now);
  });

  test('ilk mesaj hemen okunur', () {
    queue.enqueue('İnsan, solda.', AlertLevel.info, key: 'insan/left');
    expect(speaker.spoken, ['İnsan, solda.']);
  });

  test('DANGER konuşmayı keser ve sıranın başına geçer', () async {
    queue.enqueue('İnsan, solda.', AlertLevel.info, key: 'a');
    queue.enqueue('Bank, sağda.', AlertLevel.info, key: 'b');
    queue.enqueue('Dur. Araç, önde.', AlertLevel.danger, key: 'c');
    expect(speaker.stops, 1);
    expect(speaker.spoken.last, 'Dur. Araç, önde.');
    expect(queue.pending, isEmpty, reason: 'eski bilgi mesajları atılır');
  });

  test('aynı nesne-yön mesajı 6 s içinde tekrar edilmez', () async {
    speaker.hold = false;
    queue.enqueue('Dikkat. Direk, sağda.', AlertLevel.near, key: 'direk/right');
    await Future<void>.delayed(Duration.zero);
    now = now.add(const Duration(seconds: 3));
    queue.enqueue('Dikkat. Direk, sağda.', AlertLevel.near, key: 'direk/right');
    await Future<void>.delayed(Duration.zero);
    expect(speaker.spoken.length, 1);

    now = now.add(const Duration(seconds: 4));
    queue.enqueue('Dikkat. Direk, sağda.', AlertLevel.near, key: 'direk/right');
    expect(speaker.spoken.length, 2);
  });

  test('kuyrukta en fazla 2 mesaj kalır; eskisi atılır', () {
    queue.enqueue('bir', AlertLevel.info, key: '1');
    queue.enqueue('iki', AlertLevel.info, key: '2');
    queue.enqueue('üç', AlertLevel.info, key: '3');
    queue.enqueue('dört', AlertLevel.info, key: '4');
    expect(queue.pending.map((i) => i.text), ['üç', 'dört']);
  });

  test('sıradaki mesaj önceki bitince okunur', () async {
    queue.enqueue('bir', AlertLevel.info, key: '1');
    queue.enqueue('iki', AlertLevel.info, key: '2');
    expect(speaker.spoken, ['bir']);
    speaker.finishCurrent();
    await Future<void>.delayed(Duration.zero);
    expect(speaker.spoken, ['bir', 'iki']);
  });

  test('force tekrar penceresini yok sayar', () async {
    speaker.hold = false;
    queue.enqueue('Yol açık.', AlertLevel.info, key: 'durum');
    await Future<void>.delayed(Duration.zero);
    queue.enqueue('Yol açık.', AlertLevel.info, key: 'durum', force: true);
    expect(speaker.spoken.length, 2);
  });

  test('boş metin atılır', () {
    queue.enqueue('  ', AlertLevel.danger);
    expect(speaker.spoken, isEmpty);
  });

  test('clear konuşmayı durdurur', () async {
    queue.enqueue('bir', AlertLevel.info, key: '1');
    queue.enqueue('iki', AlertLevel.info, key: '2');
    await queue.clear();
    expect(queue.pending, isEmpty);
    expect(speaker.stops, 1);
  });
}
