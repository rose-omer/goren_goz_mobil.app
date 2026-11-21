import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:goren_goz_mobil/perception/distance.dart';
import 'package:goren_goz_mobil/perception/frame_source.dart';
import 'package:goren_goz_mobil/services/settings_store.dart';
import 'package:image/image.dart' as img;

void main() {
  group('nesne boyuyla mesafe', () {
    test('d = f · H / h', () {
      final d = sizeDistance(className: 'person', focalPx: 500, top: 100, bottom: 400, imageHeight: 640);
      expect(d, closeTo(500 * 1.70 / 300, 1e-9));
    });

    test('boyu bilinmeyen sınıf için null', () {
      expect(sizeDistance(className: 'pole', focalPx: 500, top: 100, bottom: 400, imageHeight: 640), isNull);
    });

    test('kare kenarında kesik kutu için null', () {
      expect(sizeDistance(className: 'person', focalPx: 500, top: 0, bottom: 400, imageHeight: 640), isNull);
      expect(sizeDistance(className: 'person', focalPx: 500, top: 50, bottom: 640, imageHeight: 640), isNull);
    });

    test('A4 kalibrasyonu', () {
      // A4 1 m uzakta 148.5 px görünüyorsa f = 500 px.
      expect(focalFromCalibration(boxHeightPx: 148.5), closeTo(500, 1e-9));
      expect(() => focalFromCalibration(boxHeightPx: 0), throwsArgumentError);
    });

    test('odak ölçekleme', () {
      expect(scaleFocal(900, fromHeight: 1280, toHeight: 640), 450);
    });
  });

  group('oran korunur (plan D7)', () {
    test('dikey kare dikey kalır', () {
      final s = fitLongSide(720, 1280);
      expect((s.width, s.height), (360, 640));
    });

    test('küçük kare büyütülmez', () {
      final s = fitLongSide(320, 240);
      expect((s.width, s.height), (320, 240));
    });

    test('YUV → JPEG: döndürme ve küçültme oranı korur', () {
      const w = 64, h = 48;
      final frame = YuvFrame(
        width: w,
        height: h,
        y: Uint8List(w * h)..fillRange(0, w * h, 200),
        u: Uint8List(w * h ~/ 2)..fillRange(0, w * h ~/ 2, 128),
        v: Uint8List(w * h ~/ 2)..fillRange(0, w * h ~/ 2, 128),
        yRowStride: w,
        uvRowStride: w,
        uvPixelStride: 2,
        rotation: 90,
      );
      final encoded = encodeYuvFrame(frame, maxSide: 32);
      expect((encoded.width, encoded.height), (24, 32));
      final decoded = img.decodeJpg(encoded.jpeg)!;
      expect(decoded.width, 24);
      final pixel = decoded.getPixel(12, 16);
      expect(pixel.r, closeTo(200, 6));
    });
  });

  group('sunucu adresi doğrulaması (plan G8)', () {
    test('yerel ağ http kabul', () {
      expect(validateServerUrl('http://192.168.1.20:8110'), isNull);
      expect(validateServerUrl('http://10.0.0.5:8110'), isNull);
      expect(validateServerUrl('http://172.20.1.1:8110'), isNull);
    });

    test('ağ dışı http ret, https kabul', () {
      expect(validateServerUrl('http://example.com'), isNotNull);
      expect(validateServerUrl('https://example.com'), isNull);
    });

    test('boş ve bozuk adres ret', () {
      expect(validateServerUrl(''), contains('Sunucu adresini yazın'));
      expect(validateServerUrl('192.168.1.20'), isNotNull);
      expect(validateServerUrl('ftp://192.168.1.2'), isNotNull);
    });

    test('release: http ret ve nedenini söyler, https kabul', () {
      expect(validateServerUrl('http://192.168.1.20:8110', allowHttp: false), contains('http:// adresine bağlanamaz'));
      expect(validateServerUrl('https://192.168.1.20:8110', allowHttp: false), isNull);
      expect(validateServerUrl('', allowHttp: false), contains('https://'));
      expect(serverUrlHelp(allowHttp: false), contains('yalnız https'));
    });
  });
}
