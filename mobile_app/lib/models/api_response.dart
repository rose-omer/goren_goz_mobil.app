///
/// API Response Models
/// ===================
///

import 'alert_level.dart';

class DistanceStats {
  final double min;
  final double max;
  final double avg;
  
  DistanceStats({
    required this.min,
    required this.max,
    required this.avg,
  });
  
  factory DistanceStats.fromJson(Map<String, dynamic> json) {
    return DistanceStats(
      min: (json['min'] as num).toDouble(),
      max: (json['max'] as num).toDouble(),
      avg: (json['avg'] as num).toDouble(),
    );
  }
}

class Warning {
  final String message;
  final String level;
  final double distance;
  final double areaPercentage;
  
  Warning({
    required this.message,
    required this.level,
    required this.distance,
    required this.areaPercentage,
  });
  
  factory Warning.fromJson(Map<String, dynamic> json) {
    return Warning(
      message: json['message'] as String,
      level: json['level'] as String,
      distance: (json['distance'] as num).toDouble(),
      areaPercentage: (json['area_percentage'] as num).toDouble(),
    );
  }
}

class DetectedObject {
  final String name;
  final String nameTr;
  final double confidence;
  final List<double> bbox;
  final List<double> center;
  final int priority;
  final String region;
  
  DetectedObject({
    required this.name,
    required this.nameTr,
    required this.confidence,
    required this.bbox,
    required this.center,
    required this.priority,
    required this.region,
  });
  
  factory DetectedObject.fromJson(Map<String, dynamic> json) {
    return DetectedObject(
      name: json['name'] as String,
      nameTr: json['name_tr'] as String,
      confidence: (json['confidence'] as num).toDouble(),
      bbox: (json['bbox'] as List).map((e) => (e as num).toDouble()).toList(),
      center: (json['center'] as List).map((e) => (e as num).toDouble()).toList(),
      priority: json['priority'] as int,
      region: json['region'] as String,
    );
  }
}

class RegionalAlert {
  final String alertLevel;
  final double minDistance;
  final double? avgDistance;
  final bool hasObstacle;
  final String message;
  final double? dangerPercentage;
  final double? nearPercentage;
  
  RegionalAlert({
    required this.alertLevel,
    required this.minDistance,
    this.avgDistance,
    required this.hasObstacle,
    required this.message,
    this.dangerPercentage,
    this.nearPercentage,
  });
  
  factory RegionalAlert.fromJson(Map<String, dynamic> json) {
    return RegionalAlert(
      alertLevel: json['alert_level'] as String,
      minDistance: (json['min_distance'] as num).toDouble(),
      avgDistance: json['avg_distance'] != null 
          ? (json['avg_distance'] as num).toDouble() 
          : null,
      hasObstacle: json['has_obstacle'] as bool,
      message: json['message'] as String,
      dangerPercentage: json['danger_percentage'] != null
          ? (json['danger_percentage'] as num).toDouble()
          : null,
      nearPercentage: json['near_percentage'] != null
          ? (json['near_percentage'] as num).toDouble()
          : null,
    );
  }
}

class RegionalAlerts {
  final RegionalAlert left;
  final RegionalAlert center;
  final RegionalAlert right;
  
  RegionalAlerts({
    required this.left,
    required this.center,
    required this.right,
  });
  
  factory RegionalAlerts.fromJson(Map<String, dynamic> json) {
    return RegionalAlerts(
      left: RegionalAlert.fromJson(json['left']),
      center: RegionalAlert.fromJson(json['center']),
      right: RegionalAlert.fromJson(json['right']),
    );
  }
}

class AnalysisData {
  final AlertLevel alertLevel;
  final DistanceStats distanceStats;
  final List<Warning> warnings;
  final Map<String, double>? areaPercentages;
  final String? depthImageBase64;
  final RegionalAlerts? regionalAlerts;
  final List<DetectedObject>? detectedObjects;
  
  AnalysisData({
    required this.alertLevel,
    required this.distanceStats,
    required this.warnings,
    this.areaPercentages,
    this.depthImageBase64,
    this.regionalAlerts,
    this.detectedObjects,
  });
  
  factory AnalysisData.fromJson(Map<String, dynamic> json) {
    return AnalysisData(
      alertLevel: AlertLevel.fromString(json['alert_level'] as String),
      distanceStats: DistanceStats.fromJson(json['distance_stats']),
      warnings: (json['warnings'] as List)
          .map((w) => Warning.fromJson(w))
          .toList(),
      areaPercentages: json['area_percentages'] != null
          ? Map<String, double>.from(json['area_percentages'])
          : null,
      depthImageBase64: json['depth_image_base64'] as String?,
      regionalAlerts: json['regional_alerts'] != null
          ? RegionalAlerts.fromJson(json['regional_alerts'])
          : null,
      detectedObjects: json['detected_objects'] != null
          ? (json['detected_objects'] as List)
              .map((o) => DetectedObject.fromJson(o))
              .toList()
          : null,
    );
  }
}

class ApiResponse {
  final bool success;
  final String timestamp;
  final double processingTimeMs;
  final AnalysisData? data;
  final Map<String, String>? error;
  
  ApiResponse({
    required this.success,
    required this.timestamp,
    required this.processingTimeMs,
    this.data,
    this.error,
  });
  
  factory ApiResponse.fromJson(Map<String, dynamic> json) {
    return ApiResponse(
      success: json['success'] as bool,
      timestamp: json['timestamp'] as String,
      processingTimeMs: (json['processing_time_ms'] as num).toDouble(),
      data: json['data'] != null 
          ? AnalysisData.fromJson(json['data']) 
          : null,
      error: json['error'] != null
          ? Map<String, String>.from(json['error'])
          : null,
    );
  }
}
