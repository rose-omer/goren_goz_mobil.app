"""
Gören Göz - Model Validation Script
"""

import argparse
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, required=True)
    parser.add_argument('--data', type=str, default='configs/dataset.yaml')
    args = parser.parse_args()
    
    model = YOLO(args.model)
    metrics = model.val(data=args.data)
    
    print(f"\nmAP50: {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")


if __name__ == '__main__':
    main()
