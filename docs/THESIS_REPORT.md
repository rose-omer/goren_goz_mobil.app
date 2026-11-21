# Gören Göz: bitirme projesi raporu

- Konu: Görme engelliler için sesli engel uyarısı ve Türkçe görsel soru-cevap.
- Geliştirici: rose-omer (GitHub). Teslimden önce tam ad yazılmalı.
- Sürüm: 2.0.0 (geliştirme dalı). Eski kök raporlar (5 dosya) bu dosyada birleşti.

## 1. Amaç

Görme engelli kullanıcı telefonu önüne tutar. Uygulama önündeki engeli bulur, tehlikeyi kısa Türkçe cümle, ses ve titreşimle bildirir. Kullanıcı sahne hakkında Türkçe soru sorabilir. Uygulama baston ya da rehber köpeğin yerini tutmaz.

## 2. Mimari

- Mobil (Flutter 3.50.1): kamera akışı, uyarı motoru, konuşma kuyruğu, haptik, TalkBack uyumlu dört bantlı arayüz.
- Sunucu (FastAPI 0.165): MiDaS_small (OpenVINO) göreli derinlik, YOLO nesne tespiti, oturum başına takip ve TTC, Türkçe VLM sorusu.
- Hedef mimari: tehlike döngüsü cihaz üstünde (LiteRT), sunucu yalnız VLM ve karşılaştırma için. Cihaz üstü model henüz eğitilmedi.

Ayrıntı: `docs/ARCHITECTURE.md`.

## 3. Önceki sürümden düzeltilen hatalar

| Konu | Eski davranış | Yeni davranış |
|---|---|---|
| Mesafe (D1) | MiDaS çıktısı her karede 0.5–5 m'ye yayılıyordu; söylenen metre uydurmaydı. | Derinlikten metre söylenmez. Metre yalnız nesne boyu + kalibrasyondan; yaklaşma TTC ile. |
| Orta seviye (D2) | Maske hep boştu. | Kural yeniden yazıldı; testle korunur. |
| Ön işleme (D3) | OpenVINO ve PyTorch farklı normalize ediyordu. | Tek fonksiyon, ImageNet normu, testli. |
| Şema (D4) | Nesne mesafesi yanıttan düşüyordu. | `distance_m`, `ttc_s` alanları. |
| VLM (D10, D11) | Görüntü büyük olasılıkla gönderilmiyordu; istem İngilizceydi. | `/v1/chat/completions` + `image_url`, Türkçe istem ve hazır sorular. |
| Gizlilik (G1, G2) | Son kare ağa açık yayınlanıyor, soru görüntüleri bellekte tutuluyordu. | Yayın kaldırıldı; debug uçları yalnız debug ve yerel; görüntü saklanmaz. |
| Kimlik (G4) | Yoktu. | `X-API-Key`. |
| Erişilebilirlik (M1, M2) | Mikrofon ve düğmeler TalkBack'te adsızdı. | Her denetim Türkçe ad ve ipucuyla; widget testleri kılavuzları denetler. |
| Gecikme (E9, E11) | Her karede deklanşör + diske JPEG; bayt karşılaştırmalı kare atlama. | Görüntü akışı, isolate'ta kodlama, çıkarım bitmeden yeni kare yok. |

## 4. Ölçümler

Bu sürümde sahada ölçüm yapılmadı. Eski raporlardaki "3-5x hızlı", "+17% doğruluk" gibi ölçülmemiş iddialar çıkarıldı.

Bu makinede (CPU, OpenVINO 2024.6) yerel deneme: MiDaS_small çıkarımı ilk karede 83 ms, ısındıktan sonra 7.5 ms (tek ölçüm; istatistik değildir).

Yapılacak ölçümler ve tablolar: `docs/TEST_PLAN.md`.

## 5. Sınırlar ve riskler

- Yanlış "Yol açık" mesajı yaralanmaya yol açabilir. Mesaj yalnız derinlik de temizse söylenir.
- Nesne boyu yöntemi oturan, eğilen ya da kesik görünen kişide yanılır; TTC ile birlikte kullanılır.
- COCO modeli merdiven, bordür, çukur tanımaz; 12 sınıflı model gerekir.
- Algılama şimdilik sunucuya bağlı; bağlantı kopması sesle bildirilir.
- Lisans: Ultralytics AGPL-3.0 eğitilen modeli de kapsar.

## 6. Gelecek çalışma

1. 12 sınıflı YOLO26n eğitimi ve LiteRT INT8 dışa aktarma.
2. Cihaz üstü tespit ve derinlik (`flutter_litert`), uçak modunda çalışan tehlike döngüsü.
3. VLM model karşılaştırması (30 soru × 4 model).
4. Saha testi (10 senaryo) ve TalkBack el testi.
