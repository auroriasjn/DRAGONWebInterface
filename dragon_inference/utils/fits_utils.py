import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

import random
from pathlib import Path

import warnings
import streamlit as st

DEBUG = True


def warning_suppression(toggle=True):
    def warn(func):
        def wrapper(*args, **kwargs):
            with warnings.catch_warnings():
                if not toggle:
                    warnings.simplefilter('ignore')

                return func(*args, **kwargs)

        return wrapper

    return warn


# My first version of load_fits already had some exception hadnling built into it.
@st.cache_data
def load_fits(file_path: str = None, extension: int = 0, explore: bool = False):
    # Exploration
    if explore:
        root = Path.cwd()
        fits_files = list(root.glob('**/*.fits'))
        if len(fits_files) == 0:
            raise OSError('No fits files found to explore!')

        file_path = random.choice(fits_files)

        print(file_path)
    elif file_path is None:
        raise AttributeError('No file path included and explore option not indicated.')

    # Exception handling
    path = Path(file_path)

    valid_suffixes = ['.fits', '.fit']
    if path.suffix.lower() not in valid_suffixes:
        raise AttributeError('Non-FITS path provided to load_fits function.')
    if not path.exists() or not path.is_file():
        raise OSError('Invalid path provided.')

    # Opening file
    hdu = fits.open(file_path)
    if len(hdu) < extension:
        hdu.close()  # close the file descriptor so inode is not left open
        raise IndexError('Extension provided out of bounds.')

    header = hdu[extension].header
    data = hdu[extension].data

    hdu.close()

    return header, data


# A more robust get_fits_image function
def get_fits_image(
        image: np.ndarray,
        figsize: tuple[int, int] = (15, 13),
        cmap: str = 'gray_r',
        scale: float = 0.5,
        wcs: WCS = None,
        grid: bool = False,
        **kwargs
):
    # Calculating the mean and standard deviation
    mean = np.mean(image)
    sigma = np.std(image)

    vmin_temp = mean - scale * sigma
    vmax_temp = mean + scale * sigma

    # Use dictionary pop to get a default value
    vmin = kwargs.pop('vmin', vmin_temp)
    vmax = kwargs.pop('vmax', vmax_temp)
    cmap = kwargs.pop('cmap', cmap)

    # Plotting the without WCS coordinates
    if wcs is None:
        fig, ax = plt.subplots(figsize=figsize)
        if grid:
            ax.coords.grid(color='white', alpha=0.5, linestyle='solid')

        im = ax.imshow(image, vmin=vmin, vmax=vmax, cmap=cmap, **kwargs)
        return fig, ax

    # Conditional branching to make code more readable
    fig, ax = plt.subplots(figsize=figsize, subplot_kw={'projection': wcs})

    plt.rcParams.update({'axes.labelsize': 15})  # update to font size 15
    ax.set_xlabel("Right Ascension [hms]")
    ax.set_ylabel("Declination [degrees]")

    if grid:
        ax.coords.grid(color='gray', alpha=0.5, linestyle='solid')

    im = ax.imshow(image, vmin=vmin, vmax=vmax, cmap=cmap, **kwargs)
    return fig, ax


@warning_suppression(toggle=DEBUG)
def implot(
        image: np.ndarray,
        figsize: tuple[int, int] = (15, 13),
        cmap: str = 'gray_r',
        scale: float = 0.5,
        wcs: (WCS or fits.header.Header) = None,
        grid: bool = False,
        **kwargs
):
    # Additional functionality: if you just import the header
    # object, it will automatically do the conversion for you
    if type(wcs) == fits.header.Header:
        wcs = WCS(wcs)

    return get_fits_image(image=image, figsize=figsize, \
                          cmap=cmap, scale=scale, wcs=wcs, grid=grid, **kwargs)