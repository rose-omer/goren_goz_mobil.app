// Açılış ve kamera izni (plan 5.2.1). Mikrofon izni burada istenmez; ilk soruda istenir (plan M11).

import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';

import '../app.dart';
import '../core/hazard_engine.dart';
import '../theme/app_theme.dart';
import 'texts.dart';

enum _Step { ask, denied, requesting }

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  _Step _step = _Step.ask;
  late final AppServices _services = context.read<AppServices>();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _greet());
  }

  void _greet() {
    if (!mounted) return;
    _services.speech.enqueue(Texts.welcome, AlertLevel.info, key: 'hosgeldin', force: true);
  }

  Future<void> _requestCamera() async {
    setState(() => _step = _Step.requesting);
    final granted = await _services.permissions.requestCamera();
    if (!mounted) return;
    if (!granted) {
      setState(() => _step = _Step.denied);
      _services.speech.enqueue(Texts.cameraDenied, AlertLevel.near, key: 'izin-yok', force: true);
      return;
    }
    final settings = _services.settings;
    if (!settings.safetyHeard) {
      _services.speech.enqueue('${Texts.safety} ${Texts.tour}', AlertLevel.info, key: 'tur', force: true);
      await settings.setSafetyHeard(true);
    }
    await settings.setOnboarded(true);
    if (!mounted) return;
    Navigator.of(context).pushReplacementNamed(Routes.walk);
  }

  @override
  Widget build(BuildContext context) {
    final p = Palette.of(context);
    final text = Theme.of(context).textTheme;
    final denied = _step == _Step.denied;

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(Space.l),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: Space.xl),
                      Semantics(
                        header: true,
                        child: Text(
                          'Gören Göz',
                          style: TextStyle(
                            fontSize: 44,
                            fontWeight: FontWeight.w800,
                            color: p.ink,
                            height: 1.05,
                            letterSpacing: -0.5,
                          ),
                        ),
                      ),
                      const SizedBox(height: Space.l),
                      Text(
                        'Kamera önünüzdeki engelleri bulur, sesle ve titreşimle haber verir.',
                        style: text.bodyLarge?.copyWith(color: p.ink),
                      ),
                      const SizedBox(height: Space.m),
                      Text(Texts.safety, style: text.bodyLarge),
                      if (denied) ...[
                        const SizedBox(height: Space.l),
                        Semantics(
                          liveRegion: true,
                          child: Text(Texts.cameraDenied, style: text.titleMedium?.copyWith(color: p.danger)),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              // Ekranın alt yarısı tek düğme: konum tarif etmek kolay (plan 5.2.1).
              SizedBox(
                height: MediaQuery.sizeOf(context).height * 0.4,
                child: FilledButton(
                  onPressed: switch (_step) {
                    _Step.requesting => null,
                    _Step.denied => _services.permissions.openSettings,
                    _Step.ask => _requestCamera,
                  },
                  style: FilledButton.styleFrom(
                    disabledBackgroundColor: p.pressed,
                    disabledForegroundColor: p.ink,
                    padding: const EdgeInsets.all(Space.l),
                  ),
                  child: Text(switch (_step) {
                    _Step.requesting => 'İzin bekleniyor',
                    _Step.denied => 'Ayarları aç',
                    _Step.ask => 'Kamera iznini ver',
                  }, textAlign: TextAlign.center),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
