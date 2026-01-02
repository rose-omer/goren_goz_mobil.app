///
/// Camera Screen - Main Application Screen
/// ========================================
/// 
/// Captures frames from camera and sends to API for analysis.
/// Displays real-time alerts and depth visualization.
///

import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_service.dart';
import '../services/sound_service.dart';
import '../services/tts_service.dart';
import '../services/speech_recognition_service.dart';
import '../models/api_response.dart';
import '../models/alert_level.dart';
import '../widgets/alert_overlay.dart';
import '../widgets/info_panel.dart';
import '../widgets/regional_indicators.dart';
import '../widgets/object_list.dart';
import '../utils/constants.dart';
import '../utils/logger.dart';
import '../utils/speech_helper.dart';

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> with WidgetsBindingObserver {
  CameraController? _controller;
  Timer? _frameTimer;
  ApiResponse? _latestResponse;
  bool _isInitialized = false;
  bool _isPaused = false;
  int _frameCount = 0;
  int _currentFrameRate = 1;
  DateTime _startTime = DateTime.now();
  
  // VLM contextual assistance
  final SpeechHelper _speechHelper = SpeechHelper();
  bool _isAskingVLM = false;
  
  // Speech recognition
  late SpeechRecognitionService _speechRecognitionService;
  bool _isListeningToSpeech = false;
  String _recognizedQuestion = '';
  
  // Preset questions
  final List<Map<String, String>> _presetQuestions = [
    {'key': 'whats_ahead', 'text': 'What is ahead of me?'},
    {'key': 'safe_to_cross', 'text': 'Is it safe to cross the street?'},
    {'key': 'nearest_obstacle', 'text': 'Where is the nearest obstacle?'},
    {'key': 'stairs_present', 'text': 'Are there stairs ahead?'},
    {'key': 'people_around', 'text': 'Are there people around me?'},
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _speechRecognitionService = SpeechRecognitionService();
    _initializeCamera();
    _initializeSpeechRecognition();
  }
  
  /// Initialize speech recognition
  Future<void> _initializeSpeechRecognition() async {
    final initialized = await _speechRecognitionService.initialize();
    if (initialized) {
      AppLogger.info('Speech recognition initialized successfully');
    } else {
      AppLogger.warning('Speech recognition initialization failed');
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _frameTimer?.cancel();
    _controller?.dispose();
    _speechRecognitionService.cancel();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (_controller == null || !_controller!.value.isInitialized) return;

    if (state == AppLifecycleState.inactive) {
      _frameTimer?.cancel();
      _controller?.dispose();
    } else if (state == AppLifecycleState.resumed) {
      _initializeCamera();
    }
  }

  /// Called when returning from settings screen - reload settings and restart timer
  void _reloadSettingsAndRestartTimer() async {
    final prefs = await SharedPreferences.getInstance();
    final newFrameRate = prefs.getInt('frame_rate') ?? 1;
    
    // Only restart if frame rate changed
    if (newFrameRate != _currentFrameRate) {
      _currentFrameRate = newFrameRate;
      _frameTimer?.cancel();
      _startFrameCapture();
      AppLogger.info('Frame rate changed to $_currentFrameRate FPS, timer restarted');
    }
  }

  Future<void> _initializeCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        AppLogger.error('No cameras available');
        return;
      }

      final camera = cameras.first;
      _controller = CameraController(
        camera,
        ResolutionPreset.high, // High quality for better depth estimation
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.jpeg,
      );

      await _controller!.initialize();

      if (!mounted) return;

      setState(() => _isInitialized = true);

      // Start frame capture timer
      _startFrameCapture();
      
      // Announce app is ready (only on first launch)
      if (_frameCount == 0) {
        final ttsService = context.read<TtsService>();
        await Future.delayed(const Duration(milliseconds: 500));
        ttsService.speak('Gören Göz aktif');
      }

      AppLogger.info('Camera initialized: ${_controller!.value.previewSize}');
    } catch (e) {
      AppLogger.error('Camera initialization failed', e);
    }
  }

  bool _isProcessing = false;

  void _startFrameCapture() async {
    // Load frame rate from settings
    final prefs = await SharedPreferences.getInstance();
    _currentFrameRate = prefs.getInt('frame_rate') ?? 1;
    final intervalMs = (1000 / _currentFrameRate).round();
    
    AppLogger.info('Starting frame capture at $_currentFrameRate FPS (interval: ${intervalMs}ms)');
    
    _frameTimer = Timer.periodic(Duration(milliseconds: intervalMs), (_) async {
      if (_isPaused || !mounted || _controller == null || _isProcessing) return;

      _isProcessing = true;
      try {
        final image = await _controller!.takePicture();
        final bytes = await image.readAsBytes();

        _frameCount++;
        await _analyzeFrame(bytes);
      } catch (e) {
        AppLogger.error('Frame capture error', e);
      } finally {
        _isProcessing = false;
      }
    });
  }

  Future<void> _analyzeFrame(Uint8List bytes) async {
    final apiService = context.read<ApiService>();
    final soundService = context.read<SoundService>();
    final ttsService = context.read<TtsService>();

    final response = await apiService.analyzeImage(bytes);

    if (response != null && response.success && mounted) {
      setState(() => _latestResponse = response);

      final alertLevel = response.data?.alertLevel;
      final minDistance = response.data?.distanceStats.min;

      // Play sound and speak for alerts
      if (alertLevel == AlertLevel.danger) {
        soundService.playAlert(AlertLevel.danger);
        
        // Priority 1: Speak detected objects (most informative)
        final objects = response.data?.detectedObjects;
        if (objects != null && objects.isNotEmpty) {
          _speakMostImportantObject(objects, ttsService, minDistance);
        }
        // Priority 2: Speak regional alert
        else {
          final regional = response.data?.regionalAlerts;
          AppLogger.debug('Regional alerts: ${regional != null ? "Available" : "NULL"}');
          if (regional != null) {
            AppLogger.debug('Left: ${regional.left.hasObstacle}, Center: ${regional.center.hasObstacle}, Right: ${regional.right.hasObstacle}');
            _speakMostDangerousRegion(regional, ttsService);
          } else {
            AppLogger.debug('Using standard TTS');
            ttsService.speakAlert(alertLevel!, minDistance);
          }
        }
      } else if (alertLevel == AlertLevel.near || alertLevel == AlertLevel.medium) {
        // Speak objects or regional alert for near/medium
        final objects = response.data?.detectedObjects;
        if (objects != null && objects.isNotEmpty) {
          _speakMostImportantObject(objects, ttsService, minDistance);
        } else {
          final regional = response.data?.regionalAlerts;
          if (regional != null) {
            _speakMostDangerousRegion(regional, ttsService);
          } else {
            ttsService.speakAlert(alertLevel!, minDistance);
          }
        }
      }
    }
  }

  /// Speak the most dangerous region
  void _speakMostDangerousRegion(RegionalAlerts regional, TtsService ttsService) {
    // Find the most dangerous region
    final regions = [
      {'name': 'left', 'alert': regional.left},
      {'name': 'center', 'alert': regional.center},
      {'name': 'right', 'alert': regional.right},
    ];
    
    // Filter only regions with obstacles
    final dangerousRegions = regions.where((r) {
      final alert = r['alert'] as RegionalAlert;
      return alert.hasObstacle;
    }).toList();
    
    if (dangerousRegions.isEmpty) return;
    
    // Sort by danger level and distance (prioritize center, then closest)
    dangerousRegions.sort((a, b) {
      final alertA = a['alert'] as RegionalAlert;
      final alertB = b['alert'] as RegionalAlert;
      
      // Prioritize center
      if (a['name'] == 'center' && b['name'] != 'center') return -1;
      if (b['name'] == 'center' && a['name'] != 'center') return 1;
      
      // Then by alert level
      final levelOrder = {'DANGER': 0, 'NEAR': 1, 'MEDIUM': 2, 'FAR': 3, 'SAFE': 4};
      final levelCompare = (levelOrder[alertA.alertLevel] ?? 4)
          .compareTo(levelOrder[alertB.alertLevel] ?? 4);
      if (levelCompare != 0) return levelCompare;
      
      // Then by distance (closer is more dangerous)
      return alertA.minDistance.compareTo(alertB.minDistance);
    });
    
    // Speak the most dangerous region
    final mostDangerous = dangerousRegions.first;
    final alert = mostDangerous['alert'] as RegionalAlert;
    final regionName = mostDangerous['name'] as String;
    
    ttsService.speakRegionalAlert(
      region: regionName,
      alertLevel: alert.alertLevel,
      distance: alert.minDistance,
    );
  }
  
  /// Speak most important detected object
  void _speakMostImportantObject(List<DetectedObject> objects, TtsService ttsService, double? minDistance) {
    if (objects.isEmpty) return;
    
    // Objects are already sorted by priority and confidence from backend
    final topObject = objects.first;
    
    // Use Turkish name
    final objectName = ttsService.language.startsWith('tr') 
        ? topObject.nameTr 
        : topObject.name;
    
    // Use depth distance or assume close
    final distance = minDistance ?? 1.0;
    
    ttsService.speakObject(
      objectName: objectName,
      region: topObject.region,
      distance: distance,
    );
    
    AppLogger.debug('Object detected: $objectName in ${topObject.region} region');
  }

  double get _fps {
    final elapsed = DateTime.now().difference(_startTime).inSeconds;
    return elapsed > 0 ? _frameCount / elapsed : 0;
  }

  void _togglePause() {
    setState(() => _isPaused = !_isPaused);
  }
  
  /// Ask VLM a contextual question
  Future<void> _askVLMQuestion(String question) async {
    // Double-check to prevent multiple simultaneous requests
    if (_controller == null || _isAskingVLM) {
      AppLogger.warning('VLM already processing or controller null');
      return;
    }
    
    setState(() => _isAskingVLM = true);
    
    try {
      // CRITICAL: Stop frame capture to avoid resource conflict with camera
      AppLogger.info('Pausing frame capture for VLM question');
      _frameTimer?.cancel();
      
      // Wait for any ongoing frame operations to complete
      await Future.delayed(const Duration(milliseconds: 150));
      
      // Now safely capture frame without competition
      if (_controller == null || !_controller!.value.isInitialized) {
        throw Exception('Camera not initialized');
      }
      
      final image = await _controller!.takePicture();
      final bytes = await image.readAsBytes();
      
      if (bytes.isEmpty) {
        throw Exception('Captured image is empty');
      }
      
      AppLogger.info('Frame captured for VLM: ${bytes.length} bytes');
      AppLogger.info('Asking VLM: $question');
      
      // Show loading indicator
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Cevap bekleniyor...'),
          duration: Duration(seconds: 2),
        ),
      );
      
      // Ask VLM
      final apiService = context.read<ApiService>();
      final result = await apiService.askContext(bytes, question);
      
      if (result != null && result['success'] == true) {
        final answer = result['answer'] as String;
        final metadata = result['metadata'] as Map<String, dynamic>?;
        final source = metadata?['source'] ?? 'unknown';
        
        AppLogger.info('VLM answered: $answer');
        AppLogger.info('Response source: $source (Processing: ${result['processing_time_ms']}ms)');
        
        // Speak answer
        await _speechHelper.speak(answer);
        
        // Show answer in snackbar (5 seconds)
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(answer),
            duration: const Duration(seconds: 5),
            backgroundColor: AppColors.primary,
          ),
        );
      } else if (result != null) {
        // Response received but no success flag
        AppLogger.warning('Response received but success=false: $result');
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Cevap hatası: Geçersiz yanıt'),
            backgroundColor: Colors.red,
          ),
        );
      } else {
        // No response
        AppLogger.error('No response from VLM service');
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Cevap alınamadı. Tekrar deneyin.'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      AppLogger.error('VLM question failed: $e');
      
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Hata: ${e.toString()}'),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 3),
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _isAskingVLM = false);
        // CRITICAL: Resume frame capture after VLM operation completes
        // Wait 1.5 seconds to ensure processing is done and avoid resource conflicts
        AppLogger.info('Pausing frame capture for 1.5 seconds before resume');
        await Future.delayed(const Duration(milliseconds: 1500));
        AppLogger.info('Resuming frame capture');
        _startFrameCapture();
      }
    }
  }
  
  /// Start listening for voice input
  Future<void> _startVoiceQuestion() async {
    try {
      AppLogger.info('🎤 Starting voice recognition...');
      
      // Request microphone permission
      final micStatus = await Permission.microphone.request();
      if (!micStatus.isGranted) {
        if (!mounted) return;
        AppLogger.error('Microphone permission denied');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('Mikrofon izni gerekli'),
            backgroundColor: Colors.red,
            action: SnackBarAction(
              label: 'Ayarlar',
              onPressed: () => openAppSettings(),
            ),
          ),
        );
        return;
      }
      
      // Initialize speech recognition
      final initialized = await _speechRecognitionService.initialize();
      if (!initialized) {
        if (!mounted) return;
        AppLogger.error('Speech recognition init failed');
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Konuşma tanıma hatası'),
            backgroundColor: Colors.red,
          ),
        );
        return;
      }
      
      // Update UI
      setState(() => _isListeningToSpeech = true);
      _recognizedQuestion = '';
      
      AppLogger.info('🎤 Listening...');
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('🎤 Dinliyor...'),
          duration: Duration(seconds: 65),
        ),
      );
      
      // Wait for service readiness
      await Future.delayed(const Duration(milliseconds: 500));
      
      // Start listening
      await _speechRecognitionService.startListening(
        languageCode: 'en-US',
        onResult: (text) {
          setState(() => _recognizedQuestion = text);
          AppLogger.info('📝 Recognized: $text');
        },
      );
      
    } catch (e) {
      AppLogger.error('❌ Voice error: $e');
      setState(() => _isListeningToSpeech = false);
      
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Hata: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }
  
  /// Stop listening and process the recognized question
  Future<void> _stopVoiceQuestion() async {
    if (!_isListeningToSpeech) return;
    
    AppLogger.info('Stopping voice listening...');
    await _speechRecognitionService.stopListening();
    
    // Wait a moment for the speech service to process the final result
    await Future.delayed(const Duration(milliseconds: 300));
    
    if (!mounted) return;
    setState(() => _isListeningToSpeech = false);
    
    // Use the state variable which was updated by the callback
    final question = _recognizedQuestion.trim();
    
    AppLogger.info('Recognized question: "$question"');
    
    if (question.isEmpty) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No speech detected. Please try again.'),
          backgroundColor: Colors.orange,
          duration: Duration(seconds: 2),
        ),
      );
      AppLogger.warning('No speech recognized');
      return;
    }
    
    AppLogger.info('Processing voice question: $question');
    // Now ask VLM with the recognized question
    await _askVLMQuestion(question);
  }
  
  /// Handle voice button tap - simple handler
  void _handleVoiceButtonTap() {
    print('=== VOICE BUTTON TAPPED ===');
    AppLogger.info('Voice button tapped. Currently listening: $_isListeningToSpeech');
    
    if (_isListeningToSpeech) {
      print('=== STOPPING VOICE ===');
      _stopVoiceQuestion();
    } else {
      print('=== STARTING VOICE ===');
      _startVoiceQuestion();
    }
  }
  
  /// Show question selector bottom sheet
  void _showQuestionSheet() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.black87,
      builder: (context) => Container(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Soru Seçin',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ..._presetQuestions.map((q) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: ElevatedButton.icon(
                onPressed: _isAskingVLM ? null : () {
                  Navigator.pop(context);
                  _askVLMQuestion(q['text']!);
                },
                icon: const Icon(Icons.question_answer, color: Colors.white),
                label: Text(
                  q['text']!,
                  style: const TextStyle(fontSize: 16, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.all(16),
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                ),
              ),
            )),
            const SizedBox(height: 8),
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text(
                'İptal',
                style: TextStyle(color: Colors.white70),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getBackgroundColor() {
    final alertLevel = _latestResponse?.data?.alertLevel ?? AlertLevel.safe;
    
    switch (alertLevel) {
      case AlertLevel.danger:
        return AppColors.danger.withOpacity(0.3);
      case AlertLevel.near:
        return AppColors.near.withOpacity(0.2);
      case AlertLevel.medium:
        return AppColors.medium.withOpacity(0.1);
      default:
        return Colors.transparent;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_isInitialized || _controller == null) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          // Camera preview
          CameraPreview(_controller!),

          // Alert color overlay
          AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            color: _getBackgroundColor(),
          ),

          // Alert bar (top)
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: AlertOverlay(
              alertLevel: _latestResponse?.data?.alertLevel ?? AlertLevel.safe,
              warnings: _latestResponse?.data?.warnings ?? [],
            ),
          ),

          // Info panel (top right)
          Positioned(
            top: MediaQuery.of(context).padding.top + 16,
            right: 16,
            child: InfoPanel(
              fps: _fps,
              distanceStats: _latestResponse?.data?.distanceStats,
              processingTime: _latestResponse?.processingTimeMs ?? 0,
            ),
          ),

          // Regional indicators (left/center/right)
          RegionalIndicators(
            regionalAlerts: _latestResponse?.data?.regionalAlerts,
          ),
          
          // Object list (bottom left)
          Positioned(
            bottom: 120,
            left: 0,
            child: ObjectList(
              objects: _latestResponse?.data?.detectedObjects,
              language: context.read<TtsService>().language,
            ),
          ),

          // Control buttons (bottom)
          Positioned(
            bottom: 32,
            left: 0,
            right: 0,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                // Pause button
                FloatingActionButton(
                  onPressed: _togglePause,
                  heroTag: 'pause',
                  child: Icon(_isPaused ? Icons.play_arrow : Icons.pause),
                ),
                
                // Ask Question button (VLM)
                FloatingActionButton.extended(
                  onPressed: _isAskingVLM ? null : _showQuestionSheet,
                  heroTag: 'ask_vlm',
                  icon: _isAskingVLM 
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                      )
                    : const Icon(Icons.question_answer),
                  label: const Text('Soru Sor'),
                  backgroundColor: _isAskingVLM ? Colors.grey : AppColors.accent,
                ),
                // Voice question button (Mic) - with proper hit testing
                Material(
                  color: Colors.transparent,
                  child: GestureDetector(
                    onTap: () {
                      print('=== VOICE BUTTON TAPPED ===');
                      _handleVoiceButtonTap();
                    },
                    child: Container(
                      width: 60,
                      height: 60,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: _isListeningToSpeech ? Colors.red : AppColors.primary,
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.3),
                            blurRadius: 8,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                      child: Center(
                        child: Icon(
                          _isListeningToSpeech ? Icons.mic : Icons.mic_none,
                          color: Colors.white,
                          size: 28,
                        ),
                      ),
                    ),
                  ),
                ),

                // Settings button
                FloatingActionButton(
                  onPressed: () async {
                    await Navigator.pushNamed(context, '/settings');
                    // Reload settings when returning from settings screen
                    if (mounted) {
                      _reloadSettingsAndRestartTimer();
                    }
                  },
                  heroTag: 'settings',
                  child: const Icon(Icons.settings),
                ),
              ],
            ),
          ),

          // Status indicator (processing)
          if (context.watch<ApiService>().isProcessing)
            const Positioned(
              top: 100,
              right: 16,
              child: CircularProgressIndicator(
                valueColor: AlwaysStoppedAnimation<Color>(AppColors.secondary),
              ),
            ),
        ],
      ),
    );
  }
}
