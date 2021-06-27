from collections import defaultdict
from dataclasses import dataclass
import os

from app.image import ImageFile, ImageFiles, UnsupportedImageFormatError
from app.location import InvalidLocationError, Location, World

API_KEY = "SV6kWr3TZFpCnj0_kFDsYCmeBxiCSDY5WsZp4WPtUsE"

IMAGES_DIRECTORY = "images"


def main() -> None:
    image_files = ImageFiles(IMAGES_DIRECTORY).get()
    print(f"Processing {len(image_files)} images...")

    world = World(API_KEY)

    problematic_images = []
    located_images: defaultdict = defaultdict(list)
    counter = 0
    for image_file in image_files:
        try:
            coordinates = image_file.get_coordinates()
            location = world.locate(coordinates)
            located_images[location.city].append(LocatedImage(image_file, location))
            counter += 1
            if counter % 100 == 0:
                print(f"Have processed {counter}.")
        except UnsupportedImageFormatError:
            problematic_images.append(image_file.name)
        except InvalidLocationError:
            problematic_images.append(image_file.name)

    print("Finished processing all the images.")
    print(f"There were {len(problematic_images)} problematic images.")

    print("Organising images into folders...")
    for city in located_images.keys():
        city_snake_case = city.replace(" ", "_")
        os.mkdir(f"images/{city_snake_case}")
        for image in located_images[city]:
            os.rename(
                image.image_file.filepath,
                f"images/{city_snake_case}/{image.image_file.name}",
            )

    print("Done.")


@dataclass
class LocatedImage:
    image_file: ImageFile
    location: Location

    def __repr__(self) -> str:
        return f"{self.image_file} ({self.location})"


if __name__ == "__main__":
    main()
