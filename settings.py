from fetcher import SprzedajemyFetcher


class SprzedajemySettings:
    def __init__(self, sprzedajemy_fetcher):
        self.fetcher = sprzedajemy_fetcher

    def from_json(self, settings_json: dict):

#
# class OtomotoSettings:
#     @classmethod
#     def from_json(cls, settings_json: dict) -> OtomotoSettings:
#         ...
#
#
# class OLXSettings:
#     @classmethod
#     def from_json(cls, settings_json: dict) -> OLXSettings:
#         ...
