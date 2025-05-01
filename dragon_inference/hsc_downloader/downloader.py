import requests
from pathlib import Path
from astroquery.sdss import SDSS
from astropy.coordinates import SkyCoord
import io
import astropy.units as u
import logging


class HSCDownloader:
    """
    This class handles requests and queries to the HSC telescope database.

    :param user: The username (for login to HSC).
    :param password: Password (for login to HSC). Since this is a localized instance, we don't worry about security in this case.
    :param pwd: The directory in which we want all files to be downloaded.
    """

    def __init__(self, user: str, password: str, pwd: Path = Path.cwd()):
        self.user = user
        self.password = password
        self.pwd = pwd


    def _query_sdss_name(self, sdss_name: str):
        # Try resolving the name as an object
        try:
            pos = SkyCoord.from_name(sdss_name)
        except Exception:
            try:
                pos = SkyCoord(sdss_name, unit=(u.hourangle, u.deg), frame='icrs')
            except Exception:
                pos = None

        if pos is not None:
            res = SDSS.query_region(coordinates=pos, radius=8 * u.arcsec)
            if res is not None:
                return pos.ra.deg, pos.dec.deg

        # Final fallback: manual SQL query on SDSS name
        logging.info("Falling back to manual SQL query...")
        query = f"""
            SELECT TOP 1 objID, ra, dec 
            FROM PhotoObj 
            WHERE objID IN (
                SELECT objID FROM SpecObj 
                WHERE SDSS17 = '{sdss_name}'
            ) OR objID = CAST('{sdss_name}' AS BIGINT)
            ORDER BY dec DESC
        """
        try:
            res = self._manual_SQL_query(query=query)
            if res is not None and not res.empty:
                return res['ra'].iloc[0], res['dec'].iloc[0]
        except Exception:
            pass  # Suppress query failure

        raise RuntimeWarning('No valid objects found with the given name or coordinates.')

    def _query_ra_dec(self, ra: float, dec: float):
        pos = SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg), frame='icrs')

        return pos.ra.deg, pos.dec.deg

    def cutout_query_sdss(self, sdss_name: str):
        """
        Downloads an 8x8 arcsecond image of a patch of the sky in HSC
        using the SDSS naming convention of the image.

        :param sdss_name: The desired SDSS name of the galaxy
        :return: The downloaded image cutout path or None if not found
        """

        ra, dec = self._query_sdss_name(sdss_name)
        if ra is not None and dec is not None:
            return self._cutout_post(ra=ra, dec=dec, obj_name=sdss_name)

        return None  # If everything fails, return None

    def cutout_query_coord(self, ra: float, dec: float):
        """
        Downloads an 8x8 arcsecond image of a patch of the sky in HSC
        using the *coordinates* of the image.

        :param ra: The provided Right Ascension of the object
        :param dec: The provided Declination of the object
        :return: The downloaded image cutout path or None if not found
        """

        ra, dec = self._query_ra_dec(ra=ra, dec=dec)
        return self._cutout_post(ra=ra, dec=dec, obj_name=f"({ra}, {dec})")

    def _cutout_post(self, ra: float, dec: float, obj_name: str = "default") -> Path:
        """
        Private method for sending the cutout request to HSC without using their API.
        """
        s = requests.Session()
        s.auth = (self.user, self.password)

        base_url = "https://hsc-release.mtk.nao.ac.jp/das_cutout/pdr3/cgi-bin/cutout"
        params = {
            "ra": ra,
            "dec": dec,
            "sw": "8asec",
            "sh": "8asec",
            "type": "coadd",
            "image": "on",
            "filter": "HSC-G",
            "tract": "",
            "rerun": "pdr3_wide"
        }

        filename = self.pwd / f"{obj_name}.fits"

        # If already a file, no need to do anything!
        if Path(filename).is_file():
            return filename

        response = s.get(base_url, params=params, auth=s.auth, stream=True, timeout=30)
        if response.raise_for_status() is not None:
            raise RuntimeError("No file found with the given parameters.")

        with filename.open('wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        return filename

    # Manual SQL query in the SDSS database.
    def _manual_SQL_query(self, query: str):
        res = SDSS.query_sql(query, timeout=120)
        res = res.to_pandas()

        if not len(res):
            raise RuntimeWarning("Error: no objects found via SDSS")

        return res

    # Just get the spectrum in SDSS if it exists.
    def query_spectrum(self, sdss_name: str):
        """
        Convenience method for querying a spectrum from SDSS.
        """
        ra, dec = self._query_sdss_name(sdss_name)
        position = SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg), frame='icrs')

        # Query the nearest spectrum
        xid = SDSS.query_region(position, radius=8 * u.arcsec, spectro=True)

        if xid is None or len(xid) == 0:
            raise ValueError(f"No spectrum found near {sdss_name} (RA: {ra}, Dec: {dec})")

        # Get the first spectrum
        spectra = SDSS.get_spectra(matches=xid)
        return spectra

    def download_spectrum(self, spectrum):
        """
        Convenience method for downloading a spectrum from SDSS.
        """
        buf = io.BytesIO()
        spectrum.writeto(buf)  # write the full HDUList, headers and all
        buf.seek(0)
        return buf