from fetcher import SprzedajemyFetcher
from agent import Agent

sprzedajemy_fetcher = SprzedajemyFetcher("Malbork") # NOQA

agent = Agent(sprzedajemy_fetcher)
agent.start_all_fetchers()