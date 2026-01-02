"""
Gören Göz - YOLO Fine-Tuning Script
====================================

Türkiye sokak koşullarına özel nesne tespiti modeli eğitimi.

Kullanım:
    python train.py --epochs 100 --batch 16

Google Colab'da:
    !python train.py --device 0
"""

import argparse
from pathlib import Path
from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(description='Gören Göz YOLO Fine-tuning')
    parser.add_argument('--model', type=str, default='yolo11n.pt',
                        help='Base model (yolo11n.pt, yolo11s.pt)')
    parser.add_argument('--data', type=str, default='configs/dataset.yaml',
                        help='Dataset config path')
    parser.add_argument('--epochs', type=int, default=100,
                        help='Number of epochs')
    parser.add_argument('--batch', type=int, default=16,
                        help='Batch size')
    parser.add_argument('--imgsz', type=int, default=640,
                        help='Image size')
    parser.add_argument('--device', type=str, default='cpu',
                        help='Device (cpu, 0, 0,1)')
    parser.add_argument('--patience', type=int, default=20,
                        help='Early stopping patience')
    parser.add_argument('--name', type=str, default='goren_goz_turkish_v1',
                        help='Experiment name')
    return parser.parse_args()


def train(args):
    """Ana eğitim fonksiyonu"""
    
    print("="*60)
    print("🇹🇷 Gören Göz - Türkiye Özel YOLO Fine-Tuning")
    print("="*60)
    
    # Base model yükle
    print(f"\n📦 Base model yükleniyor: {args.model}")
    model = YOLO(args.model)
    
    # Fine-tune başlat
    print(f"\n🚀 Eğitim başlıyor... (Epochs: {args.epochs})\n")
    
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        patience=args.patience,
        device=args.device,
        
        # Augmentation
        mosaic=1.0,
        mixup=0.1,
        
        # Proje ayarları
        project='runs/train',
        name=args.name,
        exist_ok=True,
        
        # Kaydetme
        save=True,
        plots=True
    )
    
    print("\n✅ Eğitim tamamlandı!")
    print(f"📁 Best model: runs/train/{args.name}/weights/best.pt")
    
    return results


if __name__ == '__main__':
    args = parse_args()
    train(args)
