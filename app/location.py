from dataclasses import dataclass

import requests

from app.image import Coordinates


class InvalidLocationError(Exception):
    pass


@dataclass
class Location:
    data: dict

    @property
    def city(self) -> str:
        try:
            return self.data["items"][0]["address"]["city"]
        except KeyError as e:
            raise InvalidLocationError from e
        except IndexError as e:
            raise InvalidLocationError from e

    def __repr__(self) -> str:
        return self.city


@dataclass
class World:
    URI = "https://revgeocode.search.hereapi.com/v1/revgeocode"
    api_key: str

    def locate(self, coordinates: Coordinates) -> Location:
        params = {
            "apiKey": self.api_key,
            "at": f"{coordinates.latitude},{coordinates.longitude}",
            "lang": "en-US",
            "limit": "1",
        }

        response = requests.get(self.URI, headers={}, params=params)
        response.raise_for_status()
        return Location(response.json())
