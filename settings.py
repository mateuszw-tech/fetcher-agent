from fetcher import SprzedajemyFetcher


class SprzedajemySettings:
    @classmethod
    def from_json(cls, settings_json: dict) -> SprzedajemySettings:
        ...


class OtomotoSettings:
    @classmethod
    def from_json(cls, settings_json: dict) -> OtomotoSettings:
        ...


class OLXSettings:
    @classmethod
    def from_json(cls, settings_json: dict) -> OLXSettings:
        ...
