import streamlit as st
from streamlit_cropper import st_cropper
import motor_acordes
from PIL import Image

st.set_page_config(layout="wide")

if 'acordes' not in st.session_state: st.session_state['acordes'] = []
if 'escaneado' not in st.session_state: st.session_state['escaneado'] = False
if 'refresco' not in st.session_state: st.session_state['refresco'] = 0

st.title("🎼 Chord Transposer Pro")

archivo = st.file_uploader("Sube tu partitura", type=["png", "jpg", "jpeg"])

if archivo:
    img = Image.open(archivo).convert("RGB")
    
    if not st.session_state['escaneado']:
        if st.button("🚀 Escaneo Inicial", use_container_width=True):
            st.session_state['acordes'] = motor_acordes.detectar_acordes_global(img)
            st.session_state['escaneado'] = True
            st.rerun()

    if st.session_state['escaneado']:
        col_img, col_ctrl = st.columns([2, 1])
        with col_img:
            img_rev = motor_acordes.dibujar_revision(img, st.session_state['acordes'])
            box = st_cropper(img_rev, realtime_update=True, box_color='red', aspect_ratio=None, key=f"c_{st.session_state['refresco']}")
        
        with col_ctrl:
            if st.button("🔎 Rescatar zona", use_container_width=True):
                zona = (box['top'], box['top'] + box['height'], box['left'], box['left'] + box['width'])
                nuevos = motor_acordes.pasar_lupa_en_zona(img, zona)
                if nuevos:
                    st.session_state['acordes'].extend(nuevos)
                    st.session_state['refresco'] += 1
                    st.rerun()
            
            tonos = st.slider("Bajar semitonos", 0.0, 5.0, 1.0, 0.5)
            if st.button("🪄 Transponer", type="primary", use_container_width=True):
                res = motor_acordes.aplicar_transposicion(img, st.session_state['acordes'], tonos)
                st.image(res)
