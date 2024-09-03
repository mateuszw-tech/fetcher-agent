from agent import Agent
from fetcher import SprzedajemyFetcher

sprzedajemy_fetcher = SprzedajemyFetcher()
fetchers_list = [sprzedajemy_fetcher]

agent: Agent = Agent(fetchers_list)
agent.run()

