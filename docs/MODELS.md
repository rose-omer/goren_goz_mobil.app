# Modeller

## Kullanılan

| Rol | Model | Yer | Lisans |
|---|---|---|---|
| Göreli derinlik (sunucu) | MiDaS_small OpenVINO IR | `backend/model_files/openvino/` | MIT |
| Göreli derinlik (sunucu, ikinci arka uç) | Depth Anything V2 Small OpenVINO IR, `DEPTH_BACKEND=depth_anything` | `backend/model_files/openvino/depth_anything_v2_small.xml` | Apache-2.0 |
| Nesne tespiti (sunucu) | YOLO26n (COCO) → 12 sınıflı Türkiye modeli | `backend/model_files/yolo26n.pt` | AGPL-3.0 |
| VLM (sunucu) | Aday: SmolVLM2-500M, Qwen3.5-0.8B/2B, Gemma 4 E2B | llama-server | Apache-2.0 |
| Cihaz üstü tespit | YOLO26n INT8 LiteRT | `mobile_app/assets/models/` | AGPL-3.0 |
| Cihaz üstü derinlik | Depth Anything V2/3 Small LiteRT | `mobile_app/assets/models/` | Apache-2.0 |

- Depth Anything Base/Large ve UniDepthV2 CC-BY-NC: kullanma.
- İki sunucu derinlik arka ucu aynı ön işlemeyi kullanır: ImageNet normu, en-boy oranı korunur, kalan alan dolgu (`services/depth/base.py`). Girdi kenarı IR'nin sabit şeklinden okunur (MiDaS 256, Depth Anything 518).
- Depth Anything IR `models.json`'da yok; ölçüm tablosu çıkmadan varsayılan MiDaS kalır.
- Modeller git'e girmez. 5 MB üstü dosyayı CI reddeder.

## Dağıtım

1. Hugging Face model reposuna yükle (ör. `rose-omer/goren-goz-models`).
2. `backend/scripts/models.json`: `revision` alanına 40 karakterlik commit, her dosyaya `sha256` yaz.
3. İndir: `python backend/scripts/download_models.py` (`--target backend` ya da `mobile`).

Betik commit'i sabitler ve SHA-256 denetler. Manifest doldurulmadan çalışmaz.

## Eğitim (Colab; bu makinede eğitim yok)

```bash
cd training
python scripts/train.py --model yolo26n.pt --data configs/dataset.yaml --device 0
python scripts/export.py --model runs/detect/goren_goz_turkish_v1/weights/best.pt --target both
```

- `export.py`: mobil için `format="litert", int8=True, imgsz=416`; sunucu için `format="openvino"`. Argüman adlarını Ultralytics export belgesinde doğrula.
- Sınıf başına örnek sayısını raporla; çukur ve bordür az ise veri ekle.
- Hedef: merdiven, bordür, direk için mAP50 ≥ 0.5.

## Sınıflar

12 sınıf: person, vehicle, bicycle, motorcycle, pole, stairs, pothole, obstacle, traffic_sign_tr, crosswalk, curb, construction. Türkçe adlar `backend/services/labels.py` içinde.

## VLM seçimi

- 30 Türkçe soru × 30 görüntü. Ölçüt: doğru/yanlış (iki kişi puanlar), dilbilgisi, p50 gecikme.
- Ağır ölçümden önce boş commit ≥ 8 GB olmalı.
- Seçilen model `VLM_MODEL` ortam değişkenine yazılır.
