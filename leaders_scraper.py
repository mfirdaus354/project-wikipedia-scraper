import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import os


root_url = "https://country-leaders.onrender.com"
cookies_url = f"{root_url}/cookie"
cookies_dict = dict(cookies_are='working')

async def fetch_url(url, session, cookies=None):
    # define fetch_url function to query root_url to a particular endpoints
    async with session.get(url, cookies=cookies) as response:
        return await response.json()

async def get_countries(session, cookies):
    # define get_countries function to query root_url to "/countries" endpoint, 
    # then assign and return to querried_countries variable
    countries_url= f"{root_url}/countries"
    querried_countries = await fetch_url(countries_url, session, cookies)
    return querried_countries

async def get_leaders(country, session, cookies):
    # define get_countries function to query root_url to "/leaders" endpoint, 
    # parse through country in querried_countries
    # then assign and return to querried_leaders variable as a dictionary
    leaders_url = f"{root_url}/leaders?country={country}"
    querried_leaders = await fetch_url(leaders_url, session, cookies)
    leaders = {country: [{f"{leader['first_name']} {leader['last_name']}": leader['wikipedia_url']} for leader in querried_leaders]}
    return leaders 

async def scrape_leaders_info(country, leaders, session):
    summary_file = os.path.dirname(os.path.abspath(__file__))
    leader_summary = os.path.join(summary_file, "leader-summary.txt")
    for leader in leaders:
        for key_people, wikipedia_leader in leader.items():
            async with session.get(wikipedia_leader) as response:
                html_content = await response.text()
                leader_soup = BeautifulSoup(html_content, 'html.parser')
                header_content = leader_soup.find_all('h2')  
                paragraph_content = leader_soup.find_all('p')
                sentences = []
                for header in header_content:
                    header_text = header.get_text()
                    sentences.append(header_text)
                for paragraph in paragraph_content:
                    paragraph_text = paragraph.get_text()
                    sentences.append(paragraph_text)

                main_content = [] 
                main_content.extend(sentences)  
                
                for content in main_content:  
                    pattern = r'(?:^|\s)([A-Z].*?[.!?])(?=\s|$)'
                    matches = re.findall(pattern, content)
                    sentences.extend(matches)  

                with open(leader_summary, "a", encoding="utf-8") as leader_story:
                    leader_story.write(f"""
                                       Leaders of {country}
                                    ----------------------------------------------
                                        {key_people}
                                        {sentences}
                                    ----------------------------------------------
                                        """)


async def main():
    async with aiohttp.ClientSession() as session:
        cookies = await fetch_url(cookies_url, session, cookies_dict)
        countries = await get_countries(session, cookies)
        print(countries[0])

        tasks = []
        for country in countries:
            tasks.append(asyncio.create_task(get_leaders(country, session, cookies)))

        leader_per_country = {}
        for task in asyncio.as_completed(tasks):
            leaders = await task
            leader_per_country.update(leaders)

        for country, leaders in leader_per_country.items():
            await scrape_leaders_info(country, leaders, session)

asyncio.run(main())