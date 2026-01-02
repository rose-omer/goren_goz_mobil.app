///
/// Object List Widget
/// ==================
///
/// Displays detected objects in a compact list at the bottom of screen.
///

import 'package:flutter/material.dart';
import '../models/api_response.dart';

class ObjectList extends StatelessWidget {
  final List<DetectedObject>? objects;
  final String language;

  const ObjectList({
    super.key,
    required this.objects,
    required this.language,
  });

  @override
  Widget build(BuildContext context) {
    if (objects == null || objects!.isEmpty) {
      return const SizedBox.shrink();
    }

    // Show top 3 objects
    final displayObjects = objects!.take(3).toList();

    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.7),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white24, width: 1),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              const Icon(Icons.visibility, color: Colors.white70, size: 16),
              const SizedBox(width: 6),
              Text(
                language.startsWith('tr') ? 'Tespit Edilen' : 'Detected',
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          // Object list
          ...displayObjects.map((obj) => _buildObjectItem(obj)),
        ],
      ),
    );
  }

  Widget _buildObjectItem(DetectedObject obj) {
    final name = language.startsWith('tr') ? obj.nameTr : obj.name;
    final regionIcon = _getRegionIcon(obj.region);
    final confidencePercent = (obj.confidence * 100).toInt();

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Region indicator
          Text(
            regionIcon,
            style: const TextStyle(fontSize: 16),
          ),
          const SizedBox(width: 8),
          // Object name
          Flexible(
            child: Text(
              name,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          const SizedBox(width: 8),
          // Confidence
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: _getConfidenceColor(obj.confidence),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              '$confidencePercent%',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 10,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _getRegionIcon(String region) {
    switch (region) {
      case 'left':
        return '←';
      case 'right':
        return '→';
      case 'center':
      default:
        return '↑';
    }
  }

  Color _getConfidenceColor(double confidence) {
    if (confidence >= 0.8) {
      return Colors.green.withOpacity(0.7);
    } else if (confidence >= 0.6) {
      return Colors.orange.withOpacity(0.7);
    } else {
      return Colors.red.withOpacity(0.7);
    }
  }
}
