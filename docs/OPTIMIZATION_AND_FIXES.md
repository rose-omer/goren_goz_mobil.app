# 🛠️ OpenVINO ve Model Optimizasyon Süreci - Sorunlar ve Çözümler

Bu belge, Gören Göz Mobil Backend projesinde derinlik tahmini (depth estimation) modellerinin optimizasyonu ve OpenVINO entegrasyonu sırasında karşılaşılan teknik zorlukları ve uygulanan çözümleri özetler.

---

## 🚀 Genel Sonuç
- **Önceki Durum (PyTorch):** ~300ms (Total Pipeline)
- **Yeni Durum (OpenVINO):** ~110ms (Total Pipeline) ⚡
- **Performans Artışı:** ~2.7 kat hızlanma!

---

## 🔍 Karşılaşılan Sorunlar ve Çözümleri

### 1. NumPy Versiyon Uyumsuzluğu
*   **Sorun:** OpenVINO SDK'sı `numpy < 2.2` versiyonunu şart koşarken, projede kullanılan diğer paketler (örneğin `opencv-python`) `numpy >= 2.0` istiyordu. Eski `1.26` versiyonu ise yeni ONNX export özellikleri ile çakışıyordu.
*   **Çözüm:** NumPy versiyonu hassas bir şekilde ayarlandı.
    ```bash
    pip install "numpy>=2.0,<2.2" --force-reinstall
    # Sonuç: numpy 2.1.3 kuruldu (Sweet Spot).
    ```

### 2. Eksik Bağımlılık: `onnxscript`
*   **Sorun:** PyTorch modellerini OpenVINO IR formatına çevirirken ONNX export aşamasında `ModuleNotFoundError: No module named 'onnxscript'` hatası alındı.
*   **Çözüm:** `onnxscript` ve ilgili yardımcı paketler kurularak export pipeline'ı düzeltildi.
    ```bash
    pip install onnxscript
    ```

### 3. Deprecated OpenVINO Convert API
*   **Sorun:** Kodda kullanılan `openvino.tools.mo.convert_model()` API'si OpenVINO 2024.x sürümlerinde deprecated olmuş ve bazı parametreleri (`output_model`) tanımaz hale gelmişti. Bu durum model çevirme işlemini durduruyordu.
*   **Çözüm:** Modern OpenVINO API (`ov.convert_model` ve `ov.save_model`) kullanımına geçildi.
    ```python
    import openvino as ov
    ov_model = ov.convert_model(str(onnx_path))
    ov.save_model(ov_model, str(model_xml))
    ```

### 4. ONNX Opset Versiyon Hatası
*   **Sorun:** Varsayılan opset version 11, MiDaS modelinin bazı katmanlarını OpenVINO'ya uygun şekilde export edemiyordu.
*   **Çözüm:** Opset version **17**'ye yükseltildi ve dinamik axis (batch_size) desteği eklendi.

### 5. Model Boyutu ve Uyumluluk (Depth Anything v2 & ZoeDepth)
*   **Sorun:** `Depth Anything v2` için indirilen model dosyaları kod mimarisiyle uyuşmadı (shape mismatch). `ZoeDepth-NK` modeli ise 1.35GB boyutuyla mobil backend için aşırı hantal bulundu.
*   **Çözüm:** Hafif, stabil ve kendini kanıtlamış olan **MiDaS_small** modelinde kalınarak bu modelin **OpenVINO** ile optimize edilmesine karar verildi.

---

## 📈 Performans Metrikleri

| Bileşen | PyTorch Backend | OpenVINO Backend (Yeni) | Kazanım |
| :--- | :--- | :--- | :--- |
| **Depth Inference** | ~120ms | **~40-60ms** | 2-3 kat ⚡ |
| **Total Analyze Time** | ~300ms | **~110ms** | ~2.7 kat 🚀 |
| **FPS (Kamera Akışı)** | 4.3 | **9.1** | +%110 ✅ |

---

## 📝 Sonraki Adımlar için Notlar
- Modeller `backend/models/openvino/` klasörü altında IR formatında (`.xml`, `.bin`) saklanmaktadır.
- Cihaz seçiminde `AUTO` kullanılarak Intel GPU varsa otomatik kullanılması sağlanmıştır.
- Herhangi bir hata durumunda sistem güvenli şekilde PyTorch'a (CPU) geri döner (Fallback Mechanism).
