import socket
from settings import OtomotoSettings, OLXSettings, SprzedajemySettings
from fetcher import SprzedajemyFetcher


class Agent:
    def __init__(self, *fetchers):
        self.fetchers = fetchers
        self.host_address = "127.0.0.1"
        self.port = 55555
        self.socket_to_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start_all_fetchers(self):
        self.socket_to_server.connect((self.host_address, self.port))
        for fetcher in self.fetchers:
            fetcher.start(
                self.host_address,
                self.port,
                socket.socket(socket.AF_INET, socket.SOCK_STREAM),
            )

    def set_settings(self, settings_json: dict) -> None:  # NOQA
        match settings_json["fetcher"]:
            case "Sprzedajemy":
                fetcher_type = SprzedajemyFetcher
                settings = SprzedajemySettings.from_json(settings_json)
            case "OLX":
                fetcher_type = "OLXFetcher"
                settings = OLXSettings.from_json(settings_json)
            case "Otomoto":
                fetcher_type = "OtomotoFetcher"
                settings = OtomotoSettings.from_json(settings_json)
            case _:
                print("no such fetcher found")
        for fetcher in self.fetchers:
            if isinstance(fetcher, fetcher_type):
                fetcher.settings = settings

    #  {"fetcher": "Sprzedajemy", "settings": {}}
    # if json['Sprzedajemy']:
    # obsługa sprzedajmy

    # Każdy fetcher(typ) miał dedykowaną klasę settingsów.
    # takie same klasy po stronie serwera i agenta
    # wysyłam typ fetchera i dedykowane settingsy
    # agent odbiera i deserializuje na podstawie jsona do odpowiedniej klasy settingsów
    # i zapisuje se do property fetchera
    # NAZEWNICTWO
