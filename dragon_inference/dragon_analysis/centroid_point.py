from astropy.wcs import WCS

class CentroidPoint:
    def __init__(self, point_dict):
        if 'x' not in point_dict or 'y' not in point_dict:
            raise RuntimeError("Invalid Point Dictionary specified.")

        self.x = point_dict['x']
        self.y = point_dict['y']

        self.ra, self.dec = None, None

    def __str__(self):
        if self.ra is not None and self.dec is not None:
            ra1_str = self.ra.to_string(unit='hourangle', sep=':', precision=2)
            dec1_str = self.dec.to_string(unit='deg', sep=':', precision=2, alwayssign=True)

            return f"({ra1_str}, {dec1_str})"

        return f"({self.x}, {self.y})"

    def __repr__(self):
        return self.__str__()

    # Only extracting Cartesian
    def extract_point(self):
        return (self.x, self.y)


    def convert_WCS(self, wcs_header):
        """
        Convenience method to help with conversion to WCS.
        """
        if not (w := WCS(wcs_header)): # I decided to use a walrus statement because why not?
            raise RuntimeError("Invalid WCS header provided")

        to_world = w.pixel_to_world(self.x, self.y)
        self.ra, self.dec = to_world.ra, to_world.dec

        # To allow for method chaining
        return self

