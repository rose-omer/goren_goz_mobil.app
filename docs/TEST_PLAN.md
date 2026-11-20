# Test planı

## Otomatik

| Komut | Kapsam |
|---|---|
| `cd backend; pytest` | Uyarı kuralı, histerezis, TTC, takip (D2, D8), şema `distance_m`/`ttc_s` (D4), 401/413/429/503, debug uçları 404 (G1, G2, G10), VLM gövdesi `image_url` (D10), ayar ayrıştırma (Y1), MiDaS ön işleme (D3). |
| `cd backend; pytest -m requires_model` | Gerçek MiDaS IR ile çıkarım. `MODELS_DIR` model içermeli. |
| `cd backend; ruff check .; ruff format --check .` | Lint ve biçim. |
| `cd mobile_app; flutter analyze` | Lint (`flutter_lints` 6). |
| `cd mobile_app; flutter test` | Uyarı motoru, konuşma kuyruğu, mesafe, YUV dönüşümü, sunucu adresi doğrulaması, yürüyüş döngüsü, erişilebilirlik kılavuzları (`androidTapTargetGuideline`, `labeledTapTargetGuideline`, `textContrastGuideline`), %200 yazı ölçeği. |

CI: `.github/workflows/ci.yml` (backend, mobile, docker, 5 MB dosya koruması).

## El testi listesi

Her madde iki cihazda (Android sürümü farklı) yapılır.

- [ ] TalkBack açık: açılıştan soru cevabına kadar bütün akış gözler kapalı tamamlanır.
- [ ] TalkBack açık: DANGER uyarısı TalkBack konuşmasını keser.
- [ ] TalkBack kapalı: bilgi mesajları TTS ile, tekrar etmeden okunur.
- [ ] Büyük yazı (%200): bant etiketleri okunur, metin kırpılmaz.
- [ ] Beyaz tema ve siyah-sarı tema: güneş altında okunur.
- [ ] Uçak modu: "Bağlantı koptu" sesi ve uzun titreşim; bağlantı gelince "Bağlantı geri geldi."
- [ ] Mikrofon izni reddi: "Mikrofon izni yok" mesajı; tehlike döngüsü sürer.
- [ ] Uygulama arka plana geçince kamera kapanır, dönünce açılır.

## Saha testi

Gören bir refakatçiyle yapılır. Gözü bağlı denemede refakatçi her an durdurur.

| # | Senaryo | Kaçırılan DANGER | Yanlış DANGER / dk | Uyarı gecikmesi (ms) |
|---|---|---|---|---|
| 1 | Koridor | | | |
| 2 | Kapı | | | |
| 3 | Merdiven başı | | | |
| 4 | Kaldırım bordürü | | | |
| 5 | Direk | | | |
| 6 | Park etmiş araç | | | |
| 7 | Yaklaşan yaya | | | |
| 8 | Yaya geçidi | | | |
| 9 | Karanlık oda | | | |
| 10 | Kalabalık | | | |

Gecikme video zaman damgasıyla ölçülür: kare anı → ilk ses. Hedef p95 ≤ 300 ms (cihaz üstü), 60 s yürüyüşte konuşma ≤ 12.

## Mesafe ölçümü

20 sahne, lazer metreyle 1–4 m. Nesne boyu yönteminde insan ve araç için ortalama mutlak yüzde hata ≤ %20 hedef. Sonuç README tablosuna.
