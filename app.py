from flask import Flask, render_template, request, redirect, url_for
import joblib
import numpy as np
from bokeh.plotting import figure
from bokeh.embed import components
import stanza
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
from gensim.utils import simple_preprocess
import os
from werkzeug.utils import secure_filename
import nltk
from nltk.tokenize import word_tokenize
from gensim.utils import simple_preprocess
from datetime import datetime
import json
import re
import asyncio
# import tweets.py
from datetime import datetime
import csv
from configparser import ConfigParser
from random import randint
import asyncio
import json
from twikit import Client, TooManyRequests
import time
from tensorflow import keras

from keras.preprocessing.sequence import pad_sequences


stanza.download('ro')
nlp = stanza.Pipeline('ro')
nltk.download('stopwords')
nltk.download('punkt')
# Load result_list from the JSON file
with open('result_list_stopwords.json', 'r') as f:
    stop_words = set(json.load(f))
print(stop_words)

with open('word_embeddings.json', 'r', encoding='utf-8') as f:
    word_embeddings = json.load(f)


# Load the trained model and vectorizer
model = keras.models.load_model('my_model.h5')
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Initialize Flask app
app = Flask(__name__)

LAST_TIME="PLACEHOLDER"
LAST_MESSAGE="PLACEHOLDER"
LAST_SENTIMENT="PLACEHOLDER"
LAST_ACTION="PLACEHOLDER"
LAST_EXTRA="PLACEHOLDER"

# Set up file upload folder and allowed extensions
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'txt'}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Create the logs folder if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')


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
    
    while tweet_count < 5:
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

        tweetz=[]
        print (tweets)
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
            tweetz.append(tweet_data)
        # Open the log file in 'append' mode so we can write all tweets to it
        with open(log_filename, 'a', encoding='utf-8') as log_file:
                # Write each tweet as a JSON object to the log file
            json.dump(tweetz, log_file, ensure_ascii=False, indent=4)
            # log_file.write('\n')  # Write a newline between each tweet JSON object


        print(f'{datetime.now()} - Got {tweet_count} tweets')

    print(f'{datetime.now()} - Done! Got {tweet_count} tweets found')
    return log_filename

def log_analysis(data, sentiment, task_type, extra=None):
    global LAST_TIME, LAST_MESSAGE, LAST_SENTIMENT, LAST_ACTION, LAST_EXTRA

    # Get current system time for unique filename
    current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = f"logs/log_{current_time}.json"

    LAST_TIME=current_time
    LAST_MESSAGE=data
    LAST_SENTIMENT=sentiment
    LAST_ACTION=task_type
    LAST_EXTRA=extra
    
    # Prepare the log entry
    log_entry = {
        'timestamp': current_time,
        'text': data,  # Original text analyzed (can be truncated if needed)
        'sentiment': sentiment,
        'task_type': task_type,
        'extra':extra
    }

    # Write the log to the file (overwrite or create a new file each time)
    with open(log_filename, 'w', encoding='utf-8') as log_file:
        json.dump(log_entry, log_file, ensure_ascii=False, indent=4)

# Define functions for stopwords, bigrams, trigrams and lemmatization
def remove_stopwords(texts):
    return [[word for word in simple_preprocess(str(doc)) if word not in stop_words] for doc in texts]

def lemmatization(texts, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV']):
    """
    Lemmatize the input texts using Stanza, with specified allowed POS tags.

    :param texts: List of sentences (list of lists of words)
    :param allowed_postags: List of allowed POS tags for lemmatization
    :return: List of lemmatized words
    """
    # texts_out = []
    # Process the sentence with Stanza
    doc = nlp(texts) 
    
    # Extract the lemmatized tokens based on allowed POS tags
    lemmatized_tokens = [word.lemma for sent in doc.sentences for word in sent.words if word.pos in allowed_postags]
    
        # texts_out.append(lemmatized_tokens)
    
    return lemmatized_tokens

def pre_proc(rev):
    # Remove Stop Words
    


    rev = re.sub(r'http[s]?://\S+|www\.\S+', '', rev)
    
    # Remove @ mentions
    rev = re.sub(r'@\w+', '', rev)

    [rev] = remove_stopwords([rev])

    print(rev)

    rev=' '.join(rev)


    # Do lemmatization keeping only noun, adj, vb, adv
    data_lemmatized = lemmatization(rev, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV'])
    return data_lemmatized


# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']



# # Function to preprocess and predict sentiment
# def predict_sentiment(text):
#     # Preprocessing (stopwords, lemmatization)
#     # Replace this with your pre-processing pipeline
#     review=' '.join(pre_proc(text))
#     print(review)
#     review_vec = vectorizer.transform([review])  # Vectorize the input review
#     prediction = model.predict(review_vec)  # Predict sentiment
#     # Assuming the prediction is 1 for Positive, 0 for Negative
#     sentiment = "Positive" if prediction == 1 else "Negative"
#     return sentiment

def predict_sentiment(text):
    # Preprocessing (stopwords, lemmatization)
    review = pre_proc(text)
    print(review)

    np.set_printoptions(precision=10)

    # Process positive and negative reviews into word embeddings
    reviews_embeddings = [word_embeddings[word] if word in word_embeddings else np.zeros(300) for word in review]

    # Pad the sequence to have a consistent length of 60
    reviews_embeddings = pad_sequences([reviews_embeddings], maxlen=60, padding='post', truncating='post', dtype='float64')

    # Check the shape to ensure it's (1, 60, 300)
    print(f"Shape of reviews_embeddings: {reviews_embeddings.shape}")

    # Predict sentiment
    prediction = model.predict(reviews_embeddings)  # Predict sentiment
    sentiment = "Positive" if prediction[0][0] >= 0.5 else "Negative"
    print(f"Prediction: {prediction[0][0]} - Sentiment: {sentiment}")
    return sentiment


def predict_percentage(text):

    if not isinstance(text, list):
        sentences = sent_tokenize(text)  # Split the text into sentences
    else:
        sentences = text
    
    # Placeholder for storing results
    positive_count = 0
    total_sentences = len(sentences)
    
    # Analyze each sentence (you can replace this with your own sentiment analysis logic)
    for sentence in sentences:
        sentiment = predict_sentiment(sentence)  # Assuming you have a predict_sentiment function
        if sentiment == "Positive":
            positive_count += 1
    
    # Calculate the percentage of positive sentences
    sentiment_percentage = (positive_count / total_sentences) * 100 if total_sentences > 0 else 0
    return sentiment_percentage


def predict_tweets(text):

    sentences = text
    
    # Placeholder for storing results
    positive_count = 0
    positive_likes = 0
    positive_retweets = 0
    negative_likes = 0
    negative_retweets = 0
    total_sentences = len(sentences)
    
    # Analyze each sentence (you can replace this with your own sentiment analysis logic)
    for sentence in sentences:
        sentiment = predict_sentiment(sentence['text'])  # Assuming you have a predict_sentiment function
        if sentiment == "Positive":
            positive_count += 1
            positive_likes += sentence['likes']
            positive_retweets += sentence['retweets']
        else:
            negative_likes += sentence['likes']
            negative_retweets += sentence['retweets']
    
    # Calculate the percentage of positive sentences
    sentiment_percentage = (positive_count / total_sentences) * 100 if total_sentences > 0 else 0
    return (sentiment_percentage, positive_likes,negative_likes,positive_retweets,negative_retweets)



# Route for the home page
@app.route('/')
def home():
    return render_template('index.html')

# Route for handling sentiment analysis on text from the text box
@app.route('/predict_text', methods=['POST'])
def predict_text():
    if request.method == 'POST':
        review = request.form['review']  # Get review text from the form
        sentiment = predict_sentiment(review)
        log_analysis(review, sentiment, 'Text')
        
        return render_template('index.html', prediction_text=f"Sentiment: {sentiment}", task="Text")

# Route for handling sentiment analysis on file upload
@app.route('/predict_file', methods=['POST'])
def predict_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Read the content of the uploaded file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Perform sentiment analysis on the file content
            sentiment = predict_sentiment(content)
            percentage = predict_percentage(content)
            log_analysis(content, (sentiment, percentage), 'File')

            return render_template('index.html', prediction_text=f"Sentiment: {sentiment} Percentage: {percentage}", task="File")

# Route for handling sentiment analysis on tweets (for now just text input)
@app.route('/predict_tweet', methods=['POST'])
def predict_tweet():
    if request.method == 'POST':
        query = request.form['tweet']  # Get tweet text from the form

        filename =asyncio.run(run_tweets(query))
        # filename='tweets/log_2025-01-05_05-42-08.json'

        # List to store all texts
        content = []

        # Open the JSON file and read line by line
        with open(filename, 'r', encoding='utf-8') as file:
            tweets_data = json.load(file)

            # for line in file:
            #     try:
            #         # Parse each line (which is a valid JSON object)
            #         tweet_data = json.loads(line.strip())  # Strip unnecessary spaces/newlines

            #         # Extract the 'text' field and append it to the list
            #         content.append(tweet_data['text'])

            #     except json.JSONDecodeError as e:
            #         print(f"Error decoding JSON: {e} in line: {line.strip()}")

        # Print the list of all texts
        # print(texts)

        for tweet in tweets_data:
            # Clean the text of the tweet
            content.append(tweet['text'])

        # Perform sentiment analysis on the file content
        sentiment = predict_sentiment(' '.join(content))
        (percentage, positive_likes, negative_likes, positive_retweets,negative_retweets ) = predict_tweets(tweets_data)
        extra=(positive_likes, negative_likes, positive_retweets,negative_retweets)
        log_analysis(content, (sentiment, percentage), 'Tweets',extra)

        return render_template('index.html', prediction_text=f"Sentiment overall: {sentiment} Percentage: {percentage} Likes: {positive_likes}/{negative_likes} Retweets: {positive_retweets}/{negative_retweets}", task="Tweet")
    
@app.route('/flag_analysis', methods=['POST'])
def flag_analysis():
    if request.method == 'POST':
        # Retrieve the analysis text and task type from the form
        # Log the flagged analysis
        
        log_analysis(LAST_MESSAGE, LAST_SENTIMENT, "Flagged", (LAST_ACTION,LAST_TIME,LAST_EXTRA))

        # Respond with a confirmation message
        return render_template('index.html', prediction_text="The analysis has been flagged as wrong/suspect.", task="Flagged Analysis")


if __name__ == '__main__':
    app.run(debug=True)
