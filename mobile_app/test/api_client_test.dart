import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:goren_goz_mobil/services/api_client.dart';

/// İsteği kaydeder ve sabit JSON döner; ağa çıkmaz.
class RecordingAdapter implements HttpClientAdapter {
  RecordingAdapter(this.body);

  final Map<String, Object?> body;
  final List<RequestOptions> requests = [];

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(options);
    await requestStream?.drain<void>();
    // Analiz ve soru gerçekten aynı anda uçuşta olsun.
    await Future<void>.delayed(const Duration(milliseconds: 5));
    return ResponseBody.fromString(
      jsonEncode(body),
      200,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  test('eşzamanlı analiz ve soru kendi zaman aşımını korur', () async {
    final analyzeAdapter = RecordingAdapter({
      'processing_time_ms': 10.0,
      'data': {'objects': <Object>[], 'regions': null, 'detector_ok': true},
    });
    final askAdapter = RecordingAdapter({'answer': 'Önünüzde kapı var.'});
    final client = ApiClient(
      baseUrl: 'http://192.168.1.20:8110/',
      apiKey: 'anahtar',
      analyzeDio: Dio()..httpClientAdapter = analyzeAdapter,
      askDio: Dio()..httpClientAdapter = askAdapter,
      sessionId: 'oturum',
    );
    final jpeg = Uint8List.fromList([0xff, 0xd8, 0xff, 0xd9]);

    final results = await Future.wait([
      client.analyze(jpeg, width: 4, height: 4),
      client.ask(jpeg, 'Önümde ne var?'),
      client.analyze(jpeg, width: 4, height: 4),
    ]);

    expect((results[0] as FrameAnalysis).detectorOk, isTrue);
    expect((results[1] as AskResult).answer, 'Önünüzde kapı var.');
    for (final r in analyzeAdapter.requests) {
      expect(r.connectTimeout, ApiClient.analyzeConnectTimeout);
      expect(r.receiveTimeout, ApiClient.analyzeReceiveTimeout);
      expect(r.uri.toString(), 'http://192.168.1.20:8110/api/analyze');
      expect(r.headers['X-Session-Id'], 'oturum');
    }
    final ask = askAdapter.requests.single;
    expect(ask.connectTimeout, ApiClient.askConnectTimeout);
    expect(ask.receiveTimeout, ApiClient.askTimeout);
    expect(ask.headers['X-API-Key'], 'anahtar');
  });
}
