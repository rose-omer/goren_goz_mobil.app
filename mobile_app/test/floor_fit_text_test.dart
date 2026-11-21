// Sığdırma tabanı (plan 5.1): bant etiketi 28 sp, gövde 24 sp altına inmez.

import 'package:flutter_test/flutter_test.dart';
import 'package:goren_goz_mobil/services/settings_store.dart';
import 'package:goren_goz_mobil/theme/app_theme.dart';
import 'package:goren_goz_mobil/widgets/band_button.dart';
import 'package:goren_goz_mobil/widgets/floor_fit_text.dart';
import 'package:material_ui/material_ui.dart';

Future<void> pumpBox(WidgetTester tester, Widget child, {required Size size, double textScale = 1}) async {
  await tester.pumpWidget(
    MaterialApp(
      theme: buildTheme(Contrast.darkSignal),
      home: MediaQuery(
        data: MediaQueryData(textScaler: TextScaler.linear(textScale)),
        child: Scaffold(
          body: Center(
            child: SizedBox(width: size.width, height: size.height, child: child),
          ),
        ),
      ),
    ),
  );
}

/// Ekranda görünen boy: stil boyu × yazı ölçeği.
double shownSize(WidgetTester tester, String text, double textScale) {
  final widget = tester.widget<Text>(find.text(text));
  return widget.style!.fontSize! * textScale;
}

void main() {
  for (final scale in [1.0, 1.5, 2.0]) {
    testWidgets('dar bantta etiket 28 sp altına inmez (ölçek $scale)', (tester) async {
      await pumpBox(
        tester,
        const BandButton(
          label: 'Durumu söyle',
          hint: 'Sahneyi okur',
          icon: Icons.record_voice_over,
          detail: 'Dinliyorum',
        ),
        size: const Size(320, 110),
        textScale: scale,
      );
      expect(tester.takeException(), isNull);
      expect(shownSize(tester, 'Durumu söyle', scale), greaterThanOrEqualTo(TypeScale.buttonMin - 0.01));
    });
  }

  testWidgets('yer varsa tam boy ve ek satır görünür', (tester) async {
    await pumpBox(
      tester,
      const BandButton(label: 'Soru sor', hint: 'Basılı tutun', icon: Icons.mic, detail: 'Dinliyorum'),
      size: const Size(400, 200),
    );
    expect(shownSize(tester, 'Soru sor', 1), TypeScale.band);
    expect(find.text('Dinliyorum'), findsOneWidget);
  });

  testWidgets('sığmayan ek satır gizlenir, etiket küçülmez', (tester) async {
    await pumpBox(
      tester,
      const BandButton(label: 'Soru sor', hint: 'Basılı tutun', icon: Icons.mic, detail: 'Cevap bekleniyor'),
      size: const Size(400, 96),
      textScale: 2,
    );
    expect(tester.takeException(), isNull);
    expect(find.text('Cevap bekleniyor'), findsNothing);
    expect(shownSize(tester, 'Soru sor', 2), greaterThanOrEqualTo(TypeScale.buttonMin));
  });

  testWidgets('uzun durum metni 24 sp altına inmez, taşma hatası yok', (tester) async {
    const text = 'Kaydedildi ama sunucu cevap vermedi. Adresi ve ağı denetleyin. Sonra yeniden deneyin.';
    await pumpBox(
      tester,
      const FloorFitText(
        text,
        minSize: TypeScale.body,
        style: TextStyle(fontSize: TypeScale.status),
      ),
      size: const Size(200, 60),
      textScale: 2,
    );
    expect(tester.takeException(), isNull);
    expect(shownSize(tester, text, 2), greaterThanOrEqualTo(TypeScale.body));
  });
}
