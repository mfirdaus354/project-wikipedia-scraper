import sys

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
import re

root_url = "https://country-leaders.onrender.com"
cookies_url = f"{root_url}/cookie"
cookies_dict = dict(cookies_are='working')
countries_url = f"{root_url}/countries"


async def get_countries_and_leaders():
    async with aiohttp.ClientSession() as session:
        # Make the cookies request
        async with session.get(cookies_url, cookies=cookies_dict) as response:
            ultimate_cookies = response.cookies

        # Make the countries request
        async with session.get(countries_url, cookies=ultimate_cookies) as response:
            some_countries = await response.json()

        # Fetch leaders for each country asynchronously
        tasks = []
        for country in some_countries:
            leaders_url = f"{root_url}/leaders?country={country}"
            task = asyncio.create_task(fetch_leaders(session, leaders_url, ultimate_cookies))
            tasks.append(task)

        # Wait for all leader requests to complete
        leader_responses = await asyncio.gather(*tasks)

        final_dict = {}
        for leaders in leader_responses:
            for country, leader_names in leaders.items():
                if country not in final_dict:
                    final_dict[country] = leader_names
                else:
                    final_dict[country].extend(leader_names)

        return final_dict


async def fetch_leaders(session, leaders_url, cookies):
    async with session.get(leaders_url, cookies=cookies) as response:
        some_leaders = await response.json()
        leader_names = []
        for leader in some_leaders:
            name = leader["first_name"] + " " + leader["last_name"]
            wikipedia_url = leader["wikipedia_url"].replace("nl", "en")
            leader_names.append({name: wikipedia_url})
        return leader_names


def extract_sentences(url, tag="p"):
    response = requests.get(url)
    leader_soup = BeautifulSoup(response.content, 'html.parser')
    tag_content = leader_soup.find_all(tag)
    sentences = []
    for content in tag_content:
        text = content.get_text()
        pattern = r'(?:^|\s)([A-Z].*?[.!?])(?=\s|$)'
        matches = re.findall(pattern, text)
        sentences.extend(matches)
    return sentences


async def process_countries():
    leader_per_country = await get_countries_and_leaders()

    for country, leaders in leader_per_country.items():
        for leader in leaders:
            for name, wikipedia_leader in leader.items():
                leader_summary_file = "C:\\Users\\dimas\\Desktop\\BECODE\\PROJECTS\\project-wikipedia-scrapper\\leader-summary.txt"
                sentences = extract_sentences(wikipedia_leader)

                with open(leader_summary_file, "a") as leader_story:
                    leader_story.write(f"""Leaders of {country}
----------------------------------------------
{name}
{sentences}
----------------------------------------------""")


async def main():
    await process_countries()



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

    
