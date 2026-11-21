// Nesne boyuyla mesafe: d = f_px · H_gerçek / h_px (plan 4.2).
// Göreli derinlik metre vermez; bu dosya yalnız ölçülebilir yolu içerir.

/// Ortalama gerçek yükseklik (metre). Boyu değişken sınıflar (direk) bilerek yok.
const Map<String, double> realHeightM = {
  'person': 1.70,
  'car': 1.50,
  'vehicle': 1.50,
  'bicycle': 1.05,
  'motorcycle': 1.10,
  'bus': 3.00,
  'truck': 3.00,
  'dog': 0.55,
  'chair': 0.90,
};

/// A4 kâğıdının uzun kenarı (metre). Kalibrasyon: kâğıt 1 m uzakta, dik tutulur.
const double a4HeightM = 0.297;

/// Kalibrasyondan odak uzaklığı (piksel): f = h_px · d / H.
double focalFromCalibration({required double boxHeightPx, double distanceM = 1.0, double realM = a4HeightM}) {
  if (boxHeightPx <= 0 || distanceM <= 0 || realM <= 0) {
    throw ArgumentError('Kalibrasyon değerleri pozitif olmalı.');
  }
  return boxHeightPx * distanceM / realM;
}

/// Odak uzaklığını başka bir kare yüksekliğine ölçekler (ör. 1080 px kalibrasyon → 640 px gönderim).
double scaleFocal(double focalPx, {required int fromHeight, required int toHeight}) => focalPx * toHeight / fromHeight;

/// Mesafe (metre). Sınıfın boyu bilinmiyorsa, kutu çok küçükse ya da kare kenarında kesikse `null`.
double? sizeDistance({
  required String className,
  required double focalPx,
  required double top,
  required double bottom,
  required int imageHeight,
  double edgeMarginPx = 2,
}) {
  final real = realHeightM[className];
  final height = bottom - top;
  if (real == null || focalPx <= 0 || height < 8) return null;
  if (top <= edgeMarginPx || bottom >= imageHeight - edgeMarginPx) return null;
  return focalPx * real / height;
}

/// Uzun kenarı [maxSide] olacak boyutu, en-boy oranını koruyarak hesaplar (plan D7).
({int width, int height}) fitLongSide(int width, int height, {int maxSide = 640}) {
  final longSide = width > height ? width : height;
  if (longSide <= maxSide) return (width: width, height: height);
  final scale = maxSide / longSide;
  return (width: (width * scale).round(), height: (height * scale).round());
}
