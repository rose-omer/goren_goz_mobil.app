// Sunucu istemcisi. Analiz isteğinde yeniden deneme yok (eski kare gerçek zamanda yanlıştır);
// soru isteğinde yeni FormData ile bir kez denenir (plan E12, E13).

import 'dart:math';
import 'dart:typed_data';

import 'package:dio/dio.dart';

import '../core/hazard_engine.dart';

/// Kullanıcıya okunacak hata. [message] Türkçe ve eylem söyler.
class ApiFailure implements Exception {
  const ApiFailure(this.code, this.message);

  final String code;
  final String message;

  bool get isOffline => code == 'OFFLINE' || code == 'TIMEOUT';

  @override
  String toString() => 'ApiFailure($code)';
}

class ServerObject {
  const ServerObject({
    required this.name,
    required this.nameTr,
    required this.confidence,
    required this.bbox,
    required this.region,
    required this.priority,
    required this.trackId,
    required this.isApproaching,
    this.distanceM,
    this.ttcS,
  });

  factory ServerObject.fromJson(Map<String, dynamic> json) {
    final box = (json['bbox'] as List).map((v) => (v as num).toDouble()).toList();
    return ServerObject(
      name: json['name'] as String,
      nameTr: json['name_tr'] as String,
      confidence: (json['confidence'] as num).toDouble(),
      bbox: box,
      region: Region.values.byName(json['region'] as String),
      priority: json['priority'] as int,
      trackId: json['track_id'] as String,
      isApproaching: json['is_approaching'] as bool? ?? false,
      distanceM: (json['distance_m'] as num?)?.toDouble(),
      ttcS: (json['ttc_s'] as num?)?.toDouble(),
    );
  }

  final String name;
  final String nameTr;
  final double confidence;
  final List<double> bbox;
  final Region region;
  final int priority;
  final String trackId;
  final bool isApproaching;
  final double? distanceM;
  final double? ttcS;

  PerceivedObject toPerceived() => PerceivedObject(
    nameTr: nameTr,
    region: region,
    priority: priority,
    trackId: trackId,
    ttcS: ttcS,
    distanceM: distanceM,
  );
}

class FrameAnalysis {
  const FrameAnalysis({
    required this.objects,
    required this.regions,
    required this.detectorOk,
    required this.serverMs,
    required this.imageWidth,
    required this.imageHeight,
  });

  factory FrameAnalysis.fromJson(Map<String, dynamic> json, {required int width, required int height}) {
    final data = json['data'] as Map<String, dynamic>;
    final rawRegions = data['regions'] as Map<String, dynamic>?;
    return FrameAnalysis(
      objects: [for (final o in data['objects'] as List) ServerObject.fromJson(o as Map<String, dynamic>)],
      regions: rawRegions == null
          ? null
          : {
              for (final entry in rawRegions.entries)
                Region.values.byName(entry.key): RegionReading(
                  proximity: ((entry.value as Map)['proximity'] as num).toDouble(),
                  label: (entry.value as Map)['label'] as String,
                  closeArea: (((entry.value as Map)['close_area'] as num?) ?? 0).toDouble(),
                ),
            },
      // Alan yoksa (eski sunucu) tespitin çalıştığı varsayılmaz: "Yol açık" denmez.
      detectorOk: data['detector_ok'] as bool? ?? false,
      serverMs: (json['processing_time_ms'] as num).toDouble(),
      imageWidth: width,
      imageHeight: height,
    );
  }

  final List<ServerObject> objects;
  final Map<Region, RegionReading>? regions;

  /// Sunucuda tespit modeli çalıştı mı. `false` ise boş [objects] "nesne yok" demek değildir.
  final bool detectorOk;
  final double serverMs;
  final int imageWidth;
  final int imageHeight;
}

class AskResult {
  const AskResult(this.answer, this.elapsedMs);

  final String answer;
  final double elapsedMs;
}

abstract interface class AnalysisApi {
  Future<FrameAnalysis> analyze(Uint8List jpeg, {required int width, required int height, double? focalPx});
  Future<AskResult> ask(Uint8List jpeg, String question);
  Future<bool> health();
}

/// Analiz ve soru için iki ayrı [Dio]. `connectTimeout` istek başına [Options] ile verilemez;
/// paylaşılan örnekte değiştirmek eşzamanlı analiz ve sorunun zaman aşımını birbirine ezdirir.
class ApiClient implements AnalysisApi {
  ApiClient({required String baseUrl, required String apiKey, Dio? analyzeDio, Dio? askDio, String? sessionId})
    : _sessionId = sessionId ?? _newSessionId(),
      _analyzeDio = (analyzeDio ?? Dio())..options.connectTimeout = analyzeConnectTimeout,
      _askDio = (askDio ?? Dio())..options.connectTimeout = askConnectTimeout {
    configure(baseUrl: baseUrl, apiKey: apiKey);
  }

  final Dio _analyzeDio;
  final Dio _askDio;
  final String _sessionId;

  static const analyzeConnectTimeout = Duration(seconds: 2);

  /// Sunucu CPU'da MiDaS + YOLO koşar; ilk kare ısınma içerir. Tek zaman aşımı "bağlantı koptu"
  /// sayılmaz (bkz. `WalkController.offlineAfterTimeouts`).
  static const analyzeReceiveTimeout = Duration(seconds: 2);
  static const askConnectTimeout = Duration(seconds: 5);
  static const askTimeout = Duration(seconds: 30);

  void configure({required String baseUrl, required String apiKey}) {
    final base = baseUrl.trim().replaceAll(RegExp(r'/+$'), '');
    final headers = {if (apiKey.isNotEmpty) 'X-API-Key': apiKey, 'X-Session-Id': _sessionId};
    for (final dio in [_analyzeDio, _askDio]) {
      dio.options
        ..baseUrl = base
        ..headers = {...headers};
    }
  }

  @override
  Future<FrameAnalysis> analyze(Uint8List jpeg, {required int width, required int height, double? focalPx}) async {
    final form = FormData.fromMap({
      'image': MultipartFile.fromBytes(jpeg, filename: 'kare.jpg', contentType: DioMediaType('image', 'jpeg')),
      if (focalPx != null) 'focal_px': focalPx.toStringAsFixed(1),
    });
    final json = await _post(
      _analyzeDio,
      '/api/analyze',
      form,
      Options(sendTimeout: analyzeConnectTimeout, receiveTimeout: analyzeReceiveTimeout),
    );
    return FrameAnalysis.fromJson(json, width: width, height: height);
  }

  @override
  Future<AskResult> ask(Uint8List jpeg, String question) async {
    final watch = Stopwatch()..start();
    FormData buildForm() => FormData.fromMap({
      'image': MultipartFile.fromBytes(jpeg, filename: 'soru.jpg', contentType: DioMediaType('image', 'jpeg')),
      'question': question,
    });
    final options = Options(sendTimeout: askTimeout, receiveTimeout: askTimeout);
    Map<String, dynamic> json;
    try {
      json = await _post(_askDio, '/api/ask_context', buildForm(), options);
    } on ApiFailure catch (failure) {
      if (!failure.isOffline) rethrow;
      // FormData tek kullanımlık; yeniden denemede yenisini kur.
      json = await _post(_askDio, '/api/ask_context', buildForm(), options);
    }
    return AskResult(json['answer'] as String, watch.elapsedMilliseconds.toDouble());
  }

  @override
  Future<bool> health() async {
    try {
      final response = await _askDio.get<Map<String, dynamic>>(
        '/health',
        options: Options(receiveTimeout: const Duration(seconds: 2)),
      );
      return response.statusCode == 200;
    } on DioException {
      return false;
    }
  }

  Future<Map<String, dynamic>> _post(Dio dio, String path, FormData form, Options options) async {
    try {
      final response = await dio.post<Map<String, dynamic>>(path, data: form, options: options);
      return response.data ?? const {};
    } on DioException catch (error) {
      throw mapDioError(error);
    }
  }

  static String _newSessionId() {
    final random = Random.secure();
    return List.generate(16, (_) => random.nextInt(256).toRadixString(16).padLeft(2, '0')).join();
  }
}

/// Dio hatasını sabit kodlu, Türkçe [ApiFailure]'a çevirir. Ham hata metni kullanıcıya gitmez.
ApiFailure mapDioError(DioException error) {
  switch (error.type) {
    case DioExceptionType.connectionTimeout:
    case DioExceptionType.sendTimeout:
    case DioExceptionType.receiveTimeout:
      return const ApiFailure('TIMEOUT', 'Sunucu geç cevap verdi.');
    case DioExceptionType.connectionError:
      return const ApiFailure('OFFLINE', 'Sunucuya bağlanılamadı.');
    case DioExceptionType.badResponse:
      final status = error.response?.statusCode ?? 0;
      final body = error.response?.data;
      final code = body is Map && body['error'] is Map ? (body['error'] as Map)['code'] as String? : null;
      return switch ((status, code)) {
        (401, _) => const ApiFailure('UNAUTHORIZED', 'API anahtarı geçersiz. Ayarlardan düzeltin.'),
        (503, 'VLM_UNAVAILABLE') => const ApiFailure('VLM_UNAVAILABLE', 'Soru sorma şu an kullanılamıyor.'),
        (503, _) => const ApiFailure('SERVER_UNAVAILABLE', 'Sunucu hazır değil.'),
        (429, _) => const ApiFailure('RATE_LIMITED', 'Çok sık istek gönderildi.'),
        (413, _) => const ApiFailure('TOO_LARGE', 'Görüntü çok büyük.'),
        _ => const ApiFailure('SERVER_ERROR', 'Sunucu hatası.'),
      };
    default:
      return const ApiFailure('UNKNOWN', 'Beklenmeyen bağlantı hatası.');
  }
}
