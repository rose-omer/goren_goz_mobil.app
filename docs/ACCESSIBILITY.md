# Erişilebilirlik ve arayüz

## İlkeler

- Ses önce, haptik ikinci, görüntü üçüncü. Görüntü gören yardımcı ve jüri içindir.
- Her denetim TalkBack ile bulunur, adı Türkçe okunur, tek dokunuşla (TalkBack'te çift dokunuşla) çalışır.
- Dokunma alanı ≥ 48×48 dp. Yürüyüş ekranındaki her bant ekran yüksekliğinin ≥ %20'si.
- Renk tek başına anlam taşımaz: seviye metinle ("Dur", "Dikkat"), ikon biçimiyle, sesle ve titreşimle de verilir.
- Hareket ve yanıp sönme yok. Sayfa geçişi anında.
- Metin sistem yazı ölçeğine uyar. %200 ölçekte metin önce satır kırar, sığmazsa küçülür; kırpılmaz.

## Tasarım tokenleri (`mobile_app/lib/theme/app_theme.dart`)

| Token | Siyah-sarı (varsayılan) | Beyaz-siyah | Kullanım |
|---|---|---|---|
| ground | #000000 | #FFFFFF | Zemin |
| ink | #FFD600 (14.9:1) | #000000 (21:1) | Bant etiketi, kenar, başlık |
| inkMuted | #F3ECCB (17:1) | #3D3A30 (11:1) | Açıklama metni |
| danger / onDanger | #FF7A66 / #000000 (8.2:1) | #A51C12 / #FFFFFF (7.6:1) | "Dur" şeridi |
| near / onNear | #FFD600 / #000000 | #FFD600 / #000000 | "Dikkat" şeridi |
| focus | #FFFFFF | #0050C8 | Klavye ve anahtar erişimi odak kenarı (4 dp) |

Tip ölçeği (sp): bant 30, durum 26, başlık 28, gövde 24, küçük 20. Aralık: 4, 8, 16, 24, 32. Köşe 12, kenar 2.

Yazı tipi: sistem fontu (Android'de Roboto). Çalışma anında font indirilmez.

## Ekranlar

1. **Açılış:** "Gören Göz'e hoş geldiniz. Kamera izni gerekiyor. Ekranın alt yarısına dokunun." Alt %40 tek düğme. Ret: "İzin olmadan çalışamam. Ayarları açmak için dokunun." → sistem ayarları. İzin sonrası güvenlik uyarısı ve kullanım turu bir kez okunur.
2. **Yürüyüş:** üstte durum şeridi (`liveRegion`), altta dört bant:
   - Durumu söyle: sahne özeti ve son 2 dakikadaki cevap.
   - Soru sor: basılı tut, konuş, bırak. Kısa dokunuş ya da TalkBack çift dokunuşu: dinleme başlar, ikinci dokunuş gönderir.
   - Duraklat / Devam et: durum sesle söylenir.
   - Ayarlar: sunucu yoksa "Sunucu adresi gerekli." ek satırı.
3. **Soru akışı:** yükselen bip + kısa titreşim, "Dinliyorum." (mikrofon açıkken TTS susar). Bırakınca alçalan bip, "Soruyorum.", beklerken 2 s'de bir tık. Cevap TTS ile; ardından "Tekrar dinlemek için Durumu söyle bandına dokunun." Hata: "Cevap alınamadı. Tehlike uyarıları açık."
4. **Ayarlar:** konuşma hızı (ekran okuyucu: "Konuşma hızı yüzde 60"), ses, titreşim, yön anlatımı, ayrıntı düzeyi, sunucu adresi ve anahtarı ("Kaydet ve dene"), sunucu analizi, yardımcı görünümü, beyaz tema, kullanım turu ve güvenlik uyarısını tekrar dinleme.
5. **Yardımcı görünümü:** kamera, kutular, Türkçe etiket, bölge çizgileri, FPS ve gecikme. Bantlar 2×2 ızgaraya geçer.

## TalkBack

- Algılama: `MediaQuery.accessibleNavigationOf(context)`.
- TalkBack açıkken bilgi mesajı TTS'e gitmez; durum şeridindeki `liveRegion` metni değişir, TalkBack okur.
- DANGER ve NEAR her zaman `flutter_tts` ile; TTS navigasyon ses özniteliğiyle kısa ses odağı ister.
- Android duyuru olayları kullanımdan kalktığı için `SemanticsService` duyurusu yerine `liveRegion` kullanılır.
- `MaterialApp.locale = tr_TR`; ekran okuyucu sesi de Türkçe.

## Haptik (`vibration`, ms)

| Olay | Desen | Genlik |
|---|---|---|
| DANGER | 0, 120, 60, 120, 60, 120; seviye sürdükçe 1.5 s'de bir | 255 |
| NEAR | 0, 80, 120, 80 | 180 |
| Bilgi | 0, 40 | 100 |
| Dinleme başladı | 0, 30 | 120 |
| Cevap geldi | 0, 30, 80, 30 | 120 |
| Bağlantı koptu | 0, 300 | 200 |

## Ses (`assets/sounds/`)

`danger.wav` 1000 Hz 3×80 ms · `near.wav` 750 Hz 2×80 ms · `info.wav` 500 Hz 40 ms · `listen_start.wav` 600→900 Hz · `listen_end.wav` 900→600 Hz · `tick.wav` 12 ms. Hepsi 4 ms atak, 8 ms bırakma ile tık sesi vermez.

## Açık işler

- Stereo yön sesi (kulaklıkta sol/sağ kanal): `audioplayers` denge API'si doğrulanmadı.
- iOS ve VoiceOver: `ios/` klasörü yok.
- Gömülü, düşük görüşe uygun yazı tipi (ör. Atkinson Hyperlegible) eklenmedi; dosya indirme gerekiyor.
