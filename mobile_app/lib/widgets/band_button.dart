// Tam genişlik bant düğmesi. TalkBack tek öğe olarak okur: ad + ipucu (plan 5.2).

import 'package:material_ui/material_ui.dart';

import '../theme/app_theme.dart';
import 'floor_fit_text.dart';

class BandButton extends StatefulWidget {
  const BandButton({
    super.key,
    required this.label,
    required this.hint,
    required this.icon,
    this.onTap,
    this.onPressStart,
    this.onPressEnd,
    this.active = false,
    this.detail,
    this.compact = false,
  });

  final String label;
  final String hint;
  final IconData icon;
  final VoidCallback? onTap;

  /// Basılı tutma akışı (Soru sor). Verilirse [onTap] yerine bunlar kullanılır.
  final VoidCallback? onPressStart;
  final ValueChanged<Duration>? onPressEnd;

  /// Etkin durum (dinliyor, duraklatıldı): dolgu tersine döner.
  final bool active;

  /// Etiketin altında küçük ek satır (ör. "Dinliyorum").
  final String? detail;

  /// Yardımcı görünümündeki yarım genişlik bant: ikon üstte, metin altta.
  final bool compact;

  @override
  State<BandButton> createState() => _BandButtonState();
}

class _BandButtonState extends State<BandButton> {
  bool _pressed = false;
  bool _focused = false;
  DateTime? _downAt;

  bool get _holdMode => widget.onPressStart != null;

  void _down() {
    setState(() => _pressed = true);
    _downAt = DateTime.now();
    if (_holdMode) widget.onPressStart!();
  }

  void _up() {
    setState(() => _pressed = false);
    if (_holdMode) {
      final held = _downAt == null ? Duration.zero : DateTime.now().difference(_downAt!);
      widget.onPressEnd?.call(held);
    } else {
      widget.onTap?.call();
    }
  }

  void _cancel() {
    if (!_pressed) return;
    setState(() => _pressed = false);
    if (_holdMode) widget.onPressEnd?.call(Duration.zero);
  }

  /// Klavye, anahtar erişimi ve TalkBack çift dokunuşu tek dokunuş sayılır.
  void _activate() {
    if (_holdMode) {
      widget.onPressStart!();
      widget.onPressEnd?.call(Duration.zero);
    } else {
      widget.onTap?.call();
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = Palette.of(context);
    final background = widget.active ? p.ink : (_pressed ? p.pressed : p.ground);
    final foreground = widget.active ? p.ground : p.ink;
    final detail = widget.detail;

    return Semantics(
      button: true,
      label: detail == null ? widget.label : '${widget.label}. $detail',
      hint: widget.hint,
      onTap: _activate,
      excludeSemantics: true,
      child: FocusableActionDetector(
        onShowFocusHighlight: (value) => setState(() => _focused = value),
        actions: {ActivateIntent: CallbackAction<ActivateIntent>(onInvoke: (_) => _activate())},
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTapDown: (_) => _down(),
          onTapUp: (_) => _up(),
          onTapCancel: _cancel,
          child: Container(
            constraints: const BoxConstraints(minHeight: 96),
            padding: widget.compact
                ? const EdgeInsets.all(Space.s)
                : const EdgeInsets.symmetric(horizontal: Space.l, vertical: Space.m),
            decoration: BoxDecoration(
              color: background,
              borderRadius: BorderRadius.circular(Shape.radius),
              border: Border.all(color: _focused ? p.focus : p.edge, width: _focused ? Shape.focusEdge : Shape.edge),
            ),
            child: widget.compact
                ? Column(
                    children: [
                      Icon(widget.icon, size: 36, color: foreground),
                      const SizedBox(height: Space.s),
                      Expanded(child: _texts(context, foreground, center: true)),
                    ],
                  )
                : Row(
                    children: [
                      Icon(widget.icon, size: 44, color: foreground),
                      const SizedBox(width: Space.l),
                      Expanded(child: _texts(context, foreground, center: false)),
                    ],
                  ),
          ),
        ),
      ),
    );
  }

  /// Büyük yazı ölçeğinde önce satır kırılır, sonra küçülür; etiket 28 sp (yarım bantta 24 sp)
  /// altına inmez. Ek satır sığmazsa gizlenir; Semantics etiketinde kalır.
  Widget _texts(BuildContext context, Color foreground, {required bool center}) {
    final p = Palette.of(context);
    return FloorFitText(
      widget.label,
      align: center ? TextAlign.center : TextAlign.start,
      minSize: center ? TypeScale.body : TypeScale.buttonMin,
      style: TextStyle(
        fontSize: center ? TypeScale.body : TypeScale.band,
        fontWeight: FontWeight.w700,
        color: foreground,
        height: 1.1,
      ),
      secondary: widget.detail,
      secondaryStyle: TextStyle(
        fontSize: TypeScale.small,
        fontWeight: FontWeight.w600,
        color: widget.active ? p.ground : p.inkMuted,
      ),
    );
  }
}
