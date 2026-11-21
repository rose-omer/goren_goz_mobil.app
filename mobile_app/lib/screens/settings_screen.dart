// Ayarlar (plan 5.2.4). Eşik kaydırıcıları yok (plan M9). Sunucu adresi kalıcı.

import 'dart:async';

import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';

import '../app.dart';
import '../core/hazard_engine.dart';
import '../services/feedback.dart';
import '../services/settings_store.dart';
import '../theme/app_theme.dart';
import 'texts.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final settings = context.watch<SettingsStore>();
    final services = context.read<AppServices>();

    Future<void> applyVoice() async {
      final speaker = services.speaker;
      if (speaker is TtsSpeaker) {
        await speaker.configure(rate: settings.speechRate, volume: settings.volume);
      }
    }

    void speakSample(String text) => services.speech.enqueue(text, AlertLevel.info, key: 'ornek', force: true);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Ayarlar'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, size: 32),
          tooltip: 'Yürüyüşe dön',
          onPressed: () => Navigator.of(context).maybePop(),
        ),
      ),
      body: SafeArea(
        top: false,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(Space.m, 0, Space.m, Space.xl),
          children: [
            const _Section('Ses ve titreşim'),
            _SliderRow(
              label: 'Konuşma hızı',
              value: settings.speechRate,
              min: 0.3,
              max: 1.0,
              onChanged: settings.setSpeechRate,
              onChangeEnd: (_) async {
                await applyVoice();
                speakSample('Konuşma hızı bu.');
              },
            ),
            _SliderRow(
              label: 'Ses düzeyi',
              value: settings.volume,
              min: 0.0,
              max: 1.0,
              onChanged: settings.setVolume,
              onChangeEnd: (_) async {
                await applyVoice();
                speakSample('Ses düzeyi bu.');
              },
            ),
            _SwitchRow(
              title: 'Titreşim',
              subtitle: 'Tehlikede üç kısa, yakın engelde iki titreşim.',
              value: settings.vibration,
              onChanged: (value) async {
                await settings.setVibration(value);
                if (value) unawaited(services.haptics.play(HapticPattern.near));
              },
            ),
            const _Section('Anlatım'),
            _ChoiceGroup<DirectionStyle>(
              title: 'Yön anlatımı',
              value: settings.directionStyle,
              onChanged: settings.setDirectionStyle,
              options: const {
                DirectionStyle.sides: ('Solda, önde, sağda', null),
                DirectionStyle.clock: ('Saat yönü', 'Saat 10, saat 12, saat 2'),
              },
            ),
            _ChoiceGroup<Verbosity>(
              title: 'Ne söylensin',
              value: settings.verbosity,
              onChanged: settings.setVerbosity,
              options: const {
                Verbosity.dangerOnly: ('Yalnız tehlike', 'Dur ve Dikkat uyarıları'),
                Verbosity.all: ('Tehlike ve bilgi', 'Yakındaki nesneler de söylenir'),
              },
            ),
            const _Section('Sunucu'),
            const _ServerForm(),
            _SwitchRow(
              title: 'Sunucu analizi',
              subtitle: 'Cihaz üstü model eklenene kadar engel algılama sunucuda yapılır.',
              value: settings.serverAnalysis,
              onChanged: settings.setServerAnalysis,
            ),
            const _Section('Görünüm'),
            _SwitchRow(
              title: 'Yardımcı görünümü',
              subtitle: 'Gören yardımcı için kamera görüntüsü, kutular ve gecikme.',
              value: settings.assistantView,
              onChanged: settings.setAssistantView,
            ),
            _SwitchRow(
              title: 'Beyaz tema',
              subtitle: 'Beyaz zemin, siyah yazı. Kapalıyken siyah zemin, sarı yazı.',
              value: settings.contrast == Contrast.lightInk,
              onChanged: (value) => settings.setContrast(value ? Contrast.lightInk : Contrast.darkSignal),
            ),
            const _Section('Yardım'),
            const SizedBox(height: Space.s),
            OutlinedButton.icon(
              onPressed: () => speakSample(Texts.tour),
              icon: const Icon(Icons.hearing, size: 28),
              label: const Text('Kullanım turunu dinle'),
            ),
            const SizedBox(height: Space.m),
            OutlinedButton.icon(
              onPressed: () => speakSample(Texts.safety),
              icon: const Icon(Icons.health_and_safety_outlined, size: 28),
              label: const Text('Güvenlik uyarısını dinle'),
            ),
          ],
        ),
      ),
    );
  }
}

class _Section extends StatelessWidget {
  const _Section(this.title);

  final String title;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: Space.xl, bottom: Space.s),
      child: Semantics(header: true, child: Text(title, style: Theme.of(context).textTheme.headlineSmall)),
    );
  }
}

class _SwitchRow extends StatelessWidget {
  const _SwitchRow({required this.title, required this.subtitle, required this.value, required this.onChanged});

  final String title;
  final String subtitle;
  final bool value;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return SwitchListTile(
      contentPadding: EdgeInsets.zero,
      value: value,
      onChanged: onChanged,
      title: Text(title, style: text.titleMedium),
      subtitle: Padding(
        padding: const EdgeInsets.only(top: Space.xs),
        child: Text(subtitle, style: text.bodySmall),
      ),
    );
  }
}

class _SliderRow extends StatelessWidget {
  const _SliderRow({
    required this.label,
    required this.value,
    required this.min,
    required this.max,
    required this.onChanged,
    required this.onChangeEnd,
  });

  final String label;
  final double value;
  final double min;
  final double max;
  final ValueChanged<double> onChanged;
  final ValueChanged<double> onChangeEnd;

  @override
  Widget build(BuildContext context) {
    final percent = (value * 100).round();
    final text = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.only(top: Space.m),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ExcludeSemantics(
            child: Row(
              children: [
                Expanded(child: Text(label, style: text.titleMedium)),
                Text(
                  'yüzde $percent',
                  style: text.bodySmall?.copyWith(fontFeatures: const [FontFeature.tabularFigures()]),
                ),
              ],
            ),
          ),
          Slider(
            value: value.clamp(min, max),
            min: min,
            max: max,
            divisions: ((max - min) * 10).round(),
            label: 'yüzde $percent',
            // Ekran okuyucu: "Konuşma hızı yüzde 60".
            semanticFormatterCallback: (v) => '$label yüzde ${(v * 100).round()}',
            onChanged: onChanged,
            onChangeEnd: onChangeEnd,
          ),
        ],
      ),
    );
  }
}

class _ChoiceGroup<T> extends StatelessWidget {
  const _ChoiceGroup({required this.title, required this.value, required this.onChanged, required this.options});

  final String title;
  final T value;
  final ValueChanged<T> onChanged;
  final Map<T, (String, String?)> options;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Padding(
      padding: const EdgeInsets.only(top: Space.m),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Semantics(header: true, child: Text(title, style: text.titleMedium)),
          RadioGroup<T>(
            groupValue: value,
            onChanged: (v) {
              if (v != null) onChanged(v);
            },
            child: Column(
              children: [
                for (final entry in options.entries)
                  RadioListTile<T>(
                    contentPadding: EdgeInsets.zero,
                    value: entry.key,
                    title: Text(entry.value.$1, style: text.bodyLarge),
                    subtitle: entry.value.$2 == null ? null : Text(entry.value.$2!, style: text.bodySmall),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

enum _Probe { idle, checking, ok, failed }

class _ServerForm extends StatefulWidget {
  const _ServerForm();

  @override
  State<_ServerForm> createState() => _ServerFormState();
}

class _ServerFormState extends State<_ServerForm> {
  final _formKey = GlobalKey<FormState>();
  late final SettingsStore _settings = context.read<SettingsStore>();
  late final TextEditingController _url = TextEditingController(text: _settings.serverUrl);
  late final TextEditingController _key = TextEditingController(text: _settings.apiKey);
  bool _showKey = false;
  _Probe _probe = _Probe.idle;

  @override
  void dispose() {
    _url.dispose();
    _key.dispose();
    super.dispose();
  }

  Future<void> _saveAndCheck() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    await _settings.setServerUrl(_url.text);
    await _settings.setApiKey(_key.text);
    if (!mounted) return;
    final api = context.read<AppServices>().apiFactory(_settings);
    setState(() => _probe = _Probe.checking);
    final ok = await api?.health() ?? false;
    if (!mounted) return;
    setState(() => _probe = ok ? _Probe.ok : _Probe.failed);
  }

  @override
  Widget build(BuildContext context) {
    final p = Palette.of(context);
    final text = Theme.of(context).textTheme;
    final (message, color) = switch (_probe) {
      _Probe.idle => (null, p.inkMuted),
      _Probe.checking => ('Bağlantı deneniyor.', p.inkMuted),
      _Probe.ok => ('Kaydedildi. Sunucu cevap veriyor.', p.ink),
      _Probe.failed => ('Kaydedildi ama sunucu cevap vermedi. Adresi ve ağı denetleyin.', p.danger),
    };

    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const SizedBox(height: Space.s),
          TextFormField(
            controller: _url,
            keyboardType: TextInputType.url,
            autocorrect: false,
            textInputAction: TextInputAction.next,
            style: text.bodyLarge?.copyWith(color: p.ink),
            decoration: InputDecoration(labelText: 'Sunucu adresi', helperText: serverUrlHelp(), helperMaxLines: 3),
            validator: (value) => validateServerUrl(value ?? ''),
          ),
          const SizedBox(height: Space.m),
          TextFormField(
            controller: _key,
            obscureText: !_showKey,
            autocorrect: false,
            enableSuggestions: false,
            style: text.bodyLarge?.copyWith(color: p.ink),
            decoration: InputDecoration(
              labelText: 'API anahtarı',
              helperText: 'Sunucudaki API_KEY değeri.',
              suffixIcon: IconButton(
                iconSize: 28,
                tooltip: _showKey ? 'Anahtarı gizle' : 'Anahtarı göster',
                icon: Icon(_showKey ? Icons.visibility_off : Icons.visibility),
                onPressed: () => setState(() => _showKey = !_showKey),
              ),
            ),
          ),
          const SizedBox(height: Space.m),
          FilledButton(
            onPressed: _probe == _Probe.checking ? null : _saveAndCheck,
            style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(64)),
            child: const Text('Kaydet ve dene', style: TextStyle(fontSize: TypeScale.body)),
          ),
          if (message != null) ...[
            const SizedBox(height: Space.s),
            Semantics(
              liveRegion: true,
              child: Text(
                message,
                style: text.bodySmall?.copyWith(color: color, fontWeight: FontWeight.w600),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
