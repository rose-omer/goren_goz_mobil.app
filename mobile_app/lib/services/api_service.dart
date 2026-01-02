///
/// API Service - Backend Communication with Retry Logic
/// =====================================================
///

import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:image/image.dart' as img;

import '../models/api_response.dart';
import '../utils/constants.dart';
import '../utils/logger.dart';

class ApiService extends ChangeNotifier {
  late Dio _dio;
  String _apiUrl = AppConfig.apiUrl;
  bool _isProcessing = false;
  ApiResponse? _lastResponse;
  
  ApiService() {
    _initDio();
  }
  
  void _initDio() {
    _dio = Dio(BaseOptions(
      baseUrl: _apiUrl,
      connectTimeout: AppConfig.requestTimeout,
      receiveTimeout: AppConfig.requestTimeout,
      headers: {
        'Accept': 'application/json',
      },
    ));
    
    // Add retry interceptor
    _dio.interceptors.add(RetryInterceptor(
      dio: _dio,
      maxRetries: AppConfig.maxRetries,
      retryDelays: const [
        Duration(milliseconds: 500),
        Duration(milliseconds: 1000),
      ],
    ));
    
    AppLogger.info('ApiService initialized with URL: $_apiUrl');
  }
  
  // Getters
  bool get isProcessing => _isProcessing;
  ApiResponse? get lastResponse => _lastResponse;
  String get apiUrl => _apiUrl;
  
  // Update API URL
  void setApiUrl(String url) {
    _apiUrl = url;
    _initDio();
    notifyListeners();
    AppLogger.info('API URL updated to: $url');
  }
  
  Future<ApiResponse?> analyzeImage(
    Uint8List imageBytes, {
    bool includeDepthImage = false,
    String colormap = 'JET',
  }) async {
    if (_isProcessing) {
      AppLogger.warning('Analysis already in progress, skipping request');
      return _lastResponse;
    }
    
    // ✅ Check if frame should be processed (skip static scenes)
    if (!_shouldProcessFrame(imageBytes)) {
      return _lastResponse;
    }
    
    _isProcessing = true;
    notifyListeners();
    
    try {
      // Compress image to reduce size
      final compressedBytes = await _compressImage(imageBytes);
      
      // Create multipart request
      final formData = FormData.fromMap({
        'image': MultipartFile.fromBytes(
          compressedBytes,
          filename: 'frame.jpg',
        ),
      });
      
      // Make request
      final response = await _dio.post(
        AppConfig.analyzeEndpoint,
        data: formData,
        queryParameters: {
          'include_depth_image': includeDepthImage,
          'colormap': colormap,
        },
      );
      
      // Parse response
      final apiResponse = ApiResponse.fromJson(response.data);
      _lastResponse = apiResponse;
      
      AppLogger.info(
        'Analysis completed: ${apiResponse.data?.alertLevel.displayName}, '
        'time: ${apiResponse.processingTimeMs.toStringAsFixed(1)}ms'
      );
      
      return apiResponse;
      
    } on DioException catch (e) {
      AppLogger.error('API request failed', e);
      
      // Return error response
      return ApiResponse(
        success: false,
        timestamp: DateTime.now().toIso8601String(),
        processingTimeMs: 0,
        error: {
          'code': e.type.toString(),
          'message': _getErrorMessage(e),
        },
      );
      
    } catch (e) {
      AppLogger.error('Unexpected error in analyzeImage', e);
      
      // ✅ Return proper error response instead of null
      return ApiResponse(
        success: false,
        timestamp: DateTime.now().toIso8601String(),
        processingTimeMs: 0,
        error: {
          'code': 'UNEXPECTED_ERROR',
          'message': 'Beklenmeyen bir hata oluştu: ${e.toString()}',
        },
      );
      
    } finally {
      _isProcessing = false;
      notifyListeners();
    }
  }
  
  // Previous frame for skip logic
  Uint8List? _previousFrame;
  int _framesSinceStart = 0;
  static const int _warmupFrames = 5; // Always process first 5 frames
  
  /// Check if frame has significant changes (skip static scenes)
  /// Improved algorithm: samples random points across entire image
  bool _shouldProcessFrame(Uint8List current) {
    _framesSinceStart++;
    
    // Always process first few frames (warmup period)
    if (_framesSinceStart <= _warmupFrames) {
      _previousFrame = current;
      AppLogger.debug('Warmup frame $_framesSinceStart/$_warmupFrames - processing');
      return true;
    }
    
    if (_previousFrame == null) {
      _previousFrame = current;
      return true;
    }
    
    // Skip comparison if sizes don't match
    if (current.length != _previousFrame!.length) {
      _previousFrame = current;
      return true;
    }
    
    // Sample random points across the ENTIRE image (not just first 1000 bytes)
    // This ensures we detect changes anywhere in the frame
    final frameLength = current.length;
    const numSamples = 500; // Number of random sample points
    int diffCount = 0;
    
    // Use deterministic "random" based on frame size for reproducibility
    final step = frameLength ~/ numSamples;
    
    for (int i = 0; i < numSamples; i++) {
      // Sample evenly distributed points across the frame
      final idx = (i * step + (i * 17) % step) % frameLength; // Pseudo-random distribution
      
      final diff = (current[idx] - _previousFrame![idx]).abs();
      if (diff > 20) { // Pixel difference threshold (was 25)
        diffCount++;
      }
    }
    
    _previousFrame = current;
    
    // Process if >3% of sampled points changed (was 5%)
    final changeRatio = diffCount / numSamples;
    final shouldProcess = changeRatio > 0.03;
    
    if (!shouldProcess) {
      AppLogger.debug('Skip frame - change ratio: ${(changeRatio * 100).toStringAsFixed(1)}%');
    } else {
      AppLogger.debug('Process frame - change ratio: ${(changeRatio * 100).toStringAsFixed(1)}%');
    }
    
    return shouldProcess;
  }
  
  /// Compress image to reduce size and improve speed
  Future<List<int>> _compressImage(Uint8List bytes) async {
    return await compute(_compressImageIsolate, bytes);
  }
  
  static List<int> _compressImageIsolate(Uint8List bytes) {
    final image = img.decodeImage(bytes);
    if (image == null) return bytes;
    
    // Resize to target size if needed
    final resized = img.copyResize(
      image,
      width: 640,
      height: 480,
      interpolation: img.Interpolation.linear,
    );
    
    // Encode as JPEG with quality
    return img.encodeJpg(resized, quality: AppConfig.jpegQuality);
  }
  
  /// Ask VLM a contextual question about the scene
  Future<Map<String, dynamic>?> askContext(
    Uint8List imageBytes,
    String question, {
    bool useCachedDetections = true,
  }) async {
    try {
      AppLogger.info('Asking VLM question: $question');
      
      // Create multipart request
      final formData = FormData.fromMap({
        'image': MultipartFile.fromBytes(
          imageBytes,
          filename: 'frame.jpg',
        ),
        'question': question,
        'use_cached_detections': useCachedDetections.toString(),
      });
      
      // Make request
      final response = await _dio.post(
        '/api/ask_context',
        data: formData,
      );
      
      if (response.statusCode == 200 && response.data != null) {
        final result = response.data as Map<String, dynamic>;
        AppLogger.info('VLM Raw Response: $result');
        
        // Check if response contains answer (success field may vary)
        if (result.containsKey('answer') && result['answer'] != null) {
          final answer = result['answer'] as String;
          AppLogger.info(
            'VLM answered in ${result['processing_time_ms']}ms: ${answer.substring(0, min(50, answer.length))}...'
          );
          return {
            'success': true,
            'answer': answer,
            'processing_time_ms': result['processing_time_ms'],
          };
        } else {
          AppLogger.error('VLM response missing answer field: ${result['error'] ?? 'Unknown error'}');
          return null;
        }
      }
      
      AppLogger.error('VLM response: statusCode=${response.statusCode}, data=${response.data}');
      return null;
      
    } on DioException catch (e) {
      AppLogger.error('VLM API request failed', e);
      AppLogger.error('DioException details: status=${e.response?.statusCode}, data=${e.response?.data}');
      return null;
    } catch (e) {
      AppLogger.error('Unexpected error in askContext', e);
      AppLogger.error('Error type: ${e.runtimeType}, message: $e');
      return null;
    }
  }
  
  /// Check server health
  Future<bool> checkHealth() async {
    try {
      final response = await _dio.get(AppConfig.healthEndpoint);
      return response.statusCode == 200;
    } catch (e) {
      AppLogger.error('Health check failed', e);
      return false;
    }
  }
  
  String _getErrorMessage(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return 'Bağlantı zaman aşımı';
      case DioExceptionType.badResponse:
        return 'Sunucu hatası (${error.response?.statusCode})';
      case DioExceptionType.cancel:
        return 'İstek iptal edildi';
      default:
        return 'Bağlantı hatası';
    }
  }
}

/// Retry interceptor for Dio
class RetryInterceptor extends Interceptor {
  final Dio dio;
  final int maxRetries;
  final List<Duration> retryDelays;
  
  RetryInterceptor({
    required this.dio,
    required this.maxRetries,
    required this.retryDelays,
  });
  
  @override
  Future onError(DioException err, ErrorInterceptorHandler handler) async {
    if (_shouldRetry(err) && err.requestOptions.extra['retryCount'] == null) {
      int retryCount = 0;
      
      while (retryCount < maxRetries) {
        await Future.delayed(retryDelays[retryCount]);
        
        try {
          final response = await dio.fetch(err.requestOptions);
          return handler.resolve(response);
        } catch (e) {
          retryCount++;
          if (retryCount >= maxRetries) {
            return handler.next(err);
          }
        }
      }
    }
    
    return handler.next(err);
  }
  
  bool _shouldRetry(DioException err) {
    return err.type == DioExceptionType.connectionTimeout ||
           err.type == DioExceptionType.sendTimeout ||
           err.type == DioExceptionType.receiveTimeout ||
           (err.response?.statusCode ?? 0) >= 500;
  }
}
