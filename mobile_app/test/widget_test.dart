// This is a basic Flutter widget test for Gören Göz Mobil.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:goren_goz_mobil/main.dart';

void main() {
  testWidgets('Gören Göz app smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const GorenGozApp());

    // Wait for app to settle
    await tester.pumpAndSettle();

    // Verify that app renders (Splash screen shows app title or loading)
    // The app should at least render without crashing
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
