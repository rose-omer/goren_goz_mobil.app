// Sesli ve yazılı sabit metinler. Aynı şey için hep aynı terim: "Durumu söyle", "Soru sor", "Duraklat".

abstract final class Texts {
  static const welcome = "Gören Göz'e hoş geldiniz. Kamera izni gerekiyor. Ekranın alt yarısına dokunun.";

  static const safety = 'Gören Göz yardımcı bir araçtır. Baston ya da rehber köpeğin yerini tutmaz.';

  static const cameraDenied = 'İzin olmadan çalışamam. Ayarları açmak için dokunun.';

  /// Yaklaşık 20 saniyelik sesli kullanım turu (plan 5.2.1).
  static const tour =
      'Ekran yukarıdan aşağıya dört banda bölünür. '
      'Birinci bant Durumu söyle: son sahneyi okur. '
      'İkinci bant Soru sor: basılı tutup konuşun, bırakınca soru gider. '
      'Üçüncü bant Duraklat: algılamayı durdurur ya da sürdürür. '
      'Dördüncü bant Ayarlar. '
      'Tehlikede üç kısa titreşim ve Dur uyarısı duyarsınız.';
}
