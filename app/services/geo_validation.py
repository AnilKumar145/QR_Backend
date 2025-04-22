from math import radians, cos, sin, asin, sqrt
from typing import Tuple

class GeoValidator:
    # KL University coordinates
    INSTITUTION_LAT = 16.466167
    INSTITUTION_LON = 80.674499
    MAX_DISTANCE_KM = 0.05  # 50 meters radius

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r

    @classmethod
    def is_location_valid(cls, lat: float, lon: float) -> Tuple[bool, float]:
        distance = cls.calculate_distance(
            cls.INSTITUTION_LAT, 
            cls.INSTITUTION_LON, 
            lat, 
            lon
        )
        return distance <= cls.MAX_DISTANCE_KM, distance
