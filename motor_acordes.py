import os
import re
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
from paddleocr import PaddleOCR

NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
MAPEO_BEMOLES = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'}
NOTAS_SALIDA = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

# Motores OCR / OCR 引擎
ocr_ch = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False, det_db_thresh=0.005)
ocr_en = PaddleOCR(use_angle_cls=True, lang='en', show_log=False, det_db_thresh=0.001)

def transponer_nota(nota_str, semitonos):
    if '/' in nota_str:
        partes = nota_str.split('/')
        return transponer_nota(partes[0], semitonos) + "/" + transponer_nota(partes[1], semitonos)
    
    limpia = re.sub(r"[^A-Ga-g#bmajdim7susadug0-9]", "", nota_str)
    match = re.search(r"([A-G][#b]?)", limpia, re.IGNORECASE)
    if not match: return nota_str

    raiz_orig = match.group(1)
    raiz_cap = raiz_orig[0].upper() + (raiz_orig[1].lower() if len(raiz_orig) > 1 else "")
    resto = limpia.replace(raiz_orig, "", 1)
    
    if resto.upper() == "M": resto = "m"
    elif "maj" in resto.lower(): resto = "maj" + resto.lower().split("maj")[-1]
    else: resto = resto.replace("M", "m")

    raiz_n = MAPEO_BEMOLES.get(raiz_cap, raiz_cap)
    if raiz_n in NOTAS:
        idx = NOTAS.index(raiz_n)
        return NOTAS_SALIDA[(idx + semitonos) % 12] + resto
    return nota_str

def procesar_texto_mixto(texto, semitonos):
    PALABRAS_ESTRUCTURALES = ['CHORUS', 'INTRO', 'VERSE', 'BRIDGE', '制作', '原调']
    if any(p in texto.upper() for p in PALABRAS_ESTRUCTURALES) or len(texto) > 25:
        return None
        
    patron = r"\b([A-G][#b]?(?:m|maj|dim|7|sus|add|aug|[0-9])*(?:/[A-G][#b]?(?:m|maj|dim|7|sus|add|aug|[0-9])*)?)\b"
    matches = re.findall(patron, texto, re.IGNORECASE)
    matches = [m for m in matches if any(n in m.upper() for n in "ABCDEFG")]
    if not matches: return None
    
    nuevo = texto
    for m in sorted(list(set(matches)), key=len, reverse=True):
        nueva_n = transponer_nota(m, semitonos)
        nuevo = re.sub(r'\b' + re.escape(m) + r'\b', nueva_n, nuevo)
    return nuevo

def detectar_acordes_global(img_orig, zonas_excluir=[]):
    """Escaneo inicial de toda la página / 全页初步扫描"""
    w, h = img_orig.size
    img_zoom = img_orig.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
    img_gray = ImageOps.grayscale(img_zoom)
    img_gray = ImageEnhance.Contrast(img_gray).enhance(3.0)
    prep = ImageOps.expand(img_gray, border=100, fill="white")

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
    
    # Margen de seguridad para no cortar letras / 添加少许边缘余量以防裁剪字母
    w_img, h_img = img_orig.size
    ymin, ymax = max(0, ymin - 5), min(h_img, ymax + 5)
    xmin, xmax = max(0, xmin - 5), min(w_img, xmax + 5)

    parche = img_orig.crop((xmin, ymin, xmax, ymax))
    w_p, h_p = parche.size
    parche_zoom = parche.resize((w_p * 4, h_p * 4), Image.Resampling.LANCZOS)
    
    parche_gray = ImageOps.grayscale(parche_zoom)
    parche_prep = ImageEnhance.Contrast(parche_gray).enhance(2.0)
    
    res = ocr_en.ocr(np.array(parche_prep.convert("RGB")), cls=True)
    
    encontrados = []
    if res and res[0]:
        for line in res[0]:
            texto_raw, boxes_p = line[1][0], line[0]
            if procesar_texto_mixto(texto_raw, 0):
                boxes_g = []
                for p in boxes_p:
                    gx = ((p[0] / 4.0) + xmin) * 2.0 + 100
                    gy = ((p[1] / 4.0) + ymin) * 2.0 + 100
                    boxes_g.append([gx, gy])
                encontrados.append({"texto": texto_raw, "bbox": boxes_g})
    return encontrados

def dibujar_revision(img_orig, acordes):
    """Marca lo detectado en magenta para revisión visual / 用紫红色标记检测到的内容以供复查"""
    w, h = img_orig.size
    img_zoom = img_orig.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
    canvas = ImageOps.expand(img_zoom, border=100, fill="white")
    draw = ImageDraw.Draw(canvas)
    
    try: font = ImageFont.truetype("arial.ttf", 40)
    except: font = ImageFont.load_default()

    for a in acordes:
        box = a["bbox"]
        draw.rectangle([box[0][0], box[0][1], box[2][0], box[2][1]], outline="magenta", width=5)
        draw.text((box[0][0], box[0][1]-45), a["texto"], fill="magenta", font=font)

    res = canvas.crop((100, 100, canvas.width - 100, canvas.height - 100))
    return res.resize((w, h), Image.Resampling.LANCZOS)

def aplicar_transposicion(img_orig, acordes, semitonos_input):
    semitonos = -int(semitonos_input * 2)
    w, h = img_orig.size
    img_zoom = img_orig.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
    canvas = ImageOps.expand(img_zoom, border=100, fill="white")
    draw = ImageDraw.Draw(canvas)

    alturas = [a["bbox"][2][1] - a["bbox"][0][1] for a in acordes]
    font_size = max(20, int((sum(alturas)/len(alturas)) * 0.8)) if alturas else 30
    
    try: font = ImageFont.truetype("arial.ttf", font_size)
    except: font = ImageFont.load_default()

    for a in acordes:
        nuevo = procesar_texto_mixto(a["texto"], semitonos)
        if nuevo:
            draw.polygon([tuple(p) for p in a["bbox"]], fill="white")
            draw.text((a["bbox"][0][0], a["bbox"][0][1]), nuevo, fill="blue", font=font)

    res = canvas.crop((100, 100, canvas.width - 100, canvas.height - 100))
    return res.resize((w, h), Image.Resampling.LANCZOS)
