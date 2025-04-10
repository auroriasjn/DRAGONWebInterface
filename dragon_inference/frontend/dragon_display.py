from hsc_downloader import HSCDownloader
from dragon_analysis import DRAGONAnalysis, CentroidPoint
from centroid_marker import CentroidMarker
from galaxy_inference import GalaxyInference
from utils import go_to_page, go_back
from utils import load_fits, implot

from pathlib import Path
from st_bridge import bridge

import streamlit as st
import os
import matplotlib.pyplot as plt
import pandas as pd
import astropy.units as u

import mpld3
import streamlit.components.v1 as components


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
        if 'sdss_name' not in st.session_state:
            st.session_state['sdss_name'] = None

        if 'file' not in st.session_state:
            st.session_state['file'] = ''
        if 'classification' not in st.session_state:
            st.session_state['classification'] = None
        if "centroid_coordinates" not in st.session_state:
            st.session_state.centroid_coordinates = []
        if 'fits' not in st.session_state:
            st.session_state['fits'] = None

        # Button State
        if 'toggle_dragon' not in st.session_state:
            st.session_state['toggle_dragon'] = True

        # Inference State
        if 'inference_state' not in st.session_state:
            st.session_state['inference_state'] = 'Centroids'

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
                st.session_state['sdss_name'] = sdss_name
                if file_path is not None:
                    st.session_state['file'] = file_path
                    st.write(f"File written to {file_path}...") # TODO: alter functionality

                    go_to_page('Image')


    def _get_hsc_image(self):
        # Final interactive interface
        if st.session_state['fits'] is None:
            header, data = load_fits(file_path=st.session_state['file'], extension=1)
            st.session_state['fits'] = {
                "header": header,
                "data": data
            }
        else:
            header, data = st.session_state['fits']['header'], st.session_state['fits']['data']

        fig, ax = implot(
            image=data,
            figsize=(st.session_state.fig_size, st.session_state.fig_size),
            grid=st.session_state.show_grid,
            cmap=st.session_state.cmap,
            wcs=header
        )

        ax.set_title(Path(st.session_state['file']).stem)

        return fig, ax

    def _init_centroids(self):
        # Split into the two coordinates and convert!
        c1, c2 = st.session_state.centroid_coordinates
        c1, c2 = CentroidPoint(c1), CentroidPoint(c2)

        # This should already be cached, so should take minimal time.
        header, data = load_fits(file_path=st.session_state['file'], extension=1)
        c1, c2 = c1.convert_WCS(wcs_header=header), c2.convert_WCS(wcs_header=header)

        return c1, c2


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
                    "This option will use 7 DRAGON Congress Models to analyze your image.",
                    "This option is GalFit-lite: will run an MCMC on your image to determine Sersic fit.",
                ],
            )

            submitted = st.form_submit_button(label="Submit", icon=None, disabled=False, use_container_width=False)

        # Upon submission
        if submitted:
            st.session_state['toggle_dragon'] = ( use_dragon == 'Yes.' )
            with st.status("Running DRAGON..."):
                # This should already be cached, so should take minimal time.
                header, data = load_fits(file_path=st.session_state['file'], extension=1)
                st.session_state['fits'] = {
                    "header": header,
                    "data": data
                }

                # Creating a DRAGON predictor object
                predictor = DRAGONAnalysis(model_dir='models')
                st.session_state['classification'] = predictor.run(image=data)

            go_to_page('Inference')

        # Display the image itself
        fig, ax = self._get_hsc_image()
        st.pyplot(fig)


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
        st.session_state['centroid_coordinates'] = coordinate_data

        with st.form("Centroids"):
            if st.session_state.centroid_coordinates:
                c1, c2 = self._init_centroids()
                st.write(f"Current centroids: {c1}, {c2}")
            else:
                st.write("Waiting for centroid coordinates...")

            submitted = st.form_submit_button(
                "Finalize Centroids!", icon=None,
                disabled=(st.session_state.centroid_coordinates is None),
                use_container_width=False
            )

            if submitted:
                st.session_state['inference_state'] = 'Seps'
                st.rerun()

        fig, ax = self._get_hsc_image()

        mpld3.plugins.connect(fig, mpld3.plugins.MousePosition())
        mpld3.plugins.connect(fig, CentroidMarker())

        fig_html = mpld3.fig_to_html(fig)
        components.html(fig_html, height=1000)

    def _plot_spectrum(self, spec):
        data = spec[1].data
        wavelength = 10 ** data['loglam']
        flux = data['flux']

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(wavelength, flux, lw=0.5)
        ax.set_xlabel("Wavelength (Å)")
        ax.set_ylabel("Flux")

        ax.set_title("SDSS Spectrum")
        ax.grid(True)
        st.pyplot(fig)



    # Private helper method used in the subsequent method
    def _display_inference_graphs(self):
        # Initialize centroid detection module
        st.subheader("Inference Results")

        c1, c2 = self._init_centroids()
        radius1 = st.slider(f'Radius of Centroid 1 at {c1} (Pixels)', min_value=1, max_value=10, value=5, step=1)
        radius2 = st.slider(f'Radius of Centroid 2 at {c1} (Pixels)', min_value=1, max_value=10, value=5, step=1)

        with st.status("Calculating separations..."):
            st.write(f"The centroids chosen are at {c1}, {c2}.")

            sep = DRAGONAnalysis.separation(c1, c2)
            sep = sep.to(u.arcsec)

        with st.status("Calculating magnitudes..."):
            header0, _ = load_fits(file_path=st.session_state['file'], extension=0)
            fluxmag_0 = header0['FLUXMAG0']

            header, data = st.session_state['fits']['header'], st.session_state['fits']['data']
            mag_dict = DRAGONAnalysis.calculate_magnitudes(
                image=data,
                center_coords=[c1.extract_point(), c2.extract_point()],
                radii=[radius1, radius2],
                fluxmag_0=fluxmag_0
            )

            # Just for extra measure.
            st.write(mag_dict)

        with st.status("Attempting to fetch spectrum...") as status:
            st.write(f"Fetching SDSS name {st.session_state['sdss_name']}...")

            downloader = HSCDownloader(user=st.session_state['user'], password=st.session_state['password'])
            spectrum = downloader.query_spectrum(st.session_state['sdss_name'])

            if spectrum is None:
                status.update(
                    label="No spectrum found in SDSS database...", state="complete", expanded=False
                )
            else:
                status.update(
                    label="Download complete!", state="complete", expanded=False
                )

        # Unpacking prediction from DRAGON (again)
        labels_df = pd.read_csv("frontend/labels.csv", header=None)
        labels = dict(zip(labels_df[0], labels_df[1]))
        pred_class, num_voters, total_voters, avg_confidence = st.session_state["classification"].values()

        st.markdown(f"""
        ### Projected Angular Separation and Magnitude Difference

        - **Angular Separation:** {sep:.3g}
        - **Magnitude Difference:** {mag_dict['diff']:.4g}  
        - **Flux Ratio:** {mag_dict['flux_ratio']:.4g}
        - **Classification**: {labels[pred_class]}, {(avg_confidence * 100):.3f}% probability.
        """)

        # Display the image itself with added centroid positions.
        fig, ax = self._get_hsc_image()
        ax.scatter(c1.x, c1.y, s=15, c='red', marker='x', label=f'Centroid 1 {c1}')
        ax.scatter(c2.x, c2.y, s=15, c='blue', marker='x', label=f'Centroid 2 {c2}')

        mag_dict['aperture1'].plot(color='white', lw=2, label='Photometry Aperture 1')
        mag_dict['aperture2'].plot(color='white', lw=2, label='Photometry Aperture 2')

        plt.legend()
        st.pyplot(fig)

        # Plot spectrum if it exists
        if not spectrum:
            return None

        self._plot_spectrum(spectrum)


    def display_inference_results(self):
        # Honestly, the files downloaded should not be massive.
        # Let's just open it up again.

        if st.session_state['inference_state'] == 'Centroids':
            self._display_centroid_detector()
        else:
            self._display_inference_graphs()


    def display_galaxy_results(self):
        """
        Only to be used if the "galaxy" option is chosen
        """
        galaxy_inf = GalaxyInference()