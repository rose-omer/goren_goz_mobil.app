"""
Gören Göz Laptop - Test Script
===============================

Bu script, kamera modülünü basit bir şekilde test eder.
"""

import sys
import os

# src klasörünü path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import logging
import time

# Logging ayarla
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_imports():
    """Gerekli modüllerin import edilip edilmediğini test eder."""
    logger.info("=" * 70)
    logger.info("ADIM 1: Import Testi")
    logger.info("=" * 70)
    
    # Python 3.12 için Buffer workaround
    try:
        import collections.abc
        if not hasattr(collections.abc, 'Buffer'):
            collections.abc.Buffer = (bytes, bytearray, memoryview)
    except Exception:
        pass
    
    try:
        import cv2
        logger.info(f"✓ OpenCV başarıyla import edildi (versiyon: {cv2.__version__})")
    except ImportError as e:
        logger.error(f"✗ OpenCV import edilemedi: {e}")
        logger.error("  Çözüm: pip install opencv-python")
        return False
    
    try:
        import numpy as np
        logger.info(f"✓ NumPy başarıyla import edildi (versiyon: {np.__version__})")
    except ImportError as e:
        logger.error(f"✗ NumPy import edilemedi: {e}")
        logger.error("  Çözüm: pip install numpy")
        return False
    
    try:
        import yaml
        logger.info(f"✓ PyYAML başarıyla import edildi")
    except ImportError as e:
        logger.error(f"✗ PyYAML import edilemedi: {e}")
        logger.error("  Çözüm: pip install pyyaml")
        return False
    
    logger.info("✓ Tüm temel modüller başarıyla import edildi!")
    return True


def test_config():
    """Config modülünü test eder."""
    logger.info("\n" + "=" * 70)
    logger.info("ADIM 2: Config Modülü Testi")
    logger.info("=" * 70)
    
    try:
        from config import Config
        
        config = Config()
        logger.info("✓ Config modülü başarıyla yüklendi")
        
        # Test değerleri
        camera_width = config.get('camera.width')
        model_type = config.get('depth_model.model_type')
        
        logger.info(f"  - Kamera genişliği: {camera_width}")
        logger.info(f"  - Model tipi: {model_type}")
        logger.info(f"  - Config dosyası: {config.config_path}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Config modülü hatası: {e}")
        return False


def test_camera():
    """Camera handler modülünü test eder."""
    logger.info("\n" + "=" * 70)
    logger.info("ADIM 3: Camera Handler Testi")
    logger.info("=" * 70)
    
    try:
        from camera_handler import CameraHandler
        import cv2
        
        logger.info("Kamera başlatılıyor (5 saniye test)...")
        
        camera = CameraHandler(device_id=0, width=640, height=480, fps_target=30)
        
        if not camera.start():
            logger.error("✗ Kamera başlatılamadı!")
            logger.error("  Olası nedenler:")
            logger.error("  1. Kamera kullanımda (başka uygulama)")
            logger.error("  2. Kamera driver sorunu")
            logger.error("  3. Kamera izni verilmemiş")
            return False
        
        logger.info("✓ Kamera başarıyla başlatıldı!")
        
        # 5 saniye boyunca frame yakala
        logger.info("5 saniye boyunca frame yakalanacak...")
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < 5:
            frame = camera.read_frame()
            if frame is not None:
                frame_count += 1
                
                # Her 30 frame'de bir bilgi ver
                if frame_count % 30 == 0:
                    fps = camera.get_fps()
                    logger.info(f"  Frame {frame_count} - FPS: {fps:.1f}")
        
        camera.stop()
        
        logger.info(f"✓ Test tamamlandı! Toplam {frame_count} frame yakalandı")
        logger.info(f"  Ortalama FPS: {frame_count / 5:.1f}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Kamera testi hatası: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ana test fonksiyonu."""
    logger.info("\n")
    logger.info("#" * 70)
    logger.info("# GÖREN GÖZ LAPTOP - SİSTEM TESTİ (Python 3.10+ için)")
    logger.info("#" * 70)
    logger.info("\n")
    
    # Python versiyonu kontrolü
    import sys
    python_version = sys.version_info
    logger.info(f"Python Versiyonu: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 10):
        logger.warning("⚠️ Python 3.10 veya üzeri önerilir!")
    elif python_version >= (3, 12) and python_version.releaselevel == 'alpha':
        logger.warning("⚠️ Python 3.12 alpha kullanıyorsunuz - kararsız olabilir!")
        logger.info("   Config testini yapıyorum, kamera testini atlıyorum...\n")
        
        # Sadece Config testi
        if not test_config():
            logger.error("\n❌ Config testi başarısız!")
            return
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ CONFIG TESTİ BAŞARILI!")
        logger.info("=" * 70)
        logger.info("\nNOT: Kamera ve diğer testler Python 3.10/3.11 gerektirir.")
        logger.info("Şimdilik config çalışıyor, diğer modülleri yazabiliriz!")
        logger.info("\nSonraki adımlar:")
        logger.info("  1. ✅ Config modülü çalışıyor")
        logger.info("  2. ✅ Depth estimator modülünü yazabiliriz")
        logger.info("  3. ✅ Visualizer modülünü yazabiliriz")
        logger.info("  4. ✅ Alert system modülünü yazabiliriz")
        logger.info("  5. ⚠️ Kamera testi Python 3.10/3.11 ile yapılmalı")
        logger.info("=" * 70)
        return
    
    # Tam test - Python 3.10/3.11 için
    logger.info("")
    
    # Test 1: Import
    if not test_imports():
        logger.error("\n❌ Import testi başarısız! Gerekli paketleri yükleyin.")
        logger.error("   Komut: pip install -r requirements.txt")
        return
    
    # Test 2: Config
    if not test_config():
        logger.error("\n❌ Config testi başarısız!")
        return
    
    # Test 3: Camera
    if not test_camera():
        logger.error("\n❌ Kamera testi başarısız!")
        logger.info("\nNOT: Kamera testi başarısız olsa bile proje devam ettirilebilir.")
        logger.info("     Kamera sorunlarını daha sonra çözebilirsiniz.")
        return
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ TÜM TESTLER BAŞARILI!")
    logger.info("=" * 70)
    logger.info("\nSonraki adımlar:")
    logger.info("  1. Depth estimator modülünü yazabilirsiniz")
    logger.info("  2. Visualizer modülünü yazabilirsiniz")
    logger.info("  3. Alert system modülünü yazabilirsiniz")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
