from asyncio import run
from os import getenv

from browser_use import Agent, Browser, ChatGoogle, ChatOllama, ChatOpenAI
from browser_use.llm import ChatDeepSeek

from autobrowser.utils import get_browser_ip

LLM_OPTIONS = {
    "ollama": ChatOllama(model="llama3.1"),
    "openai": ChatOpenAI(model="gpt-5.4-nano"),
    "gemini": ChatGoogle(model="gemini-2.5-flash-lite"),
    "deepseak": ChatDeepSeek(api_key=getenv("DEEPSEAK_API_KEY")),
}

TASK = """
1. Visit page https://hok-elanto.fi/s-etukortti/ajankohtaista-asiakasomistajalle
2. Check bonus doubled (bonus tuplana) section on the page
3. Determine campaign offerings and their validity
4. Summarize in json format with shop short name and date
"""

TASK = """
1. Find official Marriot Bonvoy website for Westin Bora Bora Resort & Spa
2. Check low price calendar for November 2026, 4 nights, 2 adults, using "flexible dates" from "Date" dropdown from the website
3. Summarize the lowest price in json format with hotel short name, date and price
4. Further check rate details for the lowest (and earliest if on-par) date, find half-board price for the entry room type and report
"""


async def run_tasks():
    """entry point"""

    agent = Agent(
        task=TASK,
        llm=LLM_OPTIONS["gemini"],
        browser=Browser(cdp_url=get_browser_ip()),
    )
    history = await agent.run()
    print(history.final_result())


def main():
    """async wrapper for main entry point"""
    run(run_tasks())


if __name__ == "__main__":
    main()
