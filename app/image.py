from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
from typing import List, Optional, Tuple

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
        try:
            return self._get_coordinates_via_exif()
        except UnsupportedImageFormatError:
            try:
                return self._get_coordinates_straight_from_file()
            except Exception as e:
                message = f"Image {self.filepath} has an unsupported format."
                raise UnsupportedImageFormatError(message) from e

    def _get_coordinates_via_exif(self) -> Coordinates:
        geotags = self._get_geotags()
        return Coordinates.from_geotags(geotags)

    def _get_coordinates_straight_from_file(self) -> Coordinates:
        result = subprocess.run(
            ["mdls", self.filepath], capture_output=True, encoding="utf8"
        )
        lines = result.stdout.split("\n")
        latitude: Optional[float] = None
        longitude: Optional[float] = None
        for line in lines:
            if line.startswith("kMDItemLongitude"):
                longitude = float([bit.strip() for bit in line.split("=")][1])
            if line.startswith("kMDItemLatitude"):
                latitude = float([bit.strip() for bit in line.split("=")][1])
        if not latitude or not longitude:
            raise Exception("Could not find the right metadata.")
        return Coordinates(latitude, longitude)

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
            raise UnsupportedImageFormatError(
                f"No EXIF metadata found in image {self.filepath}."
            )

        geotags = {}
        for (idx, tag) in TAGS.items():
            if tag == "GPSInfo":
                if idx not in exif:
                    raise UnsupportedImageFormatError(
                        f"No EXIF geotagging found in image {self.filepath}."
                    )

                for (key, val) in GPSTAGS.items():
                    if key in exif[idx]:
                        geotags[val] = exif[idx][key]

        return geotags


@dataclass
class ImageFiles:
    EXTENSIONS_TO_AVOID = [".MOV", ".mov", ".mp4", ".MP4"]

    images_directory: str

    def get(self) -> List[ImageFile]:
        return [
            ImageFile(image, f"{self.images_directory}/{image}")
            for image in os.listdir(self.images_directory)
            if not self._has_an_extension_to_avoid(image)
        ]

    @classmethod
    def _has_an_extension_to_avoid(cls, image_name: str) -> bool:
        for extension_to_avoid in cls.EXTENSIONS_TO_AVOID:
            if image_name.endswith(extension_to_avoid):
                return True
        return False
