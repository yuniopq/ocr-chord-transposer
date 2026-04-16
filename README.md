# 🎼 Chord Lens OCR

Aplicación web para **detectar, corregir y transponer acordes musicales directamente desde imágenes de partituras** usando OCR.

Incluye un flujo completo:
1. Escaneo automático de acordes
2. Corrección manual asistida (modo lupa)
3. Transposición y exportación final

## 🧠 Características

- 🔍 **OCR especializado en acordes musicales**
- 🎯 Detección automática + refinamiento manual por zonas
- 🔎 Modo "lupa" para corregir errores de OCR
- 🎼 **Transposición de acordes** (incluye slash chords: C/G, etc.)
- 🌍 Soporte multilenguaje (inglés / chino)
- 🖼️ Exportación de imagen final con acordes reescritos

---

## 🏗️ Estructura del proyecto

```

.
├── app.py                # Interfaz Streamlit
├── motor_acordes.py      # Lógica OCR + procesamiento musical
├── requirements.txt
└── README.md

````

---

## ⚙️ Instalación

### 1. Clonar repositorio
```bash
git clone https://github.com/yuniopq/ocr-chord-transposer.git
cd chord-lens-ocr
````

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv
source venv/bin/activate  # Linux / Mac
venv\Scripts\activate     # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## ▶️ Uso

Ejecuta la aplicación:

```bash
streamlit run app.py
```

Luego abre en el navegador:

```
http://localhost:8501
```

---

## 🔄 Flujo de uso

### 1. Escaneo automático

* Detecta acordes en toda la partitura

### 2. Corrección manual

* Usa la caja roja (cropper)
* ➕ Extraer acordes en zonas no detectadas
* ❌ Eliminar detecciones incorrectas

### 3. Transposición

* Ajusta semitonos con el slider
* Genera imagen final descargable

---

## 🧩 Tecnologías utilizadas

* **Streamlit** → interfaz web
* **PaddleOCR** → reconocimiento de texto
* **Pillow (PIL)** → procesamiento de imágenes
* **NumPy** → manejo de datos OCR
* **Regex** → detección de acordes

---

## 🎼 Lógica musical

* Soporte para:

  * Acordes mayores, menores, séptimas, etc.
  * Alteraciones (# / b)
  * Slash chords (ej: D/F#)
* Normalización interna a sostenidos
* Salida optimizada en bemoles (más legible musicalmente)

---

## ⚠️ Limitaciones

* OCR depende de la calidad de la imagen
* Tipografías muy estilizadas pueden fallar
* No detecta aún:

  * Diagramas de acordes
  * Notación musical tradicional (pentagramas)

---

## 👨‍💻 Autor

Proyecto desarrollado por Xiang

---