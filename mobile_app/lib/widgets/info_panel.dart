///
/// Info Panel Widget
/// ==================
///

import 'package:flutter/material.dart';
import '../models/api_response.dart';
import '../utils/constants.dart';

class InfoPanel extends StatelessWidget {
  final double fps;
  final DistanceStats? distanceStats;
  final double processingTime;

  const InfoPanel({
    super.key,
    required this.fps,
    this.distanceStats,
    required this.processingTime,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppDimensions.paddingMedium),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.7),
        borderRadius: BorderRadius.circular(AppDimensions.borderRadiusMedium),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          _InfoRow(
            icon: Icons.speed,
            label: 'FPS',
            value: fps.toStringAsFixed(1),
          ),
          if (distanceStats != null) ...[
            const SizedBox(height: 8),
            _InfoRow(
              icon: Icons.straighten,
              label: 'Min',
              value: '${distanceStats!.min.toStringAsFixed(2)}m',
            ),
            const SizedBox(height: 8),
            _InfoRow(
              icon: Icons.equalizer,
              label: 'Avg',
              value: '${distanceStats!.avg.toStringAsFixed(2)}m',
            ),
          ],
          const SizedBox(height: 8),
          _InfoRow(
            icon: Icons.timer,
            label: 'Time',
            value: '${processingTime.toStringAsFixed(0)}ms',
          ),
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 16, color: AppColors.secondary),
        const SizedBox(width: 6),
        Text(
          '$label: ',
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: 12,
          ),
        ),
        Text(
          value,
          style: const TextStyle(
            color: AppColors.text,
            fontSize: 12,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }
}
