from collections import defaultdict
from dataclasses import dataclass
import os

from app.image import ImageFile, ImageFiles, UnsupportedImageFormatError
from app.location import Location, World

API_KEY = "SV6kWr3TZFpCnj0_kFDsYCmeBxiCSDY5WsZp4WPtUsE"

IMAGES_DIRECTORY = "images"


def main() -> None:
    image_files = ImageFiles(IMAGES_DIRECTORY).get()
    print(f"Processing {len(image_files)} images...")

    world = World(API_KEY)

    problematic_images = []
    located_images: defaultdict = defaultdict(list)
    for image_file in image_files:
        try:
            coordinates = image_file.get_coordinates()
            location = world.locate(coordinates)
            located_images[location.city].append(LocatedImage(image_file, location))
        except UnsupportedImageFormatError:
            problematic_images.append(image_file.name)
        except ValueError as e:
            if str(e) == "No EXIF metadata found":
                problematic_images.append(image_file.name)
            else:
                raise

    print(f"There were {len(problematic_images)} problematic images.")

    for city in located_images.keys():
        city_snake_case = city.replace(" ", "_")
        os.mkdir(f"images/{city_snake_case}")
        for image in located_images[city]:
            os.rename(
                image.image_file.filepath,
                f"images/{city_snake_case}/{image.image_file.name}",
            )


@dataclass
class LocatedImage:
    image_file: ImageFile
    location: Location

    def __repr__(self) -> str:
        return f"{self.image_file} ({self.location})"


if __name__ == "__main__":
    main()
