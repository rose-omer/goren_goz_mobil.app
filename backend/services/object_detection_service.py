"""
Object Detection Service
========================

YOLOv11-Nano based real-time object detection for outdoor navigation.
Detects common objects and provides Turkish/English labels with directional guidance.

Upgraded from YOLOv8 to YOLOv11 for:
- +6% better accuracy (mAP)
- +30% faster on CPU
- -22% fewer parameters
"""

import logging
import numpy as np
from typing import List, Dict, Optional
from pathlib import Path
import torch

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logging.warning("Ultralytics not available. Object detection disabled.")

from core.config import get_settings

logger = logging.getLogger(__name__)


class ObjectDetectionService:
    """
    Service for detecting objects in images using YOLOv11-Nano.
    
    Optimized for outdoor navigation with focus on collision-relevant objects.
    Provides directional guidance in Turkish for visually impaired users.
    """
    
    # Turkish translations for COCO classes - EXPANDED for outdoor use
    TURKISH_LABELS = {
        # İNSANLAR VE HAYVANLAR
        'person': 'insan',
        'bird': 'kuş',
        'cat': 'kedi',
        'dog': 'köpek',
        'horse': 'at',
        'sheep': 'koyun',
        'cow': 'inek',
        'elephant': 'fil',
        'bear': 'ayı',
        'zebra': 'zebra',
        'giraffe': 'zürafa',
        
        # ARAÇLAR - Trafik tehlikesi
        'bicycle': 'bisiklet',
        'car': 'araba',
        'motorcycle': 'motosiklet',
        'airplane': 'uçak',
        'bus': 'otobüs',
        'train': 'tren',
        'truck': 'kamyon',
        'boat': 'tekne',
        
        # DIŞ MEKAN NESNELERİ - Önemli!
        'traffic light': 'trafik ışığı',
        'fire hydrant': 'yangın musluğu',
        'stop sign': 'dur işareti',
        'parking meter': 'park sayacı',
        'bench': 'bank',
        'pole': 'direk',  # Elektrik direği
        'street light': 'sokak lambası',
        'trash can': 'çöp kutusu',
        'mailbox': 'posta kutusu',
        'fire hydrant': 'yangın musluğu',
        
        # YAPISAL NESNELER - Çarpma riski
        'door': 'kapı',
        'wall': 'duvar',
        'window': 'pencere',
        'stairs': 'merdiven',
        'fence': 'çit',
        'gate': 'geçit',
        'pillar': 'sütun',
        'column': 'kolon',
        
        # MOBİLYA VE EV İÇİ
        'chair': 'sandalye',
        'couch': 'kanepe',
        'bed': 'yatak',
        'dining table': 'masa',
        'toilet': 'tuvalet',
        'tv': 'televizyon',
        'laptop': 'dizüstü bilgisayar',
        'mouse': 'fare',
        'keyboard': 'klavye',
        'cell phone': 'cep telefonu',
        'refrigerator': 'buzdolabı',
        'oven': 'fırın',
        'sink': 'lavabo',
        'microwave': 'mikrodalga',
        
        # EL ÇANTALARI VE ZEMİN ENGELLERİ
        'backpack': 'sırt çantası',
        'umbrella': 'şemsiye',
        'handbag': 'el çantası',
        'suitcase': 'valiz',
        'tie': 'kravat',
        
        # DİĞER NESNELER
        'potted plant': 'saksı bitkisi',
        'book': 'kitap',
        'clock': 'saat',
        'vase': 'vazo',
        'scissors': 'makas',
        'teddy bear': 'oyuncak ayı',
        'bottle': 'şişe',
        'cup': 'bardak',
        'fork': 'çatal',
        'knife': 'bıçak',
        'spoon': 'kaşık',
        'bowl': 'kase',
        'wine glass': 'şarap kadehi',
        
        # SPOR EKİPMANLARI
        'frisbee': 'frizbi',
        'skis': 'kayak',
        'snowboard': 'snowboard',
        'sports ball': 'top',
        'kite': 'uçurtma',
        'baseball bat': 'beyzbol sopası',
        'baseball glove': 'beyzbol eldiveni',
        'skateboard': 'kaykay',
        'surfboard': 'sörf tahtası',
        'tennis racket': 'tenis raketi',
        
        # YİYECEKLER
        'banana': 'muz',
        'apple': 'elma',
        'sandwich': 'sandviç',
        'orange': 'portakal',
        'broccoli': 'brokoli',
        'carrot': 'havuç',
        'hot dog': 'sosisli',
        'pizza': 'pizza',
        'donut': 'donut',
        'cake': 'pasta',
    }
    
    # Priority objects for collision avoidance (higher = more important)
    # Optimized for OUTDOOR NAVIGATION
    PRIORITY_OBJECTS = {
        # KRİTİK - Acil tehlike (10)
        'person': 10,          # İnsan - En yüksek öncelik
        'car': 10,             # Araba - Trafik tehlikesi
        'truck': 10,           # Kamyon - Büyük araç
        'bus': 10,             # Otobüs - Büyük araç
        'motorcycle': 10,      # Motosiklet - Hızlı hareket
        'bicycle': 9,          # Bisiklet - Hareketli engel
        
        # YAPISAL ENGELLERr (9)
        'wall': 9,             # Duvar - Çarpma riski
        'door': 9,             # Kapı - Geçiş engeli
        'stairs': 9,           # Merdiven - Düşme riski
        'pole': 9,             # Direk - Elektrik direği
        'pillar': 9,           # Sütun
        'column': 9,           # Kolon
        'fence': 8,            # Çit
        
        # DIŞ MEKAN ENGELLERİ (8)
        'fire hydrant': 8,     # Yangın musluğu - Kaldırım engeli
        'bench': 8,            # Bank - Oturma yeri
        'trash can': 8,        # Çöp kutusu
        'parking meter': 8,    # Park sayacı
        'mailbox': 8,          # Posta kutusu
        'street light': 8,     # Sokak lambası direği
        
        # TRAFİK İŞARETLERİ (8)
        'traffic light': 8,    # Trafik ışığı
        'stop sign': 8,        # Dur işareti
        
        # MOBİLYA ENGELLERİ (7-8)
        'chair': 8,            # Sandalye - Yaygın engel
        'dining table': 8,     # Masa - Yaygın engel
        'couch': 7,            # Kanepe - Büyük mobilya
        'bed': 7,              # Yatak - Büyük mobilya
        'refrigerator': 7,     # Buzdolabı
        
        # ZEMİN ENGELLERİ (6)
        'potted plant': 6,     # Saksı - Küçük engel
        'backpack': 6,         # Çanta - Zemin engeli
        'suitcase': 6,         # Valiz - Zemin engeli
        'umbrella': 6,         # Şemsiye
        
        # HAYVANLAR (5-7)
        'dog': 7,              # Köpek - Hareketli
        'cat': 5,              # Kedi - Küçük
        
        # DİĞER (3-5)
        'sports ball': 4,      # Top
        'skateboard': 5,       # Kaykay
    }
    
    # Yön mesajları (Türkçe)
    DIRECTION_MESSAGES = {
        'left': {
            'prefix': 'Sol tarafta',
            'warning': 'Sola gitmeyin!',
            'info': 'solunuzda'
        },
        'center': {
            'prefix': 'Önünüzde',
            'warning': 'Durun!',
            'info': 'tam karşınızda'
        },
        'right': {
            'prefix': 'Sağ tarafta',
            'warning': 'Sağa gitmeyin!',
            'info': 'sağınızda'
        }
    }
    
    def __init__(self):
        """Initialize object detection service with YOLOv11-Nano."""
        self.settings = get_settings()
        self.model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        if not YOLO_AVAILABLE:
            logger.warning("YOLO not available - object detection disabled")
            return
        
        try:
            # Standard YOLO (80 COCO sınıfı - günlük nesneler)
            # person, car, chair, bottle, laptop vb. tanır
            # Get absolute path to models directory
            models_dir = Path(__file__).parent.parent / "models"
            
            logger.info("Loading YOLOv11-Nano (COCO 80 classes)...")
            try:
                # Try YOLOv11n first
                model_path = models_dir / 'yolo11n.pt'
                if not model_path.exists():
                     # Fallback to current directory if not found (development mode)
                     model_path = 'yolo11n.pt'
                     
                self.model = YOLO(str(model_path))
                self.model_name = "YOLOv11-Nano"
                logger.info(f"✓ YOLOv11-Nano loaded on {self.device}")
            except Exception as e1:
                logger.warning(f"YOLOv11n failed ({e1}), trying YOLOv8...")
                # Try YOLOv8 fallback
                try:
                    model_path_v8 = models_dir / 'yolov8n.pt'
                    if not model_path_v8.exists():
                        model_path_v8 = 'yolov8n.pt'
                    
                    self.model = YOLO(str(model_path_v8))
                    self.model_name = "YOLOv8-Nano"
                except Exception as e2:
                    logger.error(f"Failed to load any YOLO model: {e2}")
                    raise
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.model = None
    
    def detect(
        self,
        image: np.ndarray,
        confidence_threshold: float = 0.5,  # ✅ Balanced (0.4 was too many detections)
        max_objects: int = 10,               # Standard
        depth_map: Optional[np.ndarray] = None
    ) -> List[Dict]:
        """
        Detect objects in image.
        
        Args:
            image: Input image (BGR format, numpy array)
            confidence_threshold: Minimum confidence score (0-1)
            max_objects: Maximum number of objects to return
            depth_map: Optional depth map for distance calculation (same size as image)
        
        Returns:
            List of detected objects with:
                - name: Object name (English)
                - name_tr: Turkish translation
                - confidence: Detection confidence (0-1)
                - bbox: Bounding box [x1, y1, x2, y2]
                - center: Center point [x, y]
                - distance: Distance in meters (if depth_map provided)
                - priority: Collision priority (0-10)
                - region: Screen region (left/center/right)
        """
        if self.model is None:
            return []
        
        try:
            # Run inference
            results = self.model(image, verbose=False, conf=confidence_threshold)
            
            if len(results) == 0 or len(results[0].boxes) == 0:
                return []
            
            # Parse results
            detections = []
            height, width = image.shape[:2]
            
            for box in results[0].boxes:
                # Get box data
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                
                # Get class name
                class_name = self.model.names[cls_id]
                
                # Calculate center and region
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                # Determine region (left/center/right)
                if center_x < width / 3:
                    region = 'left'
                elif center_x < 2 * width / 3:
                    region = 'center'
                else:
                    region = 'right'
                
                # Get Turkish name and priority
                name_tr = self.TURKISH_LABELS.get(class_name, class_name)
                priority = self.PRIORITY_OBJECTS.get(class_name, 5)
                
                # Calculate distance from depth map if available
                distance = 0.0
                if depth_map is not None:
                    try:
                        # Sample depth at object center
                        cy, cx = int(center_y), int(center_x)
                        # Ensure coordinates are within bounds
                        cy = max(0, min(cy, depth_map.shape[0] - 1))
                        cx = max(0, min(cx, depth_map.shape[1] - 1))
                        distance = float(depth_map[cy, cx])
                    except Exception as e:
                        logger.warning(f"Failed to get distance for {class_name}: {e}")
                        distance = 0.0
                
                detection = {
                    'name': class_name,
                    'name_tr': name_tr,
                    'confidence': round(conf, 3),
                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                    'center': [float(center_x), float(center_y)],
                    'distance': distance,  # ✅ Now includes actual distance
                    'priority': priority,
                    'region': region,
                    'direction_message': self._generate_direction_message(
                        class_name, name_tr, region, priority
                    )
                }
                
                detections.append(detection)
            
            # Sort by priority (high to low) and confidence
            detections.sort(key=lambda x: (x['priority'], x['confidence']), reverse=True)
            
            # Limit number of objects
            detections = detections[:max_objects]
            
            logger.debug(f"Detected {len(detections)} objects")
            return detections
            
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return []
    
    def _generate_direction_message(
        self, 
        class_name: str, 
        name_tr: str, 
        region: str, 
        priority: int
    ) -> str:
        """
        Generate Turkish directional guidance message.
        
        Examples:
            - "Önünüzde insan var."
            - "Sol tarafta duvar var. Sola gitmeyin!"
            - "Sağ tarafta araba var. Dikkat!"
        """
        direction = self.DIRECTION_MESSAGES.get(region, self.DIRECTION_MESSAGES['center'])
        prefix = direction['prefix']
        
        # Base message
        message = f"{prefix} {name_tr} var."
        
        # Add warning for high priority objects
        if priority >= 9:
            if region == 'center':
                message += " Durun!"
            elif region == 'left':
                message += " Sola gitmeyin!"
            elif region == 'right':
                message += " Sağa gitmeyin!"
        elif priority >= 7:
            message += " Dikkat!"
        
        return message
    
    def get_priority_object(self, detections: List[Dict], region: Optional[str] = None) -> Optional[Dict]:
        """
        Get the highest priority object, optionally filtered by region.
        
        Args:
            detections: List of detected objects
            region: Optional region filter ('left'/'center'/'right')
        
        Returns:
            Highest priority object or None
        """
        if not detections:
            return None
        
        # Filter by region if specified
        if region:
            filtered = [d for d in detections if d['region'] == region]
            if not filtered:
                return None
            return filtered[0]  # Already sorted by priority
        
        return detections[0]  # Already sorted by priority
    
    def get_navigation_summary(self, detections: List[Dict]) -> Dict:
        """
        Generate a navigation summary with obstacles in each direction.
        
        Returns:
            Dict with:
                - left: List of objects on the left
                - center: List of objects in center
                - right: List of objects on the right
                - announcement: Single most important message to speak
                - all_messages: List of all direction messages
        """
        summary = {
            'left': [],
            'center': [],
            'right': [],
            'announcement': '',
            'all_messages': []
        }
        
        if not detections:
            summary['announcement'] = "Yol açık. Güvenle ilerleyebilirsiniz."
            return summary
        
        # Group by region
        for det in detections:
            region = det.get('region', 'center')
            summary[region].append({
                'name_tr': det['name_tr'],
                'priority': det['priority'],
                'message': det.get('direction_message', '')
            })
            if det.get('direction_message'):
                summary['all_messages'].append(det['direction_message'])
        
        # Generate main announcement (highest priority object)
        top_obj = detections[0]
        summary['announcement'] = top_obj.get('direction_message', 
            f"{top_obj['name_tr']} tespit edildi.")
        
        return summary
    
    def get_safe_directions(self, detections: List[Dict]) -> List[str]:
        """
        Get list of safe directions to move.
        
        Returns:
            List of safe directions: ['left', 'center', 'right']
        """
        regions_with_danger = set()
        
        for det in detections:
            if det.get('priority', 0) >= 8:  # High priority = danger
                regions_with_danger.add(det.get('region', 'center'))
        
        all_directions = {'left', 'center', 'right'}
        safe = list(all_directions - regions_with_danger)
        
        return safe


# Singleton instance
_object_detection_service = None


def get_object_detection_service() -> ObjectDetectionService:
    """Get or create object detection service singleton."""
    global _object_detection_service
    if _object_detection_service is None:
        _object_detection_service = ObjectDetectionService()
    return _object_detection_service

