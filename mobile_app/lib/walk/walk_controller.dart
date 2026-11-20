// Yürüyüş döngüsü: kare → analiz → uyarı motoru → ses, haptik, konuşma.
// Ses önce, haptik ikinci, görüntü üçüncü (plan 5.1).

import 'dart:async';

import 'package:material_ui/material_ui.dart';

import '../core/hazard_engine.dart';
import '../core/scene_summary.dart';
import '../core/speech_queue.dart';
import '../perception/frame_source.dart';
import '../services/api_client.dart';
import '../services/feedback.dart';
import '../services/settings_store.dart';
import '../services/speech_input.dart';
import '../utils/logger.dart';

enum WalkStatus { starting, running, paused, needsServer, detectionOff, offline, cameraError }

enum AskState { idle, listening, asking }

class WalkController extends ChangeNotifier {
  WalkController({
    required this.settings,
    required this.frames,
    required this.apiProvider,
    required this.speech,
    required this.haptics,
    required this.sounds,
    required this.speechInput,
    HazardEngine? engine,
  }) : engine = engine ?? HazardEngine();

  final SettingsStore settings;
  final FrameSource frames;
  final AnalysisApi? Function() apiProvider;

  /// Ayardaki sunucu değişince yeni istemci gelir; bu yüzden her çağrıda sorulur.
  AnalysisApi? get api => apiProvider();
  final SpeechQueue speech;
  final Haptics haptics;
  final Sounds sounds;
  final SpeechInput speechInput;
  final HazardEngine engine;

  static const dangerRepeat = Duration(milliseconds: 1500);

  /// Bu kadar ardışık zaman aşımı "bağlantı koptu" sayılır. Bağlantı hatası hemen sayılır.
  static const offlineAfterTimeouts = 2;
  static const askTick = Duration(seconds: 2);

  WalkStatus status = WalkStatus.starting;
  AskState askState = AskState.idle;
  HazardResult hazard = HazardResult.idle;
  FrameAnalysis? lastAnalysis;
  String? lastAnswer;
  DateTime? _lastAnswerAt;

  /// Ekranda görünen durum satırı.
  String statusLine = 'Başlatılıyor.';

  /// Ekran okuyucunun okuduğu satır (liveRegion).
  String liveMessage = 'Başlatılıyor.';

  /// Uçtan uca gecikme: kare kodlandı → cevap işlendi (ms).
  double? latencyMs;
  double fps = 0;

  /// TalkBack açıkken bilgi mesajları liveRegion'a gider, TTS'e gitmez (plan 5.3).
  bool screenReaderOn = false;

  Timer? _dangerTimer;
  Timer? _tickTimer;
  bool _disposed = false;
  int _frameCount = 0;
  DateTime _fpsWindow = DateTime.now();
  bool _wasOffline = false;
  int _timeouts = 0;
  bool _detectorDown = false;

  bool get isPaused => status == WalkStatus.paused;
  bool get isRunning => status == WalkStatus.running || status == WalkStatus.offline;

  Future<void> start() async {
    if (!settings.serverAnalysis) {
      _setStatus(WalkStatus.detectionOff, 'Algılama kapalı. Ayarlardan sunucu analizini açın.');
      return;
    }
    if (api == null || !settings.hasServer) {
      _setStatus(WalkStatus.needsServer, 'Sunucu adresi gerekli. Ayarlar bandından girin.', speak: true);
      return;
    }
    try {
      await frames.start(_onFrame);
      _setStatus(WalkStatus.running, 'Algılama açık.');
    } on Exception catch (error) {
      AppLogger.error('Kamera açılamadı', error);
      _setStatus(WalkStatus.cameraError, 'Kamera açılamadı. Uygulamayı yeniden başlatın.', speak: true);
    }
  }

  Future<void> togglePause() async => isPaused ? resume() : pause();

  Future<void> pause({bool announce = true}) async {
    await frames.stop();
    _stopDangerRepeat();
    engine.reset();
    hazard = HazardResult.idle;
    await speech.clear();
    _setStatus(WalkStatus.paused, 'Algılama duraklatıldı.', speak: announce, force: announce);
  }

  Future<void> resume({bool announce = true}) async {
    _setStatus(WalkStatus.starting, 'Algılama devam ediyor.', speak: announce, force: announce);
    await start();
  }

  /// Uygulama arka plana geçti: kamerayı bırak (plan M8).
  Future<void> suspend() async {
    _stopDangerRepeat();
    await frames.stop();
    await frames.dispose();
  }

  Future<void> sayStatus() async {
    final analysis = lastAnalysis;
    final summary = switch (status) {
      WalkStatus.running || WalkStatus.offline when analysis != null => sceneSummary(
        hazard: hazard,
        objects: [for (final o in analysis.objects) SceneObject(o.nameTr, o.region)],
        depthKnown: analysis.regions != null,
        detectorOk: analysis.detectorOk,
        style: settings.directionStyle,
      ),
      _ => statusLine,
    };
    final answerAt = _lastAnswerAt;
    final recentAnswer = answerAt != null && DateTime.now().difference(answerAt) < const Duration(minutes: 2)
        ? lastAnswer
        : null;
    final text = recentAnswer == null ? summary : '$summary Son cevap: $recentAnswer';
    speech.enqueue(text, AlertLevel.info, key: 'durum', force: true);
  }

  Future<void> beginQuestion() async {
    if (askState != AskState.idle) return;
    final failure = await speechInput.start();
    if (failure != null) {
      final message = switch (failure) {
        ListenFailure.permissionDenied => 'Mikrofon izni yok. Soru sormak için izni ayarlardan açın.',
        ListenFailure.unavailable => 'Bu cihazda konuşma tanıma yok.',
        ListenFailure.nothingHeard => 'Soru duyulamadı. Tekrar deneyin.',
      };
      _announce(message, force: true);
      return;
    }
    askState = AskState.listening;
    unawaited(sounds.play(Cue.listenStart));
    unawaited(haptics.play(HapticPattern.listenStart));
    // Mikrofon açıkken TTS konuşmaz; durum yalnız ekrana ve ekran okuyucuya yazılır.
    _publish('Dinliyorum.', spokenByTts: false);
  }

  Future<void> finishQuestion() async {
    if (askState != AskState.listening) return;
    final question = await speechInput.finish();
    unawaited(sounds.play(Cue.listenEnd));
    if (question.isEmpty) {
      askState = AskState.idle;
      _announce('Soru duyulamadı. Tekrar deneyin.', force: true);
      return;
    }
    await ask(question);
  }

  Future<void> cancelQuestion() async {
    if (askState == AskState.listening) await speechInput.cancel();
    askState = AskState.idle;
    _notify();
  }

  Future<void> ask(String question) async {
    final client = api;
    if (client == null || !settings.hasServer) {
      askState = AskState.idle;
      _announce('Soru sorma şu an kullanılamıyor. Tehlike uyarıları açık.', force: true);
      return;
    }
    askState = AskState.asking;
    _announce('Soruyorum.', force: true);
    _tickTimer = Timer.periodic(askTick, (_) => unawaited(sounds.play(Cue.tick)));
    try {
      final frame = await frames.latest();
      if (frame == null) throw const ApiFailure('NO_FRAME', 'Kamera karesi yok.');
      final result = await client.ask(frame.jpeg, question);
      lastAnswer = result.answer;
      _lastAnswerAt = DateTime.now();
      unawaited(haptics.play(HapticPattern.answer));
      _announce('${result.answer} Tekrar dinlemek için Durumu söyle bandına dokunun.', force: true);
    } on ApiFailure catch (failure) {
      AppLogger.warning('Soru başarısız: ${failure.code}');
      _announce('Cevap alınamadı. Tehlike uyarıları açık.', force: true);
    } finally {
      _tickTimer?.cancel();
      _tickTimer = null;
      askState = AskState.idle;
      _notify();
    }
  }

  Future<void> _onFrame(EncodedFrame frame) async {
    final client = api;
    if (client == null || isPaused || _disposed) return;
    final watch = Stopwatch()..start();
    try {
      final analysis = await client.analyze(
        frame.jpeg,
        width: frame.width,
        height: frame.height,
        focalPx: settings.focalPx,
      );
      if (isPaused || _disposed) return;
      latencyMs = watch.elapsedMilliseconds.toDouble();
      _timeouts = 0;
      _countFrame();
      if (_wasOffline) {
        _wasOffline = false;
        status = WalkStatus.running;
        _announce('Bağlantı geri geldi.');
      }
      lastAnalysis = analysis;
      _noteDetector(analysis.detectorOk);
      _applyHazard(
        engine.process(
          [for (final o in analysis.objects) o.toPerceived()],
          analysis.regions,
          detectorOk: analysis.detectorOk,
          style: settings.directionStyle,
        ),
      );
    } on ApiFailure catch (failure) {
      // Yavaş tek kare (ısınma, ağ dalgalanması) kopma sayılmaz.
      if (failure.code == 'TIMEOUT' && !_wasOffline && ++_timeouts < offlineAfterTimeouts) return;
      if (failure.isOffline && !_wasOffline) {
        _wasOffline = true;
        status = WalkStatus.offline;
        _stopDangerRepeat();
        unawaited(haptics.play(HapticPattern.disconnected));
        _announce('Bağlantı koptu. Uyarılar şu an çalışmıyor.', level: AlertLevel.near, force: true);
      } else if (failure.code == 'UNAUTHORIZED') {
        await frames.stop();
        _setStatus(WalkStatus.needsServer, failure.message, speak: true);
      }
    }
  }

  /// Sunucuda tespit modeli yoksa bir kez söyler: boş nesne listesi güven vermesin.
  void _noteDetector(bool ok) {
    if (ok != _detectorDown) return;
    _detectorDown = !ok;
    if (ok) {
      _announce('Nesne tespiti yeniden çalışıyor.');
    } else {
      _announce(
        'Sunucuda nesne tespiti çalışmıyor. Yalnız önde engel uyarısı var.',
        level: AlertLevel.near,
        force: true,
      );
    }
  }

  void _applyHazard(HazardResult next) {
    final previous = hazard.level;
    hazard = next;
    if (next.level != previous) {
      final cue = Cue.forLevel(next.level);
      final pattern = HapticPattern.forLevel(next.level);
      if (cue != null && next.level > previous) unawaited(sounds.play(cue));
      if (pattern != null && next.level > previous) unawaited(haptics.play(pattern));
      next.level == AlertLevel.danger ? _startDangerRepeat() : _stopDangerRepeat();
    }
    final important = next.level == AlertLevel.danger || next.level == AlertLevel.near;
    final text = next.message.isEmpty ? next.level.label : next.message;
    if (next.message.isNotEmpty && important) {
      // Tehlike her zaman TTS ile; TalkBack konuşmasını keser (plan 5.3).
      speech.enqueue(next.message, next.level, key: next.top?.speechKey ?? next.message);
      _publish(text, spokenByTts: true);
    } else if (next.message.isNotEmpty && !screenReaderOn && settings.verbosity == Verbosity.all) {
      speech.enqueue(next.message, next.level, key: next.top?.speechKey ?? next.message);
      _publish(text, spokenByTts: true);
    } else {
      _publish(text, spokenByTts: false, onlyIfChanged: true);
    }
  }

  void _startDangerRepeat() {
    _dangerTimer ??= Timer.periodic(dangerRepeat, (_) => unawaited(haptics.play(HapticPattern.danger)));
  }

  void _stopDangerRepeat() {
    _dangerTimer?.cancel();
    _dangerTimer = null;
  }

  void _countFrame() {
    _frameCount += 1;
    final elapsed = DateTime.now().difference(_fpsWindow);
    if (elapsed >= const Duration(seconds: 2)) {
      fps = _frameCount * 1000 / elapsed.inMilliseconds;
      _frameCount = 0;
      _fpsWindow = DateTime.now();
    }
  }

  void _setStatus(WalkStatus next, String line, {bool speak = false, bool force = false}) {
    status = next;
    _announce(line, force: force, silent: !speak);
  }

  /// Bilgi mesajı. TalkBack açıksa liveRegion'a yazılır ve ekran okuyucu okur; TTS susar.
  /// [force] mesajı TalkBack açıkken de TTS ile okutur (soru cevabı gibi).
  void _announce(String text, {AlertLevel level = AlertLevel.info, bool force = false, bool silent = false}) {
    final important = level == AlertLevel.danger || level == AlertLevel.near;
    final useTts = !silent && (!screenReaderOn || important || force);
    if (useTts) speech.enqueue(text, level, key: text, force: force);
    _publish(text, spokenByTts: useTts);
  }

  /// [statusLine] ekranda görünür. [liveMessage] yalnız TTS okumadığında değişir; böylece
  /// TalkBack ile uygulama sesi aynı cümleyi üst üste okumaz (plan M5).
  void _publish(String text, {required bool spokenByTts, bool onlyIfChanged = false}) {
    if (!(onlyIfChanged && text == statusLine)) {
      statusLine = text;
      if (!spokenByTts) liveMessage = text;
    }
    _notify();
  }

  void _notify() {
    if (!_disposed) notifyListeners();
  }

  @override
  void dispose() {
    _disposed = true;
    _stopDangerRepeat();
    _tickTimer?.cancel();
    unawaited(frames.dispose());
    super.dispose();
  }
}
