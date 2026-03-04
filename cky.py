from twikit import Client, TooManyRequests
import time
from datetime import datetime
import csv
from configparser import ConfigParser
from random import randint
import asyncio





async def main():
    #* authenticate to X.com
    client = Client(language='en-US')
    try:
        await client.login(auth_info_1='@away_throw40115', auth_info_2='throwmeaway34509@gmail.com', password='elonletmescrape')
    except Exception as e:
        print(f"Error during login: {e}")
    client.save_cookies('cookies.json')

    client.load_cookies('cookies.json')

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())  # Use asyncio to run the main function