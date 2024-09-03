import json


class Settings:

    @staticmethod
    def get_settings_file() -> dict:
        with open('settings.json') as settings_file:
            return json.load(settings_file)

    @staticmethod
    def get_cities_from_settings(fetcher_type: str) -> tuple:
        settings = Settings.get_settings_file()
        return tuple(settings[fetcher_type]['cities'])

    @staticmethod
    def get_active_status(fetcher_type: str) -> bool:
        settings = Settings.get_settings_file()
        return settings[fetcher_type]['is_active']

    @staticmethod
    def save_settings(settings: str) -> None:
        with open('settings.json', 'w') as settings_file:
            settings_file.write(settings)

    @staticmethod
    def get_iteration_time_from_settings_file(fetcher_type: str) -> int:
        settings = Settings.get_settings_file()
        return settings[fetcher_type]['iteration_time_hs'] * 3600


