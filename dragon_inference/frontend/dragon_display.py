from hsc_downloader import HSCDownloader
from dragon_analysis import DRAGONAnalysis
from centroid_marker import CentroidMarker

from pathlib import Path
import streamlit as st
import os
import pandas as pd

import mpld3
import streamlit.components.v1 as components
from st_bridge import bridge

from utils import go_to_page, go_back
from utils import load_fits, implot

# Frontend server, effectively served by API requests to the backend (frontend/dragon_display.py)
class DRAGONDisplay:
    def __init__(self):
        """
        Primary web application hub for the Streamlit API
        """
        if 'user' not in st.session_state:
            st.session_state['user'] = ''
        if 'password' not in st.session_state:
            st.session_state['password'] = ''
        if 'image_location' not in st.session_state:
            st.session_state['image_location'] = os.getcwd()
        if 'file' not in st.session_state:
            st.session_state['file'] = ''
        if 'classification' not in st.session_state:
            st.session_state['classification'] = None
        if "centroid_coordinates" not in st.session_state:
            st.session_state.centroid_coordinates = []

        # Button State
        if 'toggle_dragon' not in st.session_state:
            st.session_state['toggle_dragon'] = True

    def display_login_GUI(self):
        with st.form("LoginGUI"):
            st.subheader('Login')
            user = st.text_input(label="User", value="jen55")
            password = st.text_input(label="Password", value="aF5sI9Rm04C81UCY0X6QfVwdM8cE08eF0bzGgOiF", type="password")

            submitted = st.form_submit_button(label="Submit", icon=None, disabled=False, use_container_width=False)

            # On submit, change page
            if submitted:
                st.session_state['user'] = user
                st.session_state['password'] = password
                go_to_page('Cutout')

    def display_cutout_GUI(self):
        """
        For initial image display of the cutout GUI.
        """

        # Initializing the downloader
        downloader = HSCDownloader(user=st.session_state['user'], password=st.session_state['password'])

        # Setting parameters
        with st.form('HSCDownloader'):
            st.subheader('SDSS Downloader')

            st.write("Please input the SDSS name of the galaxy candidate (i.e: J141637.44+003352.2)")

            sdss_name = st.text_input(label="SDSS Name", value="J141637.44+003352.2")
            submitted = st.form_submit_button(label="Submit", icon=None, disabled=False, use_container_width=False)

        # Only after the form are we allowed to do this.
        if submitted:
            with st.status("Downloading from HSC..."):
                file_path = downloader.cutout_query_sdss(sdss_name=sdss_name)
                if file_path is not None:
                    st.session_state['file'] = file_path
                    st.write(f"File written to {file_path}...") # TODO: alter functionality

                    go_to_page('Image')


    def _get_hsc_image(self):
        # Final interactive interface
        header, data = load_fits(file_path=st.session_state['file'], extension=1)
        fig, ax = implot(
            image=data,
            figsize=(st.session_state.fig_size, st.session_state.fig_size),
            grid=st.session_state.show_grid,
            cmap=st.session_state.cmap,
            wcs=header
        )

        ax.set_title(Path(st.session_state['file']).stem)

        return fig, ax

    def _display_hsc_image(self):
        fig, ax = self._get_hsc_image()
        st.pyplot(fig)

    def display_image_GUI(self):
        """
        For initial image display of the cutout HSC.
        """
        if not Path(st.session_state['file']).is_file():
            raise RuntimeError("The path of the file entered is invalid. Please try again.")

        # Image plotting options
        st.session_state.fig_size = st.slider('Figure Size (Inches)', min_value=5, max_value=12, value=8, step=1)
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.show_grid = st.checkbox('Show Grid', value=True)
        with col2:
            st.session_state.cmap = st.selectbox('Colormap', ('viridis', 'gray_r', 'cividis'))

        with st.form("Inference Selector"):
            st.write("You may elect to analyze as a singular galaxy (MCMC fit) "
                     "or as a dual AGN candidate (uses DRAGON).")

            use_dragon = st.radio(
                "Do you wish to use the DRAGON model for your analysis?",
                ["Yes.", "No."],
                captions=[
                    "This option will use 11 DRAGON Congress Models to analyze your image.",
                    "This option is GalFit-lite: will run an MCMC on your image to determine Sersic fit.",
                ],
            )

            submitted = st.form_submit_button(label="Submit", icon=None, disabled=False, use_container_width=False)

        # Upon submission
        if submitted:
            st.session_state['toggle_dragon'] = ( use_dragon == 'Yes.' )
            with st.status("Running DRAGON..."):
                header, data = load_fits(file_path=st.session_state['file'], extension=1)

                # Creating a DRAGON predictor object
                predictor = DRAGONAnalysis(model_dir='models')
                st.session_state['classification'] = predictor.run(image=data)

            go_to_page('Inference')

        # Display the image itself
        self._display_hsc_image()


    def _display_centroid_detector(self):
        """
        Interactive tool to display and mark location of centroids in the image.
        """

        # Initialize centroid detection module
        st.subheader("Centroid Detector Module")

        # Read CSV without a header
        labels_df = pd.read_csv("frontend/labels.csv", header=None)
        labels = dict(zip(labels_df[0], labels_df[1]))

        # Unpacking prediction from DRAGON
        pred_class, num_voters, total_voters, avg_confidence = st.session_state["classification"].values()

        st.write(f"{num_voters}/{total_voters} DRAGON models predict that the object "
                 f"is a **{labels[pred_class]}** with {(avg_confidence * 100):.3f}% probability.")

        coordinate_data = bridge("coordinate_data", default=[])
        with st.form("Centroids"):
            if st.session_state.centroid_coordinates:
                st.write(f"Current centroids: {st.session_state.centroid_coordinates}")
            else:
                st.write("Waiting for centroid coordinates...")

            submitted = st.form_submit_button("Finalize Centroids!", icon=None, disabled=False, use_container_width=False)
            if submitted:
                go_to_page('Inference')

        fig, ax = self._get_hsc_image()

        mpld3.plugins.connect(fig, mpld3.plugins.MousePosition())
        mpld3.plugins.connect(fig, CentroidMarker())

        fig_html = mpld3.fig_to_html(fig)
        components.html(fig_html, height=1000)

        st.session_state['centroid_coordinates'] = coordinate_data

    # Private helper method used in the subsequent method
    def _display_inference_graphs(self):
        pass

    def display_inference_results(self):
        # Honestly, the files downloaded should not be massive.
        # Let's just open it up again.

        self._display_centroid_detector()

    def display_galaxy_results(self):
        """
        Only to be used if the "galaxy" option is chosen
        """
        pass