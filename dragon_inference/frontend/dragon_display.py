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
import io
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
            st.caption("To facilitate easier downloading, you can input your HSC credentials "
                       "here. Note that this Streamlit app is on a local instance, so the "
                       "API request will be secure. This section **requires** an **valid** HSC downloader "
                       "account to execute properly.")
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

            st.write("Please input the **SDSS name** of the galaxy candidate (i.e: J141637.44+003352.2, or "
                     "the direct SDSS object id)")

            st.caption("In Moskowitz and Ng et al. (2025), all analyses of candidates were conducted "
                       "via cross-matching to SDSS, which is why this step is necessary.")

            sdss_name = st.text_input(label="SDSS Name", value="J141637.44+003352.2")

            st.caption("Alternatively, specify RA and DEC here in ICRS (Degree) format. :red[This will override the SDSS name.]")
            col1, col2 = st.columns(2)
            with col1:
                ra = st.text_input(label="Right Ascension (RA)")
            with col2:
                dec = st.text_input(label="Declination (Dec)")

            submitted = st.form_submit_button(label="Submit", icon=None, disabled=False, use_container_width=False)


        # Only after the form are we allowed to do this.
        if submitted:
            with st.status("Downloading from HSC..."):
                if ra is None and dec is None or not len(ra) or not len(dec):
                    file_path = downloader.cutout_query_sdss(sdss_name=sdss_name)
                else:
                    file_path = downloader.cutout_query_coord(ra=ra, dec=dec)

                st.session_state['sdss_name'] = sdss_name if not len(ra) else f"({ra}, {dec})"
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

            # This should already be cached, so should take minimal time.
            header, data = load_fits(file_path=st.session_state['file'], extension=1)
            st.session_state['fits'] = {
                "header": header,
                "data": data
            }

            if st.session_state['toggle_dragon']:
                with st.status("Running DRAGON..."):
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

        st.caption("A part of Moskowitz and Ng et al. (2025) was an automated centroid analysis "
                   "via use of the GOTHIC algorithm and a fit to a Moffat2D profile. However, "
                   "since we are only dealing with one image, a manual selection of centroid "
                   "points will suffice. Your selected points will be marked in :red[**red**] "
                   "and will be saved and **automatically disappear** upon selection of _two_ points.")

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

            if submitted and len(st.session_state.centroid_coordinates) == 2:
                st.session_state['inference_state'] = 'Seps'
                st.rerun()

        fig, ax = self._get_hsc_image()

        mpld3.plugins.connect(fig, mpld3.plugins.MousePosition())
        mpld3.plugins.connect(fig, CentroidMarker())

        fig_html = mpld3.fig_to_html(fig)
        components.html(fig_html, height=1000)

    def _plot_spectrum(self, spectrum):
        # We just want the first part.
        spec = spectrum[0]

        # And then to extract from there...
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

    def _download_spectrum_button(self, spectrum):
        downloader = HSCDownloader(user=st.session_state['user'], password=st.session_state['password'])

        # Only downloading the first spectrum
        buf = downloader.download_spectrum(spectrum[0])
        st.download_button(
            label="Download Spectrum",
            data=buf,
            file_name=f"{st.session_state['sdss_name']}_spec.fits",
            mime="application/fits",
            icon=":material/download:"
        )

    def _download_magnitude_image(self, fig, ax):
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)

        st.download_button(
            label="Download Apertures",
            data=buf,
            file_name=f"{st.session_state['sdss_name']}_centroids.png",
            mime="image/png",
            icon=":material/download:"
        )


    # Private helper method used in the subsequent method
    def _display_inference_graphs(self):
        # Initialize centroid detection module
        st.subheader("Inference Results")

        c1, c2 = self._init_centroids()

        with st.sidebar:
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

        # Further sidebar shenanigans
        with st.sidebar:
            self._download_spectrum_button(spectrum)
            self._download_magnitude_image(fig, ax)


    def display_inference_results(self):
        # Honestly, the files downloaded should not be massive.
        # Let's just open it up again.

        if st.session_state['inference_state'] == 'Centroids':
            self._display_centroid_detector()
        else:
            self._display_inference_graphs()


    def _run_mcmc(self, steps, walkers, n, r_eff, i0, theta, ellip):
        param_names = ["n", "R_e", "I_0", "\\theta", "\\epsilon", "x_0", "y_0"]
        with st.status(f"Initializing Galaxy MCMC with {steps} steps and {walkers} walkers..."):
            galaxy_inference = GalaxyInference(n_steps=steps, n_walkers=walkers)

        with st.status("Standardizing initial guesses..."):
            galaxy_inference.init_params(
                n=n,
                r_eff=r_eff,
                i0=i0,
                theta=theta,
                ellip=ellip
            )

        with st.status("Loading image..."):
            header, data = st.session_state['fits']['header'], st.session_state['fits']['data']
            galaxy_inference.load_data(image=data)

        with st.status("Running MCMC..."):
            pos, prob, state, sampler, corner, inferred_params = galaxy_inference.fit_radial_light_profile()

            # First plot the Corner Plot
            st.pyplot(corner)

            # Contour map plot!
            fig, ax = self._get_hsc_image()
            medians = [inferred_params[name]["median"] for name in param_names]

            model, levels = galaxy_inference.get_contour_levels(medians, n_levels=8)
            ax.contour(model, levels=levels, colors="white", linewidths=1)
            st.pyplot(fig)

        st.subheader("Inferred Parameters")
        st.caption("These are the inferred parameters outputted from the aforementioned MCMC model. A"
                   " more _comprehensive_ corner plot is visible underneath the status header.")

        # **This segment was ChatGPTed, just to make the formatting nice!**
        latex_lines = []
        for name, values in inferred_params.items():
            med = values["median"]
            minus = values["minus_1sigma"]
            plus = values["plus_1sigma"]

            latex_expr = rf"${name} = {med:.4g}^{{+{plus:.4g}}}_{{-{minus:.4g}}}$"
            latex_lines.append(f"- {latex_expr}")

        st.markdown("\n".join(latex_lines))

    def display_galaxy_results(self):
        """
        Only to be used if the "galaxy" option is chosen.
        """
        st.subheader("Galaxy Inference Results")

        with st.form("Parameters"):
            st.subheader("MCMC Configuration")

            col1, col2 = st.columns(2)
            with col1:
                steps = st.slider("Step Count for MCMC", min_value=100, max_value=1000000, value=1000, step=100)
            with col2:
                walkers = st.slider("Walker Count for MCMC", min_value=20, max_value=1000, value=20, step=10)

            st.caption("Provide initial guesses for your parameters for the Sersic model. "
                       "Recall that the model fitted will be of the form:")
            st.latex(r'''
                I(R) = I_0 \exp\left\{-b_n \left[\left(\frac{R}{R_e}\right)^{1/n} - 1\right]\right\}
            ''')

            st.markdown("### Initial Parameter Guesses")

            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                sersic_guess = st.number_input("Sersic ($n$)", key="sersic", min_value=1., max_value=4., step=0.01)
            with col2:
                r_eff = st.number_input("Half-Light ($R_e$)", key="reff", min_value=0., value=5., step=0.1)
            with col3:
                i0 = st.number_input("Intensity ($I_0$)", key="i0", min_value=0., value=8.0, step=0.1)
            with col4:
                theta = st.number_input("Angle ($\\theta$)", min_value=0., max_value=360., step=0.5, key="theta")
            with col5:
                ellipticity = st.number_input(
                    "Ellipticity ($\\epsilon$)", min_value=0., max_value=1., value=0.5, step=0.01, key="ellip"
                )

            submitted = st.form_submit_button(label="Submit")

        if submitted:
            self._run_mcmc(
                steps=int(steps),
                walkers=int(walkers),
                n=sersic_guess,
                r_eff=r_eff,
                i0=i0,
                theta=theta,
                ellip=ellipticity
            )


        fig, ax = self._get_hsc_image()
        st.pyplot(fig)





