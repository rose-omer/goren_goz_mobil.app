// Yürüyüş ekranı (plan 5.2.2). Dört tam genişlik bant; her bant ekran yüksekliğinin en az %20'si.

import 'dart:async';

import 'package:camera/camera.dart';
import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';
import 'package:wakelock_plus/wakelock_plus.dart';

import '../app.dart';
import '../core/hazard_engine.dart';
import '../services/settings_store.dart';
import '../theme/app_theme.dart';
import '../utils/logger.dart';
import '../walk/walk_controller.dart';
import '../widgets/band_button.dart';
import '../widgets/detection_overlay.dart';
import '../widgets/status_strip.dart';

class WalkScreen extends StatefulWidget {
  const WalkScreen({super.key});

  @override
  State<WalkScreen> createState() => _WalkScreenState();
}

class _WalkScreenState extends State<WalkScreen> with WidgetsBindingObserver {
  late final AppServices _services = context.read<AppServices>();
  late final WalkController _controller = WalkController(
    settings: _services.settings,
    frames: _services.frameSourceFactory(),
    apiProvider: () => _services.apiFactory(_services.settings),
    speech: _services.speech,
    haptics: _services.haptics,
    sounds: _services.sounds,
    speechInput: _services.speechInput,
  );

  static const _holdThreshold = Duration(milliseconds: 500);
  Future<void>? _beginning;
  bool _startedThisPress = false;
  bool _tapToSend = false;
  bool _userPaused = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    unawaited(_keepScreenOn(true));
    unawaited(_controller.start());
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    unawaited(_keepScreenOn(false));
    _controller.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    switch (state) {
      case AppLifecycleState.paused:
        unawaited(_controller.suspend());
      case AppLifecycleState.resumed:
        // Ayarlar açıkken kamerayı başlatma; dönüşte resume() başlatır.
        final onTop = ModalRoute.of(context)?.isCurrent ?? true;
        if (!_userPaused && onTop) unawaited(_controller.start());
      default:
        break;
    }
  }

  Future<void> _keepScreenOn(bool on) async {
    try {
      await WakelockPlus.toggle(enable: on);
    } on Exception catch (error) {
      AppLogger.warning('Ekran açık tutulamadı: $error');
    }
  }

  void _onAskStart() {
    if (_controller.askState == AskState.listening && _tapToSend) {
      _startedThisPress = false;
      return;
    }
    if (_controller.askState != AskState.idle) return;
    _startedThisPress = true;
    _beginning = _controller.beginQuestion();
  }

  Future<void> _onAskEnd(Duration held) async {
    await _beginning;
    _beginning = null;
    if (_controller.askState != AskState.listening) return;
    if (_startedThisPress && held < _holdThreshold) {
      // Kısa dokunuş ya da TalkBack çift dokunuşu: dinleme sürer, ikinci dokunuş gönderir.
      setState(() => _tapToSend = true);
      return;
    }
    setState(() => _tapToSend = false);
    await _controller.finishQuestion();
  }

  Future<void> _togglePause() async {
    _userPaused = !_controller.isPaused;
    await _controller.togglePause();
  }

  Future<void> _openSettings() async {
    await _controller.pause(announce: false);
    if (!mounted) return;
    await Navigator.of(context).pushNamed(Routes.settings);
    if (!mounted) return;
    _userPaused = false;
    await _controller.resume(announce: false);
  }

  @override
  Widget build(BuildContext context) {
    _controller.screenReaderOn = MediaQuery.accessibleNavigationOf(context);
    final assistantView = context.select<SettingsStore, bool>((s) => s.assistantView);

    return Scaffold(
      body: SafeArea(
        child: ListenableBuilder(
          listenable: _controller,
          builder: (context, _) => Padding(
            padding: const EdgeInsets.all(Space.s),
            child: assistantView ? _assistantLayout(context) : _bandLayout(context),
          ),
        ),
      ),
    );
  }

  Widget _strip() =>
      StatusStrip(level: _controller.hazard.level, text: _controller.statusLine, liveMessage: _controller.liveMessage);

  List<Widget> _bands({bool compact = false}) {
    final c = _controller;
    final askDetail = switch (c.askState) {
      AskState.listening => _tapToSend ? 'Dinliyorum. Göndermek için tekrar dokunun.' : 'Dinliyorum. Bırakınca gider.',
      AskState.asking => 'Cevap bekleniyor.',
      AskState.idle => null,
    };
    final settingsDetail = switch (c.status) {
      WalkStatus.needsServer => 'Sunucu adresi gerekli.',
      WalkStatus.detectionOff => 'Algılama kapalı.',
      _ => null,
    };
    return [
      BandButton(
        label: 'Durumu söyle',
        compact: compact,
        hint: 'Son sahneyi okur.',
        icon: Icons.record_voice_over,
        onTap: c.sayStatus,
      ),
      BandButton(
        label: 'Soru sor',
        compact: compact,
        hint: 'Basılı tutup konuşun, bırakınca soru gider. Ya da dokunup konuşun, tekrar dokunup gönderin.',
        icon: Icons.mic,
        active: c.askState != AskState.idle,
        detail: askDetail,
        onPressStart: _onAskStart,
        onPressEnd: (held) => unawaited(_onAskEnd(held)),
      ),
      BandButton(
        label: c.isPaused ? 'Devam et' : 'Duraklat',
        compact: compact,
        hint: c.isPaused ? 'Algılamayı sürdürür.' : 'Algılamayı durdurur.',
        icon: c.isPaused ? Icons.play_arrow : Icons.pause,
        active: c.isPaused,
        detail: c.isPaused ? 'Algılama duraklatıldı.' : null,
        onTap: () => unawaited(_togglePause()),
      ),
      BandButton(
        label: 'Ayarlar',
        compact: compact,
        hint: 'Ses, titreşim ve sunucu ayarları.',
        icon: Icons.tune,
        detail: settingsDetail,
        onTap: () => unawaited(_openSettings()),
      ),
    ];
  }

  Widget _bandLayout(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final screen = MediaQuery.sizeOf(context).height;
        final bandHeight = (screen * 0.2).clamp(96.0, constraints.maxHeight / 4.6);
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Expanded(child: _strip()),
            for (final (i, band) in _bands().indexed) ...[
              const SizedBox(height: Space.s),
              SizedBox(key: ValueKey('bant-$i'), height: bandHeight, child: band),
            ],
          ],
        );
      },
    );
  }

  /// Gören yardımcı ve jüri için: önizleme, kutular, FPS ve gecikme (plan 5.2.5).
  Widget _assistantLayout(BuildContext context) {
    final bands = _bands(compact: true);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Expanded(flex: 5, child: _Preview(controller: _controller)),
        const SizedBox(height: Space.s),
        _strip(),
        const SizedBox(height: Space.s),
        Expanded(
          flex: 4,
          child: Column(
            children: [
              for (var row = 0; row < 2; row++) ...[
                if (row > 0) const SizedBox(height: Space.s),
                Expanded(
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Expanded(child: bands[row * 2]),
                      const SizedBox(width: Space.s),
                      Expanded(child: bands[row * 2 + 1]),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }
}

class _Preview extends StatelessWidget {
  const _Preview({required this.controller});

  final WalkController controller;

  @override
  Widget build(BuildContext context) {
    final p = Palette.of(context);
    final camera = controller.frames.controller;
    final metrics = [
      if (controller.fps > 0) 'FPS ${controller.fps.toStringAsFixed(1)}',
      if (controller.latencyMs != null) 'Gecikme ${controller.latencyMs!.round()} ms',
      if (controller.lastAnalysis != null) 'Sunucu ${controller.lastAnalysis!.serverMs.round()} ms',
    ].join(', ');
    final regions = controller.lastAnalysis?.regions;

    return ClipRRect(
      borderRadius: BorderRadius.circular(Shape.radius),
      child: DecoratedBox(
        decoration: BoxDecoration(
          border: Border.all(color: p.edge, width: Shape.edge),
        ),
        child: Stack(
          fit: StackFit.expand,
          children: [
            if (camera != null && camera.value.isInitialized)
              FittedBox(
                fit: BoxFit.cover,
                clipBehavior: Clip.hardEdge,
                child: SizedBox(
                  width: camera.value.previewSize?.height ?? 480,
                  height: camera.value.previewSize?.width ?? 640,
                  child: CameraPreview(camera),
                ),
              )
            else
              Center(
                child: Text(
                  'Kamera görüntüsü yok',
                  style: TextStyle(color: p.inkMuted, fontSize: TypeScale.small),
                ),
              ),
            DetectionOverlay(analysis: controller.lastAnalysis),
            Positioned(
              left: Space.s,
              right: Space.s,
              bottom: Space.s,
              child: ExcludeSemantics(
                child: Wrap(
                  spacing: Space.s,
                  runSpacing: Space.xs,
                  children: [
                    if (metrics.isNotEmpty) _Tag(metrics),
                    if (regions != null)
                      for (final r in Region.values)
                        if (regions[r] != null) _Tag('${directionWord(r, DirectionStyle.sides)}: ${regions[r]!.label}'),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Tag extends StatelessWidget {
  const _Tag(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    final p = Palette.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: Space.s, vertical: Space.xs),
      color: p.ground,
      child: Text(
        text,
        style: TextStyle(
          color: p.ink,
          fontSize: TypeScale.small,
          fontWeight: FontWeight.w600,
          fontFeatures: const [FontFeature.tabularFigures()],
        ),
      ),
    );
  }
}
