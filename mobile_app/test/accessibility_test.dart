// Erişilebilirlik widget testleri (plan 6.2): dokunma alanı, etiket, kontrast, TalkBack adları.

import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:goren_goz_mobil/app.dart';
import 'package:goren_goz_mobil/services/settings_store.dart';
import 'package:material_ui/material_ui.dart';

import 'fakes.dart';

Future<TestHarness> pumpApp(WidgetTester tester, {Map<String, Object> prefs = serverPrefs, Size? size}) async {
  tester.view.physicalSize = size ?? const Size(1080, 2340);
  tester.view.devicePixelRatio = 2.625;
  addTearDown(tester.view.reset);
  final h = await TestHarness.create(prefs: prefs);
  await tester.pumpWidget(GorenGozApp(services: h.services));
  await tester.pump();
  return h;
}

Future<void> openSettings(WidgetTester tester) async {
  await tester.tap(find.text('Ayarlar'));
  for (var i = 0; i < 10 && find.text('Konuşma hızı').evaluate().isEmpty; i++) {
    await tester.pump(const Duration(milliseconds: 50));
  }
}

Future<void> centerOn(WidgetTester tester, Finder finder) async {
  await Scrollable.ensureVisible(tester.element(finder), alignment: 0.5);
  await tester.pump();
}

/// Semantik ağacındaki bütün değerler (kaydırıcı okuması gibi).
List<String> semanticsValues(WidgetTester tester) {
  final values = <String>[];
  bool visit(SemanticsNode node) {
    if (node.value.isNotEmpty) values.add(node.value);
    node.visitChildren(visit);
    return true;
  }

  visit(tester.getSemantics(find.byType(ListView)));
  return values;
}

Future<void> expectGuidelines(WidgetTester tester) async {
  await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
  await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
  await expectLater(tester, meetsGuideline(textContrastGuideline));
}

void main() {
  group('yürüyüş ekranı', () {
    testWidgets('dört bant TalkBack adıyla bulunur ve kılavuzlara uyar', (tester) async {
      final handle = tester.ensureSemantics();
      await pumpApp(tester);

      for (final label in ['Durumu söyle', 'Soru sor', 'Duraklat', 'Ayarlar']) {
        expect(find.bySemanticsLabel(RegExp('^$label')), findsOneWidget, reason: label);
      }
      await expectGuidelines(tester);
      handle.dispose();
    });

    testWidgets('her bant ekran yüksekliğinin en az %20\'si', (tester) async {
      await pumpApp(tester);
      final screen = tester.view.physicalSize.height / tester.view.devicePixelRatio;
      for (var i = 0; i < 4; i++) {
        final band = find.byKey(ValueKey('bant-$i'));
        expect(tester.getSize(band).height, greaterThanOrEqualTo(screen * 0.2 - 0.5), reason: 'bant $i');
      }
    });

    testWidgets('durum şeridi liveRegion', (tester) async {
      final handle = tester.ensureSemantics();
      await pumpApp(tester);
      final node = tester.getSemantics(find.byType(Semantics).at(0));
      expect(node, isNotNull);
      final strip = find.bySemanticsLabel('Algılama açık.');
      expect(strip, findsOneWidget);
      expect(tester.getSemantics(strip).flagsCollection.isLiveRegion, isTrue);
      handle.dispose();
    });

    testWidgets('sunucu yoksa Ayarlar bandı nedeni söyler', (tester) async {
      final handle = tester.ensureSemantics();
      await pumpApp(tester, prefs: const {'onboarded': true});
      expect(find.bySemanticsLabel('Ayarlar. Sunucu adresi gerekli.'), findsOneWidget);
      handle.dispose();
    });

    testWidgets('Duraklat bandı durumu değiştirir', (tester) async {
      final h = await pumpApp(tester);
      await tester.tap(find.text('Duraklat'));
      await tester.pump();
      expect(find.text('Devam et'), findsOneWidget);
      expect(h.speaker.spoken.last, 'Algılama duraklatıldı.');
    });

    testWidgets('beyaz tema da kontrast kılavuzuna uyar', (tester) async {
      final handle = tester.ensureSemantics();
      await pumpApp(tester, prefs: {...serverPrefs, 'contrast': Contrast.lightInk.index});
      await expectGuidelines(tester);
      handle.dispose();
    });

    testWidgets('%200 yazı ölçeğinde taşma yok', (tester) async {
      tester.platformDispatcher.textScaleFactorTestValue = 2.0;
      addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
      await pumpApp(tester);
      expect(tester.takeException(), isNull);
    });
  });

  group('açılış', () {
    testWidgets('tek büyük izin düğmesi ve hoş geldin sesi', (tester) async {
      final handle = tester.ensureSemantics();
      final h = await pumpApp(tester, prefs: const {});
      await tester.pump();
      expect(find.text('Kamera iznini ver'), findsOneWidget);
      expect(h.speaker.spoken.first, contains("Gören Göz'e hoş geldiniz"));
      await expectGuidelines(tester);
      handle.dispose();
    });

    testWidgets('ret durumunda ayarları açar', (tester) async {
      final h = await TestHarness.create(prefs: const {});
      h.permissions.grant = false;
      tester.view.physicalSize = const Size(1080, 2340);
      tester.view.devicePixelRatio = 2.625;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(GorenGozApp(services: h.services));
      await tester.tap(find.text('Kamera iznini ver'));
      await tester.pump();
      expect(find.text('Ayarları aç'), findsOneWidget);
      await tester.tap(find.text('Ayarları aç'));
      expect(h.permissions.opened, 1);
    });

    testWidgets('izin verilince yürüyüşe geçer ve güvenlik uyarısını bir kez okur', (tester) async {
      final h = await pumpApp(tester, prefs: const {});
      await tester.tap(find.text('Kamera iznini ver'));
      await tester.pump();
      await tester.pump();
      expect(find.text('Durumu söyle'), findsOneWidget);
      expect(h.speaker.spoken.any((s) => s.contains('Baston ya da rehber köpeğin yerini tutmaz')), isTrue);
      expect(h.settings.safetyHeard, isTrue);
    });
  });

  group('ayarlar', () {
    testWidgets('kılavuzlara uyar ve kaydırıcı değeri okunur', (tester) async {
      final handle = tester.ensureSemantics();
      await pumpApp(tester);
      await openSettings(tester);
      expect(find.text('Konuşma hızı'), findsOneWidget);
      expect(semanticsValues(tester), contains('Konuşma hızı yüzde 60'));
      await expectGuidelines(tester);
      handle.dispose();
    });

    testWidgets('geçersiz sunucu adresi alan altında hata verir', (tester) async {
      await pumpApp(tester);
      await openSettings(tester);
      await tester.scrollUntilVisible(find.text('Kaydet ve dene'), 300);
      final field = find.widgetWithText(TextFormField, 'Sunucu adresi');
      await tester.enterText(field, 'http://example.com');
      await centerOn(tester, find.text('Kaydet ve dene'));
      await tester.tap(find.text('Kaydet ve dene'));
      await tester.pump();
      expect(find.text('Yerel ağ dışındaki sunucu için https:// kullanın.'), findsOneWidget);
    });

    testWidgets('geçerli adres kaydedilir ve bağlantı sonucu söylenir', (tester) async {
      final h = await pumpApp(tester);
      await openSettings(tester);
      await tester.scrollUntilVisible(find.text('Kaydet ve dene'), 300);
      await tester.enterText(find.widgetWithText(TextFormField, 'Sunucu adresi'), 'http://192.168.1.50:8110');
      await centerOn(tester, find.text('Kaydet ve dene'));
      await tester.tap(find.text('Kaydet ve dene'));
      await tester.pump();
      await tester.pump();
      expect(h.settings.serverUrl, 'http://192.168.1.50:8110');
      expect(find.text('Kaydedildi. Sunucu cevap veriyor.'), findsOneWidget);
    });
  });
}
