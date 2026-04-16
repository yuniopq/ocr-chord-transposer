# Importación de librerías necesarias
import streamlit as st
from streamlit_cropper import st_cropper  # Herramienta para seleccionar zonas de la imagen
import motor_acordes  # Módulo propio para detección y procesamiento de acordes
from PIL import Image  # Manejo de imágenes
import time
import os 

# Configuración inicial de la app
st.set_page_config(page_title="Chord Lens OCR", layout="wide")

# Inicialización de variables en sesión (persisten entre interacciones)
if 'acordes' not in st.session_state:
    st.session_state['acordes'] = []  # Lista de acordes detectados
if 'escaneado' not in st.session_state:
    st.session_state['escaneado'] = False  # Indica si ya se ha hecho el escaneo automático
if 'refresco' not in st.session_state:
    st.session_state['refresco'] = 0  # Forzar actualización del cropper

# Título principal
st.title("🎼 Transpositor de Acordes / 和弦变调器")

# Subida de imagen (partitura)
archivo = st.file_uploader("Subir partitura / 请上传乐谱", type=["png", "jpg", "jpeg"])

# Si el usuario ha subido una imagen
if archivo:
    # Abrir y convertir la imagen a RGB
    img = Image.open(archivo).convert("RGB")
    
    # Preparar nombre de salida
    nombre_base = os.path.splitext(archivo.name)[0]
    nombre_salida = f"{nombre_base}.jpg"
    
    # Paso 1: Escaneo automático de acordes
    if not st.session_state['escaneado']:
        if st.button("🚀 Paso 1: Escaneo automático / 第一步：自动扫描", type="primary", use_container_width=True):
            with st.spinner("Analizando la partitura... / 正在分析乐谱..."):
                # Detección global de acordes
                st.session_state['acordes'] = motor_acordes.detectar_acordes_global(img)
                st.session_state['escaneado'] = True
                st.rerun()  # Recargar la app

    # Si ya se ha realizado el escaneo
    if st.session_state['escaneado']:
        # División de la interfaz en dos columnas
        col_img, col_ctrl = st.columns([2, 1])

        # Columna izquierda: imagen y revisión
        with col_img:
            st.subheader("🧐 Paso 2: Revisión y corrección manual / 第二步：检查与手动修正")
            
            # Dibujar los acordes detectados sobre la imagen
            img_rev = motor_acordes.dibujar_revision(img, st.session_state['acordes'])
            
            # Configuración inicial de la "lupa" (zona seleccionable)
            w, h = img_rev.size
            cx, cy = w // 2, h // 2
            radio = min(75, w // 8, h // 8) 
            coordenadas_iniciales = (cx - radio, cx + radio, cy - radio, cy + radio)

            # Widget de selección de área (cropper)
            box = st_cropper(
                img_rev, 
                realtime_update=True, 
                box_color='red', 
                aspect_ratio=None, 
                return_type='box',
                default_coords=coordenadas_iniciales, 
                key=f"lupa_{st.session_state['refresco']}"  # Clave dinámica para refrescar
            )

        # Columna derecha: controles
        with col_ctrl:
            st.subheader("🛠️ Panel de control / 控制面板")
            
            # --- BOTÓN EXTRAER ACORDES EN ZONA ---
            if st.button("🔎 Extraer acordes de la zona / 提取选定区域的和弦", use_container_width=True):
                # Definir zona seleccionada
                zona = (box['top'], box['top'] + box['height'], box['left'], box['left'] + box['width'])
                
                with st.spinner("Buscando... / 正在搜索..."):
                    # Detectar nuevos acordes en la zona
                    nuevos = motor_acordes.pasar_lupa_en_zona(img, zona)
                    if nuevos:
                        # Añadir nuevos acordes detectados
                        st.session_state['acordes'].extend(nuevos)
                        st.session_state['refresco'] += 1 
                        st.success(f"✅ Detectado: {nuevos[0]['texto']} / 成功提取: {nuevos[0]['texto']}")
                        time.sleep(0.5) 
                        st.rerun()
                    else:
                        st.error("No se han detectado acordes. Ajuste el recuadro rojo e inténtelo de nuevo. / 未检测到和弦。请调整红框后重试。")

            # --- BOTÓN ELIMINAR ACORDES EN ZONA ---
            if st.button("❌ Eliminar acordes de la zona / 删除选定区域的和弦", use_container_width=True):
                # Límites de la zona seleccionada
                left, right = box['left'], box['left'] + box['width']
                top, bottom = box['top'], box['top'] + box['height']
                
                acordes_restantes = []
                borrados = 0
                
                # Recorrer acordes actuales
                for a in st.session_state['acordes']:
                    # Calcular centro del bounding box
                    cx_prep = (a["bbox"][0][0] + a["bbox"][2][0]) / 2.0
                    cy_prep = (a["bbox"][0][1] + a["bbox"][2][1]) / 2.0
                    
                    # Ajuste de coordenadas (normalización)
                    cx = (cx_prep - 100) / 2.0
                    cy = (cy_prep - 100) / 2.0

                    # Comprobar si está dentro de la zona
                    if left <= cx <= right and top <= cy <= bottom:
                        borrados += 1
                    else:
                        acordes_restantes.append(a)
                
                # Actualizar estado
                if borrados > 0:
                    st.session_state['acordes'] = acordes_restantes
                    st.session_state['refresco'] += 1
                    st.success(f"✅ Se han eliminado {borrados} acorde(s). / 已成功删除 {borrados} 个和弦。")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.warning("No hay acordes en la zona seleccionada para eliminar. / 该区域未找到可删除的和弦。")

            st.divider()
            
            # --- PASO 3: TRANSPOSICIÓN ---
            st.subheader("🪄 Paso 3: Transposición / 第三步：变调")
            
            # Slider para elegir semitonos
            tonos = st.slider("Reducir semitonos / 降半音数量", 0.0, 5.0, 1.0, 0.5)
            
            # Generar imagen final con acordes transpuestos
            if st.button("🚀 Generar y descargar / 生成并下载", type="primary", use_container_width=True):
                with st.spinner("Procesando la imagen final... / 正在生成最终图像..."):
                    res = motor_acordes.aplicar_transposicion(img, st.session_state['acordes'], tonos)
                    
                    # Mostrar resultado
                    st.image(res, caption="Resultado final / 最终结果")
                    
                    # Guardar y permitir descarga
                    res.save("final.jpg")
                    with open("final.jpg", "rb") as f:
                        st.download_button("⬇️ Descargar JPG / 下载 JPG", f, nombre_salida, "image/jpeg")

            # Botón para reiniciar la app
            if st.button("🗑️ Reiniciar / 重新开始"):
                st.session_state['acordes'] = []
                st.session_state['escaneado'] = False
                st.session_state['refresco'] = 0
                st.rerun()