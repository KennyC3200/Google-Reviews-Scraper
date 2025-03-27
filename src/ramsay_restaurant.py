import os
from ramsay_debug import *


# Constants
DEBUG = int(os.getenv("DEBUG", "0"))


class RamsayReview:
    def __init__(self):
        self.ratings: dict[str, int | str] = {}
        self.desc: str = ""

    def add_rating(self, title: str, rating: int):
        self.ratings[title] = rating

    def add_rating_by_desc(self, title: str, desc: str):
        self.ratings[title] = desc

    def add_desc(self, desc: str):
        self.desc = desc

    def __str__(self):
        ret = ""
        for title, rating in self.ratings.items():
            ret += f"{title}: {rating} | "

        if DEBUG == 0:
            ret += f"desc: {ramsay_shorten_str(self.desc)}"
        elif DEBUG == 1:
            ret += f"desc: {self.desc}"

        return ret


class RamsayRestaurant:
    def __init__(self, name: str, url: str):
        self.name: str = name
        self.url: str = url
        self.rating: int = 0
        self.reviews: list[RamsayReview] = []

    def __str__(self):
        return f"RamsayRestaurant | name: {self.name} | url: {ramsay_shorten_str(self.url, 30)}"

    def add_review(self, review: RamsayReview):
        self.reviews.append(review)

    def get_reviews_str(self) -> str:
        s = ""
        for i in range(len(self.reviews) - 1):
            s += str(self.reviews[i]) + "\n"
        s += str(self.reviews[-1])
        return s
