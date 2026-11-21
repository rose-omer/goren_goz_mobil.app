# Gören Göz mobil

Flutter 3.50.1 / Dart 3.14. `package:material_ui` (Flutter 3.50 `material.dart` geçişi).

```powershell
C:\src\flutter\bin\flutter.bat pub get
C:\src\flutter\bin\flutter.bat analyze
C:\src\flutter\bin\flutter.bat test
C:\src\flutter\bin\flutter.bat run
```

## Dizinler

| Dizin | İçerik |
|---|---|
| `lib/core/` | Uyarı motoru, konuşma kuyruğu, sahne özeti (saf Dart, testli) |
| `lib/perception/` | Kamera kare kaynağı, YUV → JPEG, nesne boyuyla mesafe |
| `lib/walk/` | Yürüyüş döngüsü denetleyicisi |
| `lib/services/` | Sunucu istemcisi, ayarlar, TTS, ses, titreşim, konuşma tanıma |
| `lib/screens/`, `lib/widgets/` | Açılış, yürüyüş, ayarlar; bant düğmesi, durum şeridi, tespit katmanı |
| `lib/theme/` | Tasarım tokenleri ve tema |
| `assets/sounds/` | Uyarı sesleri (üretilmiş, küçük WAV) |
| `assets/models/` | Cihaz üstü modeller (git dışında) |

Release imzası: `android/key.properties` (repoya girmez).

Sunucu adresi:

- Debug: yerel ağ IP'sine düz HTTP (`http://192.168.x.x:8110`) ya da HTTPS.
- Release ve profile: yalnız HTTPS. `network_security_config.xml` düz HTTP'yi işletim sistemi düzeyinde kapatır; Android IP aralığı için istisna tanımlayamaz. Ayarlar ekranı `http://` adresini kaydetmez ve nedenini alan altında söyler.

Arayüz ayrıntısı: `../docs/ACCESSIBILITY.md`.
