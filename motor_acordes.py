import os
import re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
from paddleocr import PaddleOCR
import firebase_admin
from firebase_admin import credentials, firestore

# --- CONFIGURACIÓN FIREBASE ---
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# --- CONFIGURACIÓN NOTAS ---
NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
MAPEO_BEMOLES = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'}
NOTAS_SALIDA = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

# Inicialización OCR
ocr_ch = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
ocr_en = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)

def transponer_nota(nota_str, semitonos):
    limpia = re.sub(r"[^A-Ga-g#bmajdim7susadug0-9/]", "", nota_str)
    match = re.search(r"([A-G][#b]?)", limpia, re.IGNORECASE)
    if not match: return nota_str
    raiz_orig = match.group(1)
    raiz_cap = raiz_orig[0].upper() + (raiz_orig[1].lower() if len(raiz_orig) > 1 else "")
    resto = limpia.replace(raiz_orig, "", 1)
    raiz_n = MAPEO_BEMOLES.get(raiz_cap, raiz_cap)
    if raiz_n in NOTAS:
        idx = NOTAS.index(raiz_n)
        return NOTAS_SALIDA[(idx + semitonos) % 12] + resto
    return nota_str

def procesar_texto_mixto(texto, semitonos):
    if len(texto) > 25: return None
    patron = r"\b([A-G][#b]?(?:m|maj|7|sus|add)?)\b"
    matches = re.findall(patron, texto, re.IGNORECASE)
    if not matches: return None
    nuevo = texto
    for m in set(matches):
        nuevo = re.sub(r'\b' + re.escape(m) + r'\b', transponer_nota(m, semitonos), nuevo)
    return nuevo

def detectar_acordes_global(img_orig):
    w, h = img_orig.size
    img_zoom = img_orig.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
    prep = ImageEnhance.Contrast(ImageOps.grayscale(img_zoom)).enhance(3.0)
    prep = ImageOps.expand(prep, border=100, fill="white")
    res = ocr_ch.ocr(np.array(prep.convert("RGB")), cls=True)
    acordes = []
    if res[0]:
        for line in res[0]:
            texto_raw, boxes = line[1][0], line[0]
            if procesar_texto_mixto(texto_raw, 0):
                acordes.append({"texto": texto_raw, "bbox": boxes})
    return acordes

def pasar_lupa_en_zona(img_orig, zona):
    ymin, ymax, xmin, xmax = zona
    parche = img_orig.crop((xmin-5, ymin-5, xmax+5, ymax+5))
    parche_zoom = parche.resize((parche.width*4, parche.height*4), Image.Resampling.LANCZOS)
    res = ocr_en.ocr(np.array(parche_zoom.convert("RGB")), cls=True)
    encontrados = []
    if res and res[0]:
        for line in res[0]:
            texto_raw, boxes_p = line[1][0], line[0]
            if procesar_texto_mixto(texto_raw, 0):
                boxes_g = []
                for p in boxes_p:
                    gx = ((p[0]/4.0) + xmin-5)*2.0 + 100
                    gy = ((p[1]/4.0) + ymin-5)*2.0 + 100
                    boxes_g.append([gx, gy])
                encontrados.append({"texto": texto_raw, "bbox": boxes_g})
    return encontrados

def dibujar_revision(img_orig, acordes):
    w, h = img_orig.size
    img_zoom = img_orig.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
    canvas = ImageOps.expand(img_zoom, border=100, fill="white")
    draw = ImageDraw.Draw(canvas)
    for a in acordes:
        box = a["bbox"]
        draw.rectangle([box[0][0], box[0][1], box[2][0], box[2][1]], outline="magenta", width=5)
    res = canvas.crop((100, 100, canvas.width - 100, canvas.height - 100))
    return res.resize((w, h), Image.Resampling.LANCZOS)

def aplicar_transposicion(img_orig, acordes, semitonos_input):
    semitonos = -int(semitonos_input * 2)
    w, h = img_orig.size
    img_zoom = img_orig.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
    canvas = ImageOps.expand(img_zoom, border=100, fill="white")
    draw = ImageDraw.Draw(canvas)
    for a in acordes:
        nuevo = procesar_texto_mixto(a["texto"], semitonos)
        if nuevo:
            draw.polygon([tuple(p) for p in a["bbox"]], fill="white")
            draw.text((a["bbox"][0][0], a["bbox"][0][1]), nuevo, fill="blue")
    res = canvas.crop((100, 100, canvas.width - 100, canvas.height - 100))
    return res.resize((w, h), Image.Resampling.LANCZOS)
