class Agent:
    def __init__(self, fetchers):
        self.fetchers = fetchers

    def start_all(self):
        for fetcher in self.fetchers:
            fetcher.start()

    @staticmethod
    def settings(fetcher, *settings) -> None:
        fetcher.settings(*settings)
