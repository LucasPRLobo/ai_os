"""
EXIF Extractor Utility
Extracts EXIF metadata from images using piexif and Pillow.
"""

import piexif
from PIL import Image
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Tuple


def extract_exif_data(image_path: str) -> Dict:
    """
    Extract EXIF metadata from an image file.

    Args:
        image_path: Path to the image file

    Returns:
        Dictionary containing extracted EXIF data:
        {
            'date_taken': datetime or None,
            'location': str or None (e.g., "40.7128N, 74.0060W" or place name),
            'camera_make': str or None,
            'camera_model': str or None,
            'image_dimensions': str or None (e.g., "1920x1080"),
            'has_exif': bool
        }
    """
    result = {
        'date_taken': None,
        'location': None,
        'camera_make': None,
        'camera_model': None,
        'image_dimensions': None,
        'has_exif': False
    }

    try:
        # Open image with Pillow
        image = Image.open(image_path)

        # Get dimensions
        width, height = image.size
        result['image_dimensions'] = f"{width}x{height}"

        # Try to load EXIF data
        try:
            exif_dict = piexif.load(image.info.get('exif', b''))
        except Exception:
            # No EXIF data or corrupted
            return result

        if not exif_dict:
            return result

        result['has_exif'] = True

        # Extract date taken
        date_taken = _extract_date_taken(exif_dict)
        if date_taken:
            result['date_taken'] = date_taken

        # Extract GPS location
        location = _extract_gps_location(exif_dict)
        if location:
            result['location'] = location

        # Extract camera info
        camera_make, camera_model = _extract_camera_info(exif_dict)
        result['camera_make'] = camera_make
        result['camera_model'] = camera_model

    except Exception as e:
        # If anything fails, return what we have
        pass

    return result


def _extract_date_taken(exif_dict: Dict) -> Optional[datetime]:
    """
    Extract date/time when photo was taken from EXIF.

    Args:
        exif_dict: EXIF dictionary from piexif

    Returns:
        datetime object or None
    """
    # Try different EXIF tags for date
    date_tags = [
        (piexif.ExifIFD.DateTimeOriginal, "0th"),
        (piexif.ExifIFD.DateTimeDigitized, "Exif"),
        (piexif.ImageIFD.DateTime, "0th"),
    ]

    for tag, ifd_name in date_tags:
        try:
            if ifd_name == "0th" and "0th" in exif_dict:
                date_str = exif_dict["0th"].get(piexif.ImageIFD.DateTime)
            elif ifd_name == "Exif" and "Exif" in exif_dict:
                date_str = exif_dict["Exif"].get(tag)
            else:
                continue

            if date_str:
                # EXIF date format: "YYYY:MM:DD HH:MM:SS"
                if isinstance(date_str, bytes):
                    date_str = date_str.decode('utf-8')

                # Parse the date
                dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                return dt
        except Exception:
            continue

    return None


def _extract_gps_location(exif_dict: Dict) -> Optional[str]:
    """
    Extract GPS coordinates from EXIF and format as string.

    Args:
        exif_dict: EXIF dictionary from piexif

    Returns:
        Location string (e.g., "40.7128N, 74.0060W") or None
    """
    if "GPS" not in exif_dict:
        return None

    gps_data = exif_dict["GPS"]

    try:
        # Get latitude
        lat = _convert_gps_to_degrees(
            gps_data.get(piexif.GPSIFD.GPSLatitude),
            gps_data.get(piexif.GPSIFD.GPSLatitudeRef)
        )

        # Get longitude
        lon = _convert_gps_to_degrees(
            gps_data.get(piexif.GPSIFD.GPSLongitude),
            gps_data.get(piexif.GPSIFD.GPSLongitudeRef)
        )

        if lat is not None and lon is not None:
            # Format as "40.7128N, 74.0060W"
            lat_dir = "N" if lat >= 0 else "S"
            lon_dir = "E" if lon >= 0 else "W"
            return f"{abs(lat):.4f}{lat_dir}, {abs(lon):.4f}{lon_dir}"

    except Exception:
        pass

    return None


def _convert_gps_to_degrees(
    gps_coord: Optional[Tuple],
    gps_ref: Optional[bytes]
) -> Optional[float]:
    """
    Convert GPS coordinates from EXIF format to decimal degrees.

    Args:
        gps_coord: GPS coordinate tuple ((degrees, 1), (minutes, 1), (seconds, 100))
        gps_ref: Reference (b'N', b'S', b'E', or b'W')

    Returns:
        Decimal degrees or None
    """
    if not gps_coord or not gps_ref:
        return None

    try:
        # Extract degrees, minutes, seconds
        degrees = gps_coord[0][0] / gps_coord[0][1]
        minutes = gps_coord[1][0] / gps_coord[1][1]
        seconds = gps_coord[2][0] / gps_coord[2][1]

        # Convert to decimal degrees
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

        # Apply direction (S and W are negative)
        if gps_ref in [b'S', b'W']:
            decimal = -decimal

        return decimal

    except Exception:
        return None


def _extract_camera_info(exif_dict: Dict) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract camera make and model from EXIF.

    Args:
        exif_dict: EXIF dictionary from piexif

    Returns:
        Tuple of (camera_make, camera_model) or (None, None)
    """
    camera_make = None
    camera_model = None

    try:
        if "0th" in exif_dict:
            # Get camera make
            make_bytes = exif_dict["0th"].get(piexif.ImageIFD.Make)
            if make_bytes:
                if isinstance(make_bytes, bytes):
                    camera_make = make_bytes.decode('utf-8').strip('\x00')
                else:
                    camera_make = str(make_bytes)

            # Get camera model
            model_bytes = exif_dict["0th"].get(piexif.ImageIFD.Model)
            if model_bytes:
                if isinstance(model_bytes, bytes):
                    camera_model = model_bytes.decode('utf-8').strip('\x00')
                else:
                    camera_model = str(model_bytes)

    except Exception:
        pass

    return camera_make, camera_model
