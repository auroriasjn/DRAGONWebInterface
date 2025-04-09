import streamlit as st
from dragon_display import DRAGONDisplay
from utils import go_back, go_to_page
import logging

import os
import torch

# Required to allow PyTorch to work with Streamlit.
torch.classes.__path__ = [os.path.join(torch.__path__[0], torch.classes.__file__)]

# Initial Methods
if 'page' not in st.session_state:
    st.session_state['page'] = 'Login'
if 'page_stack' not in st.session_state:
    st.session_state['page_stack'] = ['Login']

st.title('DRAGON Inference')
st.button('Previous Page', on_click=go_back, disabled=( st.session_state['page'] == 'Login' ))

# Initializing DRAGON Display class
dragon_frontend = DRAGONDisplay()

# Switch statement for pages
if st.session_state['page'] == 'Login':
    dragon_frontend.display_login_GUI()
elif st.session_state['page'] == 'Cutout':
    dragon_frontend.display_cutout_GUI()
elif st.session_state['page'] == 'Image':
    dragon_frontend.display_image_GUI()
elif st.session_state['page'] == 'Inference':
    if st.session_state['toggle_dragon']:
        dragon_frontend.display_inference_results()
    else:
        dragon_frontend.display_galaxy_results()

if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

