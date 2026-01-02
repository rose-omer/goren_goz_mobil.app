///
/// Alert Overlay Widget
/// =====================
///

import 'package:flutter/material.dart';
import '../models/alert_level.dart';
import '../models/api_response.dart';
import '../utils/constants.dart';

class AlertOverlay extends StatelessWidget {
  final AlertLevel alertLevel;
  final List<Warning> warnings;

  const AlertOverlay({
    super.key,
    required this.alertLevel,
    required this.warnings,
  });

  Color _getAlertColor() {
    switch (alertLevel) {
      case AlertLevel.danger:
        return AppColors.danger;
      case AlertLevel.near:
        return AppColors.near;
      case AlertLevel.medium:
        return AppColors.medium;
      case AlertLevel.far:
        return AppColors.far;
      case AlertLevel.safe:
        return AppColors.safe;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (warnings.isEmpty && alertLevel == AlertLevel.safe) {
      return const SizedBox.shrink();
    }

    return SafeArea(
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(AppDimensions.paddingMedium),
        decoration: BoxDecoration(
          color: _getAlertColor().withOpacity(0.9),
          borderRadius: const BorderRadius.only(
            bottomLeft: Radius.circular(AppDimensions.borderRadiusMedium),
            bottomRight: Radius.circular(AppDimensions.borderRadiusMedium),
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Alert level
            Row(
              children: [
                Icon(
                  _getAlertIcon(),
                  color: Colors.white,
                  size: AppDimensions.iconSizeLarge,
                ),
                const SizedBox(width: 12),
                Text(
                  alertLevel.displayName,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),

            // Warnings
            if (warnings.isNotEmpty) ...[
              const SizedBox(height: 8),
              ...warnings.map((warning) => Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      warning.message,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                      ),
                    ),
                  )),
            ],
          ],
        ),
      ),
    );
  }

  IconData _getAlertIcon() {
    switch (alertLevel) {
      case AlertLevel.danger:
        return Icons.error;
      case AlertLevel.near:
      case AlertLevel.medium:
        return Icons.warning;
      default:
        return Icons.check_circle;
    }
  }
}
