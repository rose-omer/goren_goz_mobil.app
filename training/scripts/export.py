"""
Gören Göz - model dışa aktarma.

- Mobil: LiteRT (INT8) `.tflite`, `assets/models/` altına girer.
- Sunucu: OpenVINO IR (`.xml` + `.bin`), `MODELS_DIR` altına girer.

Argüman adlarını Ultralytics export belgesiyle doğrula:
https://docs.ultralytics.com/modes/export/
"""

import argparse

from ultralytics import YOLO


def main() -> None:
    parser = argparse.ArgumentParser(description="Gören Göz model dışa aktarma")
    parser.add_argument("--model", required=True, help="Eğitilmiş ağırlık (best.pt)")
    parser.add_argument("--data", default="configs/dataset.yaml", help="INT8 kalibrasyon verisi")
    parser.add_argument("--imgsz", type=int, default=416)
    parser.add_argument(
        "--target",
        choices=("mobile", "server", "both"),
        default="both",
        help="mobile = litert int8, server = openvino",
    )
    args = parser.parse_args()

    model = YOLO(args.model)
    if args.target in ("mobile", "both"):
        path = model.export(format="litert", int8=True, imgsz=args.imgsz, data=args.data)
        print(f"LiteRT: {path}")
    if args.target in ("server", "both"):
        path = model.export(format="openvino", imgsz=args.imgsz)
        print(f"OpenVINO: {path}")


if __name__ == "__main__":
    main()
