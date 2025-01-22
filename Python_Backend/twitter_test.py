import tweepy
import psycopg2
from transformers import pipeline
from datetime import datetime
import time
from dotenv import load_dotenv
import os

load_dotenv()
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_PORT = os.getenv("DB_PORT")

# Connect to PostgreSQL
try:
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    cursor = conn.cursor()
    print("Connected to PostgreSQL database!")
except Exception as e:
    print(f"Error: {e}")
    exit()

# Set up the client
client = tweepy.Client(bearer_token=BEARER_TOKEN)

# Hugging Face sentiment analysis pipeline
sentiment_model = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

# Query for recent tweets
query = "H1B"
max_results = 100

def fetch_tweets_with_retry():
    """Fetch tweets with retry logic for handling disconnections."""
    retry_count = 5  # Number of retry attempts
    wait_time = 10  # Time to wait before retrying

    for attempt in range(retry_count):
        try:
            # Fetch tweets with expansions for author_id
            response = client.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=["created_at"],
                expansions=["author_id"],
                user_fields=["username"]
            )
            return response  # Successfully fetched
        except tweepy.errors.TooManyRequests as e:
            reset_time = int(e.response.headers.get("x-rate-limit-reset", time.time() + 900))
            wait_time = reset_time - int(time.time())
            print(f"Rate limit exceeded. Waiting for {wait_time} seconds...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"Error during tweet fetch attempt {attempt + 1}/{retry_count}: {e}")
            time.sleep(wait_time)  # Wait and retry

    print("Failed to fetch tweets after retries.")
    return None

def analyze_sentiment_hf(content):
    """
    Analyze sentiment using Hugging Face Transformers.
    Maps results to 'positive', 'neutral', or 'negative'.
    """
    try:
        result = sentiment_model(content[:512])[0]  # Truncate to 512 tokens
        label = result["label"]
        # Map the model's output to simplified sentiments
        if "4 star" in label or "5 star" in label:
            return "positive"
        elif "3 star" in label:
            return "neutral"
        else:
            return "negative"
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        return "neutral"  # Default to neutral on error

def reanalyze_existing_sentiments():
    """
    Reanalyze tweets already in the database and update their sentiment using Hugging Face.
    """
    try:
        # Fetch all tweets from the database
        cursor.execute("SELECT tweet_id, content FROM tweets;")
        tweets = cursor.fetchall()

        if not tweets:
            print("No tweets found in the database.")
            return

        print(f"Reanalyzing {len(tweets)} tweets...")

        for tweet_id, content in tweets:
            # Use the Hugging Face model for sentiment analysis
            new_sentiment = analyze_sentiment_hf(content)

            # Update the sentiment in the database
            try:
                cursor.execute(
                    "UPDATE tweets SET sentiment = %s WHERE tweet_id = %s;",
                    (new_sentiment, tweet_id),
                )
                conn.commit()
                print(f"Updated tweet ID {tweet_id} with new sentiment '{new_sentiment}'.")
            except Exception as e:
                print(f"Error updating tweet ID {tweet_id}: {e}")

    except Exception as e:
        print(f"Error during reanalysis of sentiments: {e}")

# Prompt the user to decide whether to run Twitter scraping or reanalyze existing sentiments
user_input = input("Choose an option:\n1. Run Twitter scraping\n2. Reanalyze existing sentiments\nEnter 1 or 2: ").strip()

if user_input == "1":
    print("Twitter scraping is enabled. Starting the process...")
    while True:
        try:
            response = fetch_tweets_with_retry()
            if not response or not response.data:
                print("No tweets found or failed to fetch tweets!")
                continue

            # Create a mapping of author_id to username
            users = {user["id"]: user["username"] for user in response.includes["users"]}

            for tweet in response.data:
                tweet_id = str(tweet.id)  # Convert bigint to string
                content = tweet.text
                created_at = tweet.created_at  # Timestamp from the tweet
                username = users.get(tweet.author_id, None)  # Map author_id to username

                # Perform sentiment analysis using Hugging Face
                sentiment = analyze_sentiment_hf(content)

                # Insert into PostgreSQL
                try:
                    cursor.execute(
                        """
                        INSERT INTO tweets (tweet_id, username, content, sentiment, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (tweet_id) DO NOTHING
                        """,
                        (tweet_id, username, content, sentiment, created_at)
                    )
                    conn.commit()
                    print(f"Inserted tweet ID {tweet_id} with sentiment '{sentiment}' into the database.")
                except Exception as e:
                    print(f"Error inserting tweet ID {tweet_id}: {e}")

            # Pause between requests to avoid additional rate limiting
            time.sleep(5)

        except Exception as e:
            print(f"Unexpected error: {e}")
            break

elif user_input == "2":
    print("Reanalyzing existing sentiments in the database...")
    reanalyze_existing_sentiments()

else:
    print("Invalid option. Exiting...")

# Close the database connection
cursor.close()
conn.close()
