///
/// Regional Indicators Widget
/// ===========================
/// Shows left/center/right obstacle indicators
///

import 'package:flutter/material.dart';
import '../models/api_response.dart';
import '../utils/constants.dart';

class RegionalIndicators extends StatelessWidget {
  final RegionalAlerts? regionalAlerts;
  
  const RegionalIndicators({
    super.key,
    this.regionalAlerts,
  });

  @override
  Widget build(BuildContext context) {
    if (regionalAlerts == null) {
      return const SizedBox.shrink();
    }
    
    return Positioned(
      bottom: 150,
      left: 0,
      right: 0,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _buildRegionIndicator(
            region: 'left',
            alert: regionalAlerts!.left,
            icon: Icons.arrow_back,
          ),
          _buildRegionIndicator(
            region: 'center',
            alert: regionalAlerts!.center,
            icon: Icons.warning,
          ),
          _buildRegionIndicator(
            region: 'right',
            alert: regionalAlerts!.right,
            icon: Icons.arrow_forward,
          ),
        ],
      ),
    );
  }
  
  Widget _buildRegionIndicator({
    required String region,
    required RegionalAlert alert,
    required IconData icon,
  }) {
    if (!alert.hasObstacle) {
      return const SizedBox(width: 80, height: 80);
    }
    
    Color color = _getColorForLevel(alert.alertLevel);
    
    return Container(
      width: 80,
      height: 80,
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.8),
        shape: BoxShape.circle,
        border: Border.all(color: Colors.white, width: 2),
        boxShadow: [
          BoxShadow(
            color: color.withValues(alpha: 0.5),
            blurRadius: 10,
            spreadRadius: 2,
          ),
        ],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: Colors.white, size: 32),
          const SizedBox(height: 4),
          Text(
            alert.message,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
  
  Color _getColorForLevel(String level) {
    switch (level) {
      case 'DANGER':
        return AppColors.danger;
      case 'NEAR':
        return AppColors.near;
      case 'MEDIUM':
        return AppColors.medium;
      case 'FAR':
        return AppColors.far;
      default:
        return AppColors.safe;
    }
  }
}
