import streamlit as st
from streamlit_cropper import st_cropper
import motor_acordes
from PIL import Image
import time
import os 

st.set_page_config(page_title="Chord Lens OCR", layout="wide")

if 'acordes' not in st.session_state:
    st.session_state['acordes'] = []
if 'escaneado' not in st.session_state:
    st.session_state['escaneado'] = False
if 'refresco' not in st.session_state:
    st.session_state['refresco'] = 0 

st.title("🎼 Transpositor de Acordes / 和弦变调器")

archivo = st.file_uploader("Subir partitura / 请上传乐谱", type=["png", "jpg", "jpeg"])

if archivo:
    img = Image.open(archivo).convert("RGB")
    
    nombre_base = os.path.splitext(archivo.name)[0]
    nombre_salida = f"{nombre_base}.jpg"
    
    if not st.session_state['escaneado']:
        if st.button("🚀 Paso 1: Escaneo automático / 第一步：自动扫描", type="primary", use_container_width=True):
            with st.spinner("Analizando la partitura... / 正在分析乐谱..."):
                st.session_state['acordes'] = motor_acordes.detectar_acordes_global(img)
                st.session_state['escaneado'] = True
                st.rerun()

    if st.session_state['escaneado']:
        col_img, col_ctrl = st.columns([2, 1])

        with col_img:
            st.subheader("🧐 Paso 2: Revisión y corrección manual / 第二步：检查与手动修正")
            
            img_rev = motor_acordes.dibujar_revision(img, st.session_state['acordes'])
            
            # Cálculo de la lupa en tamaño reducido
            w, h = img_rev.size
            cx, cy = w // 2, h // 2
            radio = min(75, w // 8, h // 8) 
            coordenadas_iniciales = (cx - radio, cx + radio, cy - radio, cy + radio)

            box = st_cropper(
                img_rev, 
                realtime_update=True, 
                box_color='red', 
                aspect_ratio=None, 
                return_type='box',
                default_coords=coordenadas_iniciales, 
                key=f"lupa_{st.session_state['refresco']}" 
            )

        with col_ctrl:
            st.subheader("🛠️ Panel de control / 控制面板")
            
            # --- BOTÓN EXTRAER ---
            if st.button("🔎 Extraer acordes de la zona / 提取选定区域的和弦", use_container_width=True):
                zona = (box['top'], box['top'] + box['height'], box['left'], box['left'] + box['width'])
                
                with st.spinner("Buscando... / 正在搜索..."):
                    nuevos = motor_acordes.pasar_lupa_en_zona(img, zona)
                    if nuevos:
                        st.session_state['acordes'].extend(nuevos)
                        st.session_state['refresco'] += 1 
                        st.success(f"✅ Detectado: {nuevos[0]['texto']} / 成功提取: {nuevos[0]['texto']}")
                        time.sleep(0.5) 
                        st.rerun()
                    else:
                        st.error("No se han detectado acordes. Ajuste el recuadro rojo e inténtelo de nuevo. / 未检测到和弦。请调整红框后重试。")

            # --- BOTÓN ELIMINAR ---
            if st.button("❌ Eliminar acordes de la zona / 删除选定区域的和弦", use_container_width=True):
                left, right = box['left'], box['left'] + box['width']
                top, bottom = box['top'], box['top'] + box['height']
                
                acordes_restantes = []
                borrados = 0
                
                for a in st.session_state['acordes']:
                    cx_prep = (a["bbox"][0][0] + a["bbox"][2][0]) / 2.0
                    cy_prep = (a["bbox"][0][1] + a["bbox"][2][1]) / 2.0
                    
                    cx = (cx_prep - 100) / 2.0
                    cy = (cy_prep - 100) / 2.0

                    if left <= cx <= right and top <= cy <= bottom:
                        borrados += 1
                    else:
                        acordes_restantes.append(a)
                
                if borrados > 0:
                    st.session_state['acordes'] = acordes_restantes
                    st.session_state['refresco'] += 1
                    st.success(f"✅ Se han eliminado {borrados} acorde(s). / 已成功删除 {borrados} 个和弦。")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.warning("No hay acordes en la zona seleccionada para eliminar. / 该区域未找到可删除的和弦。")

            st.divider()
            
            st.subheader("🪄 Paso 3: Transposición / 第三步：变调")
            tonos = st.slider("Reducir semitonos / 降半音数量", 0.0, 5.0, 1.0, 0.5)
            
            if st.button("🚀 Generar y descargar / 生成并下载", type="primary", use_container_width=True):
                with st.spinner("Procesando la imagen final... / 正在生成最终图像..."):
                    res = motor_acordes.aplicar_transposicion(img, st.session_state['acordes'], tonos)
                    st.image(res, caption="Resultado final / 最终结果")
                    
                    res.save("final.jpg")
                    with open("final.jpg", "rb") as f:
                        st.download_button("⬇️ Descargar JPG / 下载 JPG", f, nombre_salida, "image/jpeg")

            if st.button("🗑️ Reiniciar / 重新开始"):
                st.session_state['acordes'] = []
                st.session_state['escaneado'] = False
                st.session_state['refresco'] = 0
                st.rerun()
