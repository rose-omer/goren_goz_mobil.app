# Gören Göz Mobil - Flutter App

Flutter mobile application for real-time depth estimation and collision detection for visually impaired users.

## 🚀 Quick Start

### Prerequisites
- Flutter SDK 3.0+
- Android Studio / VS Code
- Android device or emulator (API 21+)

### Installation

1. **Install Flutter dependencies:**
```bash
cd mobile_app
flutter pub get
```

2. **Configure API URL:**
Edit `lib/utils/constants.dart`:
```dart
static const String defaultApiUrl = 'http://YOUR_SERVER_IP:8000';
```

3. **Run the app:**
```bash
flutter run
```

### Build APK

```bash
# Debug APK
flutter build apk --debug

# Release APK
flutter build apk --release
```

APK will be in: `build/app/outputs/flutter-apk/`

## 📱 Features

- **Real-time Camera Processing**: Captures frames at configurable FPS
- **API Integration**: Sends frames to backend for depth analysis
- **Visual Alerts**: Color-coded alert overlays (Red=Danger, Yellow=Warning)
- **Audio Alerts**: Sound notifications for danger situations
- **Statistics Display**: FPS, distance metrics, processing time
- **Settings**: Configurable API URL, sound toggle, frame rate

## 🎮 Usage

1. **Launch App**: Grant camera permissions
2. **Point Camera**: Aim at objects/obstacles
3. **Receive Alerts**: Visual (color overlay) and audio (beep) alerts
4. **View Stats**: Top-right info panel shows real-time metrics
5. **Adjust Settings**: Tap settings button to configure

## ⚙️ Configuration

### Settings Screen
- **API URL**: Backend server address
- **Sound Alerts**: Enable/disable audio warnings
- **Frame Rate**: 3, 5, or 10 FPS

### Performance Tips
- Use 5 FPS for balanced performance
- Lower FPS (3) for slower networks
- Higher FPS (10) for faster response (requires good connection)

## 📦 Dependencies

Key packages:
- `camera` - Camera access
- `dio` - HTTP client with retry
- `audioplayers` - Sound playback
- `provider` - State management
- `image` - Image compression

See `pubspec.yaml` for full list.

## 🏗️ Architecture

```
lib/
├── main.dart              # App entry point
├── screens/               # UI screens
│   ├── splash_screen.dart
│   ├── camera_screen.dart
│   └── settings_screen.dart
├── services/              # Business logic
│   ├── api_service.dart
│   └── sound_service.dart
├── models/                # Data models
│   ├── alert_level.dart
│   └── api_response.dart
├── widgets/               # Reusable widgets
│   ├── alert_overlay.dart
│   └── info_panel.dart
└── utils/                 # Utilities
    ├── constants.dart
    └── logger.dart
```

## 🔒 Permissions

Required permissions (auto-requested):
- **CAMERA**: Capture frames for analysis
- **INTERNET**: API communication

## 🐛 Troubleshooting

### Camera not working
- Check permissions in device settings
- Restart app after granting permissions

### Connection errors
- Verify backend is running
- Check API URL in settings
- Ensure device/emulator has network access
- Use `http://10.0.2.2:8000` for Android emulator (localhost alias)

### Sound not playing
- Check device volume
- Enable sound in settings
- Verify `assets/sounds/beep.mp3` exists

## 📝 Development

### Debug Mode
```bash
flutter run --debug
```

### Hot Reload
- Press `r` in terminal
- Or use IDE hot reload button

### Logs
```bash
flutter logs
```

## 🚢 Deployment

### Generate Release APK
```bash
flutter build apk --release --split-per-abi
```

### App Signing (Production)
1. Create keystore:
```bash
keytool -genkey -v -keystore goren-goz.jks -keyalg RSA -keysize 2048 -validity 10000 -alias goren-goz
```

2. Configure `android/key.properties`
3. Update `android/app/build.gradle`
4. Build signed APK

## 📄 License

Part of Gören Göz Mobil project.
MIT License.

## 🤝 Support

For issues, see main project repository or backend README.
