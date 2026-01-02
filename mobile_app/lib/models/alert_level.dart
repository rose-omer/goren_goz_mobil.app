///
/// Alert Level Enum
/// ================
///

enum AlertLevel {
  safe,
  far,
  medium,
  near,
  danger;
  
  String get displayName {
    switch (this) {
      case AlertLevel.safe:
        return 'GÜVENLİ';
      case AlertLevel.far:
        return 'UZAK';
      case AlertLevel.medium:
        return 'ORTA';
      case AlertLevel.near:
        return 'YAKIN';
      case AlertLevel.danger:
        return 'TEHLİKE';
    }
  }
  
  static AlertLevel fromString(String value) {
    switch (value.toUpperCase()) {
      case 'SAFE':
        return AlertLevel.safe;
      case 'FAR':
        return AlertLevel.far;
      case 'MEDIUM':
        return AlertLevel.medium;
      case 'NEAR':
        return AlertLevel.near;
      case 'DANGER':
        return AlertLevel.danger;
      default:
        return AlertLevel.safe;
    }
  }
}
