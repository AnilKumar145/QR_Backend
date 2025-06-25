from math import radians, sin, cos, sqrt, atan2
from typing import Tuple, Optional
from app.core.config import settings
from app.core.exceptions import InvalidLocationException
import logging
from app.models.venue import Venue

logger = logging.getLogger(__name__)

class GeoValidator:
    def __init__(self, venue: Optional[Venue] = None):
        # Use venue coordinates if provided, otherwise fall back to default
        if venue:
            self.venue_lat = venue.latitude
            self.venue_lon = venue.longitude
            self.max_distance_m = venue.radius_meters
            logger.info(f"GeoValidator initialized with venue coordinates: {self.venue_lat}, {self.venue_lon}, radius: {self.max_distance_m}m")
        else:
            # Fallback to institution settings (for backward compatibility)
            self.venue_lat = float(settings.INSTITUTION_LAT)
            self.venue_lon = float(settings.INSTITUTION_LON)
            self.max_distance_m = float(settings.GEOFENCE_RADIUS_M)
            logger.info(f"GeoValidator initialized with default coordinates: {self.venue_lat}, {self.venue_lon}")

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters using Haversine formula"""
        # Debug prints for exact values and types
        logger.info("=== Distance Calculation Debug ===")
        logger.info(f"Institution coordinates (type, value):")
        logger.info(f"Lat1: ({type(lat1)}, {lat1})")
        logger.info(f"Lon1: ({type(lon1)}, {lon1})")
        logger.info(f"User coordinates (type, value):")
        logger.info(f"Lat2: ({type(lat2)}, {lat2})")
        logger.info(f"Lon2: ({type(lon2)}, {lon2})")

        try:
            # Ensure all values are float and rounded to 7 decimal places
            lat1, lon1, lat2, lon2 = map(lambda x: round(float(x), 7), [lat1, lon1, lat2, lon2])
            logger.info("After rounding:")
            logger.info(f"Point 1: {lat1}, {lon1}")
            logger.info(f"Point 2: {lat2}, {lon2}")

            # Check for exact match with tolerance
            if abs(lat1 - lat2) < 1e-7 and abs(lon1 - lon2) < 1e-7:
                logger.info("Coordinates match exactly!")
                return 0.0

            # Earth's radius in meters
            R = 6371000  # meters

            # Convert to radians
            lat1_rad = radians(lat1)
            lon1_rad = radians(lon1)
            lat2_rad = radians(lat2)
            lon2_rad = radians(lon2)

            # Log radian values
            logger.info("Radian values:")
            logger.info(f"lat1_rad: {lat1_rad}")
            logger.info(f"lon1_rad: {lon1_rad}")
            logger.info(f"lat2_rad: {lat2_rad}")
            logger.info(f"lon2_rad: {lon2_rad}")

            # Calculate differences
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad

            # Haversine formula
            a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance = R * c

            logger.info(f"Final calculated distance: {distance:.2f} meters")
            return round(distance, 2)

        except Exception as e:
            logger.error(f"Error in distance calculation: {str(e)}")
            raise

    def is_location_valid(self, lat: float, lon: float) -> Tuple[bool, float]:
        """Check if given location is within allowed radius of the venue"""
        logger.info("\n=== Location Validation Start ===")
        try:
            # Basic range validation
            if not (-90 <= lat <= 90):
                raise InvalidLocationException(
                    0, lat, lon,
                    f"Invalid latitude {lat}. Must be between -90 and 90 degrees"
                )
            if not (-180 <= lon <= 180):
                raise InvalidLocationException(
                    0, lat, lon,
                    f"Invalid longitude {lon}. Must be between -180 and 180 degrees"
                )

            distance_meters = self.calculate_distance(
                self.venue_lat,
                self.venue_lon,
                lat,
                lon
            )
            
            if distance_meters > self.max_distance_m:
                # If distance is too great, simply return False and the calculated distance.
                # The endpoint will handle the logging and exception raising.
                return False, distance_meters

            return True, distance_meters

        except InvalidLocationException:
            # Re-raise the exception without modification
            raise
        except Exception as e:
            logger.error(f"Location validation error: {str(e)}")
            # For other errors, return False and a distance of -1 to indicate failure.
            return False, -1.0





