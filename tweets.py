from twikit import Client, TooManyRequests
import time
from datetime import datetime
import csv
from configparser import ConfigParser
from random import randint
import asyncio
import json

MINIMUM_TWEETS = 10
QUERY = 'alegeri lang:ro until:2020-01-01 since:2018-01-01'


def get_tweets(tweets,client,query):
    query=query+' lang:ro until:2020-01-01 since:2018-01-01'
    if tweets is None:
        #* get tweets
        print(f'{datetime.now()} - Getting tweets...')
        tweets = client.search_tweet(query, product='Top')
    else:
        wait_time = randint(5, 10)
        print(f'{datetime.now()} - Getting next tweets after {wait_time} seconds ...')
        time.sleep(wait_time)
        tweets = tweets.next()

    return tweets


#* login credentials
config = ConfigParser()
config.read('config.ini')
username = config['X']['username']
email = config['X']['email']
password = config['X']['password']

#* create a csv file
with open('tweets.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Tweet_count', 'Username', 'Text', 'Created At', 'Retweets', 'Likes'])




async def run_tweets(query):
    #* authenticate to X.com
    client = Client(language='en-US')
    # try:
    #     await client.login(auth_info_1=username, auth_info_2=email, password=password)
    # except Exception as e:
    #     print(f"Error during login: {e}")
    # await client.save_cookies('cookies.json')

    client.load_cookies('cookies.json')

    tweet_count = 0
    tweets = None

    current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = f"tweets/log_{current_time}.json"
    
    while tweet_count < MINIMUM_TWEETS:
        try:
            tweets = await get_tweets(tweets, client,query)  # Await the async function to get tweets
        except TooManyRequests as e:
            rate_limit_reset = datetime.fromtimestamp(e.rate_limit_reset)
            print(f'{datetime.now()} - Rate limit reached. Waiting until {rate_limit_reset}')
            wait_time = rate_limit_reset - datetime.now()
            await asyncio.sleep(wait_time.total_seconds())  # Await async sleep
            continue

        if not tweets:
            print(f'{datetime.now()} - No more tweets found')
            break

        
        # Open the log file in 'append' mode so we can write all tweets to it
        with open(log_filename, 'a', encoding='utf-8') as log_file:
            for tweet in tweets:
                tweet_count += 1
                
                # Create the tweet data as a dictionary (not a list)
                tweet_data = {
                    'tweet_count': tweet_count,
                    'username': tweet.user.name,
                    'text': tweet.text,
                    # 'created_at': tweet.created_at.isoformat(),  # Convert datetime to string
                    'retweets': tweet.retweet_count,
                    'likes': tweet.favorite_count
                }
                
                # Write each tweet as a JSON object to the log file
                json.dump(tweet_data, log_file, ensure_ascii=False, indent=4)
                log_file.write('\n')  # Write a newline between each tweet JSON object


        print(f'{datetime.now()} - Got {tweet_count} tweets')

    print(f'{datetime.now()} - Done! Got {tweet_count} tweets found')
    return log_filename


async def main():
    #* authenticate to X.com
    client = Client(language='en-US')
    # try:
    #     await client.login(auth_info_1=username, auth_info_2=email, password=password)
    # except Exception as e:
    #     print(f"Error during login: {e}")
    # await client.save_cookies('cookies.json')

    client.load_cookies('cookies.json')

    tweet_count = 0
    tweets = None

    while tweet_count < MINIMUM_TWEETS:
        try:
            tweets = await get_tweets(tweets, client)  # Await the async function to get tweets
        except TooManyRequests as e:
            rate_limit_reset = datetime.fromtimestamp(e.rate_limit_reset)
            print(f'{datetime.now()} - Rate limit reached. Waiting until {rate_limit_reset}')
            wait_time = rate_limit_reset - datetime.now()
            await asyncio.sleep(wait_time.total_seconds())  # Await async sleep
            continue

        if not tweets:
            print(f'{datetime.now()} - No more tweets found')
            break

        
        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_filename = f"tweets/log_{current_time}.json"
        # Open the log file in 'append' mode so we can write all tweets to it
        with open(log_filename, 'a', encoding='utf-8') as log_file:
            for tweet in tweets:
                tweet_count += 1
                
                # Create the tweet data as a dictionary (not a list)
                tweet_data = {
                    'tweet_count': tweet_count,
                    'username': tweet.user.name,
                    'text': tweet.text,
                    # 'created_at': tweet.created_at.isoformat(),  # Convert datetime to string
                    'retweets': tweet.retweet_count,
                    'likes': tweet.favorite_count
                }
                
                # Write each tweet as a JSON object to the log file
                json.dump(tweet_data, log_file, ensure_ascii=False, indent=4)
                log_file.write('\n')  # Write a newline between each tweet JSON object


        print(f'{datetime.now()} - Got {tweet_count} tweets')

    print(f'{datetime.now()} - Done! Got {tweet_count} tweets found')

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())  # Use asyncio to run the main function