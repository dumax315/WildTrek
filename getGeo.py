
import json
from pathlib import Path


from exif import Image

# file = Path("static\images\carwithMeta.jpg")


def read_exif_data(file_path: Path) -> Image:
    """Read metadata from photo."""
    with open(file_path, 'rb') as f:
        return Image(f) 
    
# img = read_exif_data(file)
# print('\n'.join([i for i in img.list_all() 
#                  if i.startswith('gps_')]))

def convert_coords_to_decimal(coords: tuple[float,...], ref: str) -> float:
    """Covert a tuple of coordinates in the format (degrees, minutes, seconds)
    and a reference to a decimal representation.

    Args:
        coords (tuple[float,...]): A tuple of degrees, minutes and seconds
        ref (str): Hemisphere reference of "N", "S", "E" or "W".

    Returns:
        float: A signed float of decimal representation of the coordinate.
    """
    if ref.upper() in ['W', 'S']:
        mul = -1
    elif ref.upper() in ['E', 'N']:
        mul = 1
    else:
        print("Incorrect hemisphere reference. "
              "Expecting one of 'N', 'S', 'E' or 'W', "
              f'got {ref} instead.')
        mul = 1
        
    return mul * (coords[0] + coords[1] / 60 + coords[2] / 3600) 


def get_decimal_coord_from_exif(exif_data: Image
                                ) -> tuple[float, ...]:
    """Get coordinate data from exif and convert to a tuple of 
    decimal latitude, longitude and altitude.

    Args:
        exif_data (Image): exif Image object

    Returns:
        tuple[float, ...]: A tuple of decimal coordinates (lat, lon, alt)
    """
    try:
        lat = convert_coords_to_decimal(
            exif_data['gps_latitude'], 
            exif_data['gps_latitude_ref']
            )
        lon = convert_coords_to_decimal(
            exif_data['gps_longitude'], 
            exif_data['gps_longitude_ref']
            )
        return (lat, lon)
    except (AttributeError, KeyError):
        print('Image does not contain spatial data or data is invalid.')  
        raise


def convert_coordinates(gps_latitude, gps_longitude, gps_latitude_ref, gps_longitude_ref):
    # Convert GPS latitude to decimal degrees
    gps_latitude_decimal = gps_latitude[0] + (gps_latitude[1] / 60) + (gps_latitude[2] / 3600)
    if gps_latitude_ref in ['S', 'W']:
        gps_latitude_decimal = -gps_latitude_decimal
    # Convert GPS longitude to decimal degrees
    gps_longitude_decimal = gps_longitude[0] + (gps_longitude[1] / 60) + (gps_longitude[2] / 3600)
    if gps_longitude_ref in ['S', 'W']:
        gps_longitude_decimal = -gps_longitude_decimal

    return [gps_latitude_decimal, gps_longitude_decimal]
# print(get_decimal_coord_from_exif(img))

def geoGetter(img):
    data = Image(img) 
    print('\n'.join([i for i in data.list_all() 
                 if i.startswith('gps_')]))
    print(data['gps_latitude'])
    print(data['gps_latitude_ref'])

    print(convert_coordinates(data['gps_latitude'],data['gps_longitude'],data['gps_latitude_ref'],data['gps_longitude_ref']))
    return get_decimal_coord_from_exif(data)
    
