from typing import Dict

from emoji import emojize

from Bot.log import logging_decor_cls


@logging_decor_cls
class Hotel:
    """
    Класс Hotel

    Args:
        all_info (Dict): передается  полная информация об отеле

    Attributes:
        _all_info(Dict): полная информация об отеле
        _name (str): название отеля
        _stars (int): количество звезд
        _rating (str): рейтинг в числовом варианте
        _rating_text (str): рейтинг в текстовом варианте
        _address (str): адрес
        _distance (str): расстояние до центра
        _price (str): цена за 1 ночь
    """

    def __init__(self, all_info: Dict) -> None:
        self._all_info = all_info
        self._name = self._all_info.get("name", '')
        self._stars = int(self._all_info.get("starRating"))
        self._rating = self._all_info.get("guestReviews", {}).get("rating", '')
        self._rating_text = self._all_info.get("guestReviews", {}).get("badgeText", '')
        self._address = ', '.join([i_value for i_key, i_value in self._all_info.get("address", {}).items()
                                   if i_key in ["streetAddress", "locality", "countryName"]])
        self._distance = self._all_info.get("landmarks", [{}])[0].get("distance", '')
        self._price = self._all_info.get("ratePlan", {}).get("price", {}).get("current", '')

    def __str__(self) -> str:
        return "*{name}*\n{stars}\n{address}\nРасстояние до центра: {distance}\n " \
               "Рейтинг: *{rating} {rating_text}*\nЦена за 1 ночь: *{price}*".format(
                                                                                stars=emojize(":star:") * self._stars,
                                                                                name=self._name,
                                                                                address=self._address,
                                                                                distance=self._distance,
                                                                                rating=self._rating,
                                                                                rating_text=self._rating_text,
                                                                                price=self._price)

    @property
    def all_info(self):
        return self._all_info

    @property
    def name(self):
        return self._name

    @property
    def starts(self):
        return self._stars

    @property
    def rating(self):
        return self._rating

    @property
    def rating_text(self):
        return self._rating_text

    @property
    def address(self):
        return self._address

    @property
    def distance(self):
        return self._distance

    @property
    def price(self):
        return self._price

    @all_info.setter
    def all_info(self, info):
        self._all_info = info
