"""
Gören Göz - Model Export Script
"""

import argparse
import shutil
from pathlib import Path
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, required=True)
    parser.add_argument('--output', type=str, default='../../backend/models')
    args = parser.parse_args()
    
    model = YOLO(args.model)
    output = Path(args.output)
    output.mkdir(exist_ok=True)
    
    # PyTorch copy
    shutil.copy(args.model, output / 'yolo11n_turkish.pt')
    print(f"✅ Exported to {output / 'yolo11n_turkish.pt'}")
    
    # ONNX export
    model.export(format='onnx', opset=17)
    print("✅ ONNX export done")


if __name__ == '__main__':
    main()
