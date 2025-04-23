from dragon_inference.frontend.dragon_display import DRAGONDisplay
from dragon_inference.utils import go_back, go_to_page
from multiprocessing import set_start_method

import streamlit as st
import logging
import os
import torch

from streamlit_javascript import st_javascript

# I unabashedly and completely ripped this from StackOverflow.
def _st_theme_mode():
    js_code = """
    (() => {
        // Grab the --base CSS variable from the root element
        const base = getComputedStyle(document.documentElement)
                           .getPropertyValue('--base');
        // Fall back to 'light' if for some reason it’s missing
        return base ? base.trim() : 'light';
    })();
    """
    st_theme = st_javascript(js_code)
    logging.info(f"Detected theme: {st_theme}")
    return st_theme


def _init_frontend():
    # Initial Methods
    if 'page' not in st.session_state:
        st.session_state['page'] = 'Login'
    if 'page_stack' not in st.session_state:
        st.session_state['page_stack'] = ['Login']

    # Navbar!
    with st.sidebar:
        ASSETS_PATH = f"{os.getcwd()}/dragon_inference/frontend/assets/"
        if _st_theme_mode() == 'dark':
            st.image(image=f"{ASSETS_PATH}/dragon_dark.png", width=300)
        else:
            st.image(image=f"{ASSETS_PATH}/dragon_light.jpg", width=300)

        st.button('Previous Page', key='prev_page', on_click=go_back, disabled=(st.session_state['page'] == 'Login'))

    # Actual title page
    st.title('DRAGON Inference')
    st.caption("The DRAGON Web Interface is a convenient web interface for **preliminary** analyses of images.")

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
    # Setup logging
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # Required to allow PyTorch to work with Streamlit.
    torch.classes.__path__ = [os.path.join(torch.__path__[0], torch.classes.__file__)]

    # Ensure the multiprocessing method is properly set for Jupyter
    try:
        set_start_method("fork", force=True)  # "fork" works best on Unix-like systems
    except RuntimeError:
        pass  # If already set, ignore the error

    _init_frontend()

