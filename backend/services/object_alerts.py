"""
Smart Object Alert Messages
===========================

Contextual warning messages for different object types.
Provides helpful guidance based on detected objects.
"""

# Turkish warning messages for critical objects
OBJECT_WARNINGS_TR = {
    'person': [
        'Önünüzde insan var. Dikkatli yürüyün.',
        'Karşınızda birisi duruyor. Yavaşlayın.',
        'İnsan tespit edildi. Yönünüzü değiştirin.',
    ],
    'stairs': [
        'MERDİVEN TESPİT EDİLDİ! Çok dikkatli olun!',
        'Önünüzde merdiven var. DURUN!',
        'Merdiven basamakları. El korkuluğunu tutun.',
    ],
    'car': [
        'ARABA TESPİT EDİLDİ! Geri çekilin!',
        'Araç yaklaşıyor. Yoldan çekilin.',
        'Trafikte araç var. Durun ve dinleyin.',
    ],
    'wall': [
        'Önünüzde duvar var. Sağa veya sola dönün.',
        'Duvara yaklaşıyorsunuz. Yön değiştirin.',
        'Engel: Duvar. Durun.',
    ],
    'door': [
        'Kapı tespit edildi. Kolunu uzat.',
        'Önünüzde kapı var. Dikkatli açın.',
        'Kapı girişi. Yavaş ilerleyin.',
    ],
    'chair': [
        'Sandalye tespit edildi. Etrafından dolaşın.',
        'Önünüzde sandalye var. Dikkat edin.',
        'Mobilya: Sandalye. Sağa kayın.',
    ],
    'dining table': [
        'Masa tespit edildi. Kenara çekilin.',
        'Önünüzde masa var. Dokunarak geçin.',
        'Büyük mobilya: Masa. Dikkatli yürüyün.',
    ],
    'truck': [
        'KAMYON TESPİT EDİLDİ! Hemen geri çekilin!',
        'Büyük araç yaklaşıyor. Tehlike!',
        'Kamyon var. Güvenli mesafe alın.',
    ],
    'bus': [
        'OTOBÜS TESPİT EDİLDİ! Yoldan çekilin!',
        'Otobüs geliyor. Dikkatli olun.',
        'Toplu taşıma aracı. Güvenli mesafe.',
    ],
    'motorcycle': [
        'Motosiklet tespit edildi. Dikkat!',
        'İki tekerlekli araç yaklaşıyor.',
        'Motosiklet sesi dinleyin.',
    ],
    'bicycle': [
        'Bisiklet tespit edildi. Dikkatli olun.',
        'Bisikletli geçiyor. Bekleyin.',
        'İki tekerlekli araç. Yol verin.',
    ],
    'traffic light': [
        'Trafik ışığı tespit edildi.',
        'Kavşakta trafik ışığı var.',
        'Işıklı kavşak. Sesi dinleyin.',
    ],
    'stop sign': [
        'DUR işareti tespit edildi.',
        'Kavşakta dur levhası var.',
        'Dur işareti. Dikkatli geçin.',
    ],
}

# English warning messages
OBJECT_WARNINGS_EN = {
    'person': [
        'Person ahead. Walk carefully.',
        'Someone is standing in front. Slow down.',
        'Person detected. Change direction.',
    ],
    'stairs': [
        'STAIRS DETECTED! Be very careful!',
        'Stairs ahead. STOP!',
        'Staircase. Hold the handrail.',
    ],
    'car': [
        'CAR DETECTED! Step back!',
        'Vehicle approaching. Move aside.',
        'Car in traffic. Stop and listen.',
    ],
    'wall': [
        'Wall ahead. Turn left or right.',
        'Approaching a wall. Change direction.',
        'Obstacle: Wall. Stop.',
    ],
    'door': [
        'Door detected. Reach out.',
        'Door ahead. Open carefully.',
        'Door entrance. Go slowly.',
    ],
    'chair': [
        'Chair detected. Walk around it.',
        'Chair ahead. Be careful.',
        'Furniture: Chair. Move right.',
    ],
    'dining table': [
        'Table detected. Move to the side.',
        'Table ahead. Navigate by touch.',
        'Large furniture: Table. Walk carefully.',
    ],
    'truck': [
        'TRUCK DETECTED! Move back immediately!',
        'Large vehicle approaching. Danger!',
        'Truck present. Keep safe distance.',
    ],
    'bus': [
        'BUS DETECTED! Move away from road!',
        'Bus coming. Be careful.',
        'Public transport. Safe distance.',
    ],
    'motorcycle': [
        'Motorcycle detected. Attention!',
        'Two-wheeler approaching.',
        'Motorcycle. Listen for sound.',
    ],
    'bicycle': [
        'Bicycle detected. Be careful.',
        'Cyclist passing. Wait.',
        'Two-wheeler. Give way.',
    ],
    'traffic light': [
        'Traffic light detected.',
        'Traffic signal at intersection.',
        'Lighted intersection. Listen for audio.',
    ],
    'stop sign': [
        'STOP sign detected.',
        'Stop sign at intersection.',
        'Stop sign. Cross carefully.',
    ],
}


def get_object_warning(object_name: str, language: str = 'tr', variant: int = 0) -> str:
    """
    Get contextual warning message for detected object.
    
    Args:
        object_name: Object class name (e.g., 'person', 'car')
        language: 'tr' for Turkish, 'en' for English
        variant: Message variant (0, 1, or 2) for variety
    
    Returns:
        Warning message string
    """
    warnings = OBJECT_WARNINGS_TR if language == 'tr' else OBJECT_WARNINGS_EN
    
    if object_name in warnings:
        messages = warnings[object_name]
        variant_idx = min(variant, len(messages) - 1)
        return messages[variant_idx]
    
    # Default fallback message
    if language == 'tr':
        return f'{object_name} tespit edildi. Dikkatli olun.'
    else:
        return f'{object_name} detected. Be careful.'


def get_distance_context(distance: float, language: str = 'tr') -> str:
    """
    Get distance-based context message.
    
    Args:
        distance: Distance in meters
        language: 'tr' or 'en'
    
    Returns:
        Distance context string
    """
    if language == 'tr':
        if distance < 0.5:
            return 'ÇOK YAKIN!'
        elif distance < 1.0:
            return 'Yakın mesafede.'
        elif distance < 2.0:
            return 'Orta mesafede.'
        else:
            return 'Uzak mesafede.'
    else:
        if distance < 0.5:
            return 'VERY CLOSE!'
        elif distance < 1.0:
            return 'At close range.'
        elif distance < 2.0:
            return 'At medium range.'
        else:
            return 'At far range.'
