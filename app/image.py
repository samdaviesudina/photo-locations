from __future__ import annotations

from dataclasses import dataclass
import os
from typing import List, Tuple

from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import GPSTAGS, TAGS


class UnsupportedImageFormatError(Exception):
    pass


@dataclass
class Coordinates:
    latitude: float
    longitude: float

    @classmethod
    def from_geotags(cls, geotags: dict) -> Coordinates:
        lat = cls._dms_to_decimal(geotags["GPSLatitude"], geotags["GPSLatitudeRef"])
        lon = cls._dms_to_decimal(geotags["GPSLongitude"], geotags["GPSLongitudeRef"])

        return Coordinates(lat, lon)

    @staticmethod
    def _dms_to_decimal(dms: Tuple, reference: str) -> float:
        degrees = dms[0]
        minutes = dms[1] / 60.0
        seconds = dms[2] / 3600.0

        if reference in ["S", "W"]:
            degrees = -degrees
            minutes = -minutes
            seconds = -seconds

        return round(degrees + minutes + seconds, 5)


@dataclass
class ImageFile:
    name: str
    filepath: str

    def __repr__(self) -> str:
        return self.filepath

    def get_coordinates(self) -> Coordinates:
        geotags = self._get_geotags()
        return Coordinates.from_geotags(geotags)

    def _get_exif(self) -> dict:
        try:
            image = Image.open(self.filepath)
            image.verify()
            return image._getexif()
        except UnidentifiedImageError as e:
            message = f"Image {self.filepath} has an unsupported format."
            raise UnsupportedImageFormatError(message) from e

    def _get_geotags(self) -> dict:
        exif = self._get_exif()

        if not exif:
            raise ValueError("No EXIF metadata found")

        geotags = {}
        for (idx, tag) in TAGS.items():
            if tag == "GPSInfo":
                if idx not in exif:
                    raise ValueError("No EXIF geotagging found")

                for (key, val) in GPSTAGS.items():
                    if key in exif[idx]:
                        geotags[val] = exif[idx][key]

        return geotags


@dataclass
class ImageFiles:
    images_directory: str

    def get(self) -> List[ImageFile]:
        return [
            ImageFile(image, f"{self.images_directory}/{image}")
            for image in os.listdir(self.images_directory)
        ]