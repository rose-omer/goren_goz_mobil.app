// Testler için sahte servisler. Kamera, ağ, TTS ve titreşim kullanılmaz.

import 'dart:async';
import 'dart:typed_data';

import 'package:camera/camera.dart';
import 'package:goren_goz_mobil/app.dart';
import 'package:goren_goz_mobil/core/speech_queue.dart';
import 'package:goren_goz_mobil/perception/frame_source.dart';
import 'package:goren_goz_mobil/services/api_client.dart';
import 'package:goren_goz_mobil/services/feedback.dart';
import 'package:goren_goz_mobil/services/settings_store.dart';
import 'package:goren_goz_mobil/services/speech_input.dart';
import 'package:shared_preferences/shared_preferences.dart';

class FakeSpeaker implements Speaker {
  final List<String> spoken = [];
  int stops = 0;

  /// `true` iken [speak] [finishCurrent] çağrılana kadar bekler.
  bool hold = false;
  Completer<void>? _current;

  @override
  Future<void> speak(String text) {
    spoken.add(text);
    if (!hold) return Future.value();
    _current = Completer<void>();
    return _current!.future;
  }

  void finishCurrent() => _current?.complete();

  @override
  Future<void> stop() async {
    stops += 1;
    if (!(_current?.isCompleted ?? true)) _current!.complete();
  }
}

class FakeHaptics implements Haptics {
  final List<HapticPattern> played = [];

  @override
  Future<void> play(HapticPattern pattern) async => played.add(pattern);
}

class FakeSounds implements Sounds {
  final List<Cue> played = [];

  @override
  Future<void> play(Cue cue) async => played.add(cue);
}

class FakeSpeechInput implements SpeechInput {
  String nextQuestion = 'Önümde ne var?';
  ListenFailure? failure;
  bool listening = false;

  @override
  Future<ListenFailure?> start() async {
    if (failure != null) return failure;
    listening = true;
    return null;
  }

  @override
  Future<String> finish() async {
    listening = false;
    return nextQuestion;
  }

  @override
  Future<void> cancel() async => listening = false;
}

class FakePermissions implements PermissionGate {
  bool grant = true;
  int opened = 0;

  @override
  Future<bool> cameraGranted() async => grant;

  @override
  Future<bool> requestCamera() async => grant;

  @override
  Future<void> openSettings() async => opened += 1;
}

class FakeFrameSource implements FrameSource {
  Future<void> Function(EncodedFrame frame)? _onFrame;
  bool started = false;
  bool disposed = false;

  static final frame = EncodedFrame(Uint8List.fromList(const [0xff, 0xd8, 0xff, 0xd9]), 480, 640);

  @override
  bool get isReady => started;

  @override
  CameraController? get controller => null;

  @override
  Future<void> start(Future<void> Function(EncodedFrame frame) onFrame) async {
    _onFrame = onFrame;
    started = true;
  }

  @override
  Future<void> stop() async => started = false;

  @override
  Future<EncodedFrame?> latest() async => frame;

  @override
  Future<void> dispose() async => disposed = true;

  Future<void> emit() async => _onFrame?.call(frame);
}

class FakeApi implements AnalysisApi {
  final List<FrameAnalysis> queue = [];
  ApiFailure? failure;
  ApiFailure? askFailure;
  String answer = 'Önünüzde bir kapı var.';
  final List<String> questions = [];
  bool healthy = true;

  @override
  Future<FrameAnalysis> analyze(Uint8List jpeg, {required int width, required int height, double? focalPx}) async {
    if (failure != null) throw failure!;
    return queue.isNotEmpty ? queue.removeAt(0) : analysis();
  }

  @override
  Future<AskResult> ask(Uint8List jpeg, String question) async {
    questions.add(question);
    if (askFailure != null) throw askFailure!;
    return AskResult(answer, 120);
  }

  @override
  Future<bool> health() async => healthy;
}

/// Sunucu yanıtı biçiminde analiz üretir.
FrameAnalysis analysis({
  List<Map<String, dynamic>> objects = const [],
  bool withRegions = true,
  double centerCloseArea = 0,
  bool detectorOk = true,
}) {
  return FrameAnalysis.fromJson(
    {
      'success': true,
      'processing_time_ms': 42.0,
      'data': {
        'alert_level': 'CLEAR',
        'raw_level': 'CLEAR',
        'message': '',
        'detector_ok': detectorOk,
        'objects': objects,
        'regions': withRegions
            ? {
                'left': {'proximity': 0.2, 'close_area': 0.0, 'label': 'uzak'},
                'center': {
                  'proximity': centerCloseArea > 0 ? 0.95 : 0.2,
                  'close_area': centerCloseArea,
                  'label': centerCloseArea > 0 ? 'çok yakın' : 'uzak',
                },
                'right': {'proximity': 0.2, 'close_area': 0.0, 'label': 'uzak'},
              }
            : null,
      },
    },
    width: 480,
    height: 640,
  );
}

Map<String, dynamic> person({String region = 'center', double? ttc, double? distance, String trackId = 't1'}) => {
  'name': 'person',
  'name_tr': 'insan',
  'confidence': 0.9,
  'bbox': [100.0, 100.0, 200.0, 500.0],
  'center': [150.0, 300.0],
  'priority': 10,
  'region': region,
  'track_id': trackId,
  'is_approaching': ttc != null,
  'distance_m': distance,
  'ttc_s': ttc,
};

class TestHarness {
  TestHarness._(
    this.services,
    this.speaker,
    this.haptics,
    this.sounds,
    this.speechInput,
    this.permissions,
    this.frames,
    this.api,
  );

  final AppServices services;
  final FakeSpeaker speaker;
  final FakeHaptics haptics;
  final FakeSounds sounds;
  final FakeSpeechInput speechInput;
  final FakePermissions permissions;
  final FakeFrameSource frames;
  final FakeApi api;

  SettingsStore get settings => services.settings;

  static Future<TestHarness> create({Map<String, Object> prefs = const {}}) async {
    SharedPreferences.setMockInitialValues(prefs);
    final settings = await SettingsStore.load();
    final speaker = FakeSpeaker();
    final haptics = FakeHaptics();
    final sounds = FakeSounds();
    final speechInput = FakeSpeechInput();
    final permissions = FakePermissions();
    final frames = FakeFrameSource();
    final api = FakeApi();
    final services = AppServices(
      settings: settings,
      speaker: speaker,
      haptics: haptics,
      sounds: sounds,
      speechInput: speechInput,
      permissions: permissions,
      frameSourceFactory: () => frames,
      apiFactory: (s) => s.hasServer ? api : null,
    );
    return TestHarness._(services, speaker, haptics, sounds, speechInput, permissions, frames, api);
  }
}

const serverPrefs = <String, Object>{'server_url': 'http://192.168.1.20:8110', 'api_key': 'anahtar', 'onboarded': true};
