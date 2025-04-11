import requests
from pathlib import Path
from astroquery.sdss import SDSS
from astropy.coordinates import SkyCoord
import astropy.units as u
import logging


class HSCDownloader:
    def __init__(self, user: str, password: str, pwd: Path = Path.cwd()):
        """
        This class handles requests and queries to the HSC telescope database.
        """
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

    def cutout_query_sdss(self, sdss_name: str):
        """
        :param sdss_name: The desired SDSS name of the galaxy
        :return: The downloaded image cutout path or None if not found
        """

        ra, dec = self._query_sdss_name(sdss_name)
        if ra is not None and dec is not None:
            return self._cutout_post(ra=ra, dec=dec, obj_name=sdss_name)

        return None  # If everything fails, return None

    def _cutout_post(self, ra: float, dec: float, obj_name: str = "default") -> Path:
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
        response.raise_for_status()

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
        ra, dec = self._query_sdss_name(sdss_name)
        position = SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg), frame='icrs')

        # Query the nearest spectrum
        xid = SDSS.query_region(position, radius=8 * u.arcsec, spectro=True)

        if xid is None or len(xid) == 0:
            raise ValueError(f"No spectrum found near {sdss_name} (RA: {ra}, Dec: {dec})")

        # Download and return the first spectrum
        spectra = SDSS.get_spectra(matches=xid)
        return spectra[0]