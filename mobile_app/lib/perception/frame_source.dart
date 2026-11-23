// Kamera kare kaynağı: `startImageStream` + YUV420, `ResolutionPreset.medium` (plan E9).
// Önceki kare işlenmeden yeni kare alınmaz. Kare diske yazılmaz (plan 4.8).

import 'dart:async';
import 'dart:isolate';
import 'dart:typed_data';

import 'package:camera/camera.dart';
import 'package:image/image.dart' as img;

import 'distance.dart';

/// Gönderime hazır kare: oranı korunmuş, uzun kenarı ≤ 640 px JPEG.
class EncodedFrame {
  const EncodedFrame(this.jpeg, this.width, this.height);

  final Uint8List jpeg;
  final int width;
  final int height;
}

/// İsolate'a geçen düz veri; `CameraImage` isolate sınırını geçemez.
class YuvFrame {
  const YuvFrame({
    required this.width,
    required this.height,
    required this.y,
    required this.u,
    required this.v,
    required this.yRowStride,
    required this.uvRowStride,
    required this.uvPixelStride,
    required this.rotation,
  });

  factory YuvFrame.fromCamera(CameraImage image, int rotation) => YuvFrame(
    width: image.width,
    height: image.height,
    y: image.planes[0].bytes,
    u: image.planes[1].bytes,
    v: image.planes[2].bytes,
    yRowStride: image.planes[0].bytesPerRow,
    uvRowStride: image.planes[1].bytesPerRow,
    uvPixelStride: image.planes[1].bytesPerPixel ?? 1,
    rotation: rotation,
  );

  final int width;
  final int height;
  final Uint8List y;
  final Uint8List u;
  final Uint8List v;
  final int yRowStride;
  final int uvRowStride;
  final int uvPixelStride;
  final int rotation;
}

/// YUV420 → RGB → (döndür) → JPEG. Uzun kenarı [maxSide]'a indirirken oranı korur (plan D7).
EncodedFrame encodeYuvFrame(YuvFrame frame, {int maxSide = 640, int quality = 75}) {
  final size = fitLongSide(frame.width, frame.height, maxSide: maxSide);
  final out = img.Image(width: size.width, height: size.height);
  final sx = frame.width / size.width;
  final sy = frame.height / size.height;
  for (var oy = 0; oy < size.height; oy++) {
    final yy = (oy * sy).floor();
    final uvRow = (yy >> 1) * frame.uvRowStride;
    for (var ox = 0; ox < size.width; ox++) {
      final xx = (ox * sx).floor();
      final yv = frame.y[yy * frame.yRowStride + xx];
      final uvIndex = uvRow + (xx >> 1) * frame.uvPixelStride;
      final u = frame.u[uvIndex] - 128;
      final v = frame.v[uvIndex] - 128;
      out.setPixelRgb(
        ox,
        oy,
        (yv + 1.402 * v).round().clamp(0, 255),
        (yv - 0.344136 * u - 0.714136 * v).round().clamp(0, 255),
        (yv + 1.772 * u).round().clamp(0, 255),
      );
    }
  }
  final rotated = frame.rotation == 0 ? out : img.copyRotate(out, angle: frame.rotation);
  return EncodedFrame(img.encodeJpg(rotated, quality: quality), rotated.width, rotated.height);
}

/// [encodeYuvFrame]'i yan isolate'te çalıştırır. Closure burada kurulur; yalnız kareyi ve
/// ayarları yakalar. Çağıranın içinde kurulursa `onFrame` ve `this` de isolate mesajına girer
/// ("object is unsendable") ve hiçbir kare kodlanmaz.
Future<EncodedFrame> encodeYuvFrameInIsolate(YuvFrame frame, {int maxSide = 640, int quality = 75}) =>
    Isolate.run(() => encodeYuvFrame(frame, maxSide: maxSide, quality: quality));

abstract interface class FrameSource {
  /// Kamera hazır mı.
  bool get isReady;

  /// Önizleme için denetleyici (yardımcı görünümü). Testte `null`.
  CameraController? get controller;

  Future<void> start(Future<void> Function(EncodedFrame frame) onFrame);
  Future<void> stop();

  /// Son kareyi verir (soru için). Kare yoksa `null`.
  Future<EncodedFrame?> latest();
  Future<void> dispose();
}

class CameraFrameSource implements FrameSource {
  CameraController? _controller;
  bool _busy = false;
  YuvFrame? _lastRaw;
  int _rotation = 90;

  @override
  bool get isReady => _controller?.value.isInitialized ?? false;

  @override
  CameraController? get controller => _controller;

  Future<void> _ensureController() async {
    if (isReady) return;
    final cameras = await availableCameras();
    final back = cameras.firstWhere((c) => c.lensDirection == CameraLensDirection.back, orElse: () => cameras.first);
    _rotation = back.sensorOrientation;
    final controller = CameraController(
      back,
      ResolutionPreset.medium,
      enableAudio: false,
      imageFormatGroup: ImageFormatGroup.yuv420,
    );
    await controller.initialize();
    _controller = controller;
  }

  @override
  Future<void> start(Future<void> Function(EncodedFrame frame) onFrame) async {
    await _ensureController();
    final controller = _controller!;
    if (controller.value.isStreamingImages) return;
    await controller.startImageStream((image) {
      final raw = YuvFrame.fromCamera(image, _rotation);
      _lastRaw = raw;
      // Son çıkarım bitmeden yeni kare alma (plan E11).
      if (_busy) return;
      _busy = true;
      unawaited(encodeYuvFrameInIsolate(raw).then(onFrame).whenComplete(() => _busy = false));
    });
  }

  @override
  Future<void> stop() async {
    final controller = _controller;
    if (controller != null && controller.value.isStreamingImages) {
      await controller.stopImageStream();
    }
  }

  @override
  Future<EncodedFrame?> latest() async {
    final raw = _lastRaw;
    if (raw == null) return null;
    return encodeYuvFrameInIsolate(raw, maxSide: 768, quality: 85);
  }

  /// Uygulama arka plana geçince kamerayı bırakır (plan M8).
  @override
  Future<void> dispose() async {
    final controller = _controller;
    _controller = null;
    _lastRaw = null;
    _busy = false;
    await controller?.dispose();
  }
}
