from collections import defaultdict
from dataclasses import dataclass
import os

from app.image import ImageFile, ImageFiles, UnsupportedImageFormatError
from app.location import InvalidLocationError, Location, World

IMAGES_DIRECTORY = "images"


def main() -> None:
    image_files = ImageFiles(IMAGES_DIRECTORY).get()
    print(f"Processing {len(image_files)} images...")

    world = World(get_here_api_key())

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
            problematic_images.append(image_file)
        except InvalidLocationError:
            problematic_images.append(image_file)

    print("Finished processing all the images.")
    print(f"There were {len(problematic_images)} problematic images.")
    directory_name = f"{IMAGES_DIRECTORY}/problematic_images"
    if not os.path.isdir(directory_name):
        os.mkdir(directory_name)
    for problematic_image in problematic_images:
        os.rename(
            f"{IMAGES_DIRECTORY}/{problematic_image.name}",
            f"{IMAGES_DIRECTORY}/problematic_images/{problematic_image.name}",
        )

    print("Organising images into folders...")
    for city in located_images.keys():
        city_snake_case = city.replace(" ", "_")

        directory_name = f"{IMAGES_DIRECTORY}/{city_snake_case}"
        if not os.path.isdir(directory_name):
            os.mkdir(directory_name)
        for image in located_images[city]:
            os.rename(
                image.image_file.filepath,
                f"{IMAGES_DIRECTORY}/{city_snake_case}/{image.image_file.name}",
            )

    print("Done.")


def get_here_api_key() -> str:
    try:
        return os.environ["HERE_API_KEY"]
    except KeyError as e:
        raise Exception("Please export the environment variable 'HERE_API_KEY'.") from e


@dataclass
class LocatedImage:
    image_file: ImageFile
    location: Location

    def __repr__(self) -> str:
        return f"{self.image_file} ({self.location})"


if __name__ == "__main__":
    main()
