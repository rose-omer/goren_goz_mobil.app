# 🇹🇷 Gören Göz - YOLO Fine-Tuning Kılavuzu

## Hızlı Başlangıç

### 1. Dataset Hazırla
Roboflow'dan YOLO format export → `datasets/goren_goz_turkish/`

### 2. Eğitim
```bash
cd training
python scripts/train.py --epochs 100 --device 0
```

### 3. Export
```bash
python scripts/export.py --model runs/train/goren_goz_turkish_v1/weights/best.pt
```

## Sınıflar (12)
| ID | Sınıf | Açıklama |
|----|-------|----------|
| 0 | person | Kişi |
| 1 | vehicle | Araç |
| 2 | bicycle | Bisiklet |
| 3 | motorcycle | Motosiklet |
| 4 | pole | Direk |
| 5 | stairs | Merdiven |
| 6 | pothole | Çukur |
| 7 | obstacle | Engel |
| 8 | traffic_sign_tr | TR Levha |
| 9 | crosswalk | Yaya Geçidi |
| 10 | curb | Bordür |
| 11 | construction | İnşaat |
