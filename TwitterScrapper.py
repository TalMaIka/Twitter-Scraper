import json
import time
import re
import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from difflib import SequenceMatcher


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("twitter_scraper.log"),
        logging.StreamHandler()
    ]
)

# Constants
CHROME_DRIVER_PATH = '<Chromedriver-Path>'
BASE_URL = "https://x.com"
LOGIN_URL = f"{BASE_URL}/login"


def automated_login(driver, email, username, password):
    try:
        logging.info("Navigating to login page...")
        driver.get(LOGIN_URL)
        time.sleep(3)

        # Input email
        email_field = driver.find_element(By.CSS_SELECTOR, "input[name='text']")
        email_field.send_keys(email)
        email_field.send_keys(Keys.ENTER)
        time.sleep(1)

        # Input username
        username_field = driver.find_element(By.CSS_SELECTOR, "input[data-testid='ocfEnterTextTextInput']")
        username_field.send_keys(username)
        username_field.send_keys(Keys.ENTER)
        time.sleep(1)

        # Input password
        password_field = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
        password_field.send_keys(password)
        password_field.send_keys(Keys.ENTER)
        time.sleep(1)

        # Check if login was successful
        if driver.current_url == f"{BASE_URL}/home":
            logging.info("Login successful.")
        else:
            logging.warning("Login failed or additional steps required.")
    except Exception as e:
        logging.error(f"An error occurred during login: {e}")

def contains_hebrew(text):
    return bool(re.search(r'[\u0590-\u05FF]', text))

def scrape_replies_from_url(driver, url):
    try:
        logging.info(f"Scraping replies from URL: {url}")
        driver.get(url)
        time.sleep(2)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.css-175oi2r"))
        )

        comments = set()
        previous_reply_count = 0
        while True:
            div_elements = driver.find_elements(By.CSS_SELECTOR, "div.css-175oi2r")

            for div in div_elements:
                try:
                    comment_span = div.find_element(By.CSS_SELECTOR, "span.css-1jxf684")
                    comment_text = comment_span.text.strip()

                    # Exclude comments shorter than 10 characters
                    if comment_text and len(comment_text) >= 10 and not re.fullmatch(r'@\S+', comment_text):
                        comments.add(comment_text)
                except Exception:
                    continue

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            current_reply_count = len(div_elements)
            if current_reply_count == previous_reply_count:
                break
            previous_reply_count = current_reply_count

        return list(comments)

    except Exception as e:
        logging.error(f"An error occurred while scraping replies: {e}")
        return []

def scrape_followers(driver, base_url):
    try:
        url = f"{base_url}/followers"
        logging.info(f"Scraping followers from: {url}")
        driver.get(url)
        time.sleep(2)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.css-1jxf684"))
        )

        followers = set()
        previous_follower_count = 0
        while True:
            span_elements = driver.find_elements(By.CSS_SELECTOR, "span.css-1jxf684")
            for element in span_elements:
                follower_username = element.text
                if follower_username and follower_username.startswith('@'):
                    followers.add(follower_username)

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            current_follower_count = len(span_elements)
            if current_follower_count == previous_follower_count:
                break
            previous_follower_count = current_follower_count

        return list(followers)

    except Exception as e:
        logging.error(f"An error occurred while scraping followers: {e}")
        return []

def load_existing_data(filename):
    """Load existing data from the JSON file."""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

def update_json_file(filename, data):
    """Update the JSON file with new data."""
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logging.info("Data has been updated successfully!")
    except Exception as e:
        logging.error(f"An error occurred while updating the JSON file: {e}")

def scrape_main_user_replies_with_skip(driver, main_user, existing_data):
    """Scrape main user replies, skipping if data already exists."""
    if main_user in existing_data and 'main_user_replies' in existing_data[main_user]:
        logging.info(f"Replies for {main_user} already exist. Skipping scraping.")
        return existing_data[main_user]['main_user_replies']

    reply_url = f"{BASE_URL}/search?l=&q=from%3A{main_user}&src=typd&lang=nl"
    return scrape_replies_from_url(driver, reply_url)

def scrape_followers_with_skip(driver, base_url, main_user, existing_data):
    """Scrape followers, skipping if data already exists."""
    if main_user in existing_data and 'followers' in existing_data[main_user]:
        logging.info(f"Followers for {main_user} already exist. Skipping scraping.")
        return existing_data[main_user]['followers']

    return scrape_followers(driver, base_url)

def scrape_replies_for_followers_with_skip(driver, followers, existing_data):
    """Scrape replies for followers, skipping if data already exists."""
    all_replies = {}
    for follower in followers:
        if follower in existing_data and 'replies' in existing_data[follower]:
            logging.info(f"Replies for {follower} already exist. Skipping scraping.")
            all_replies[follower] = existing_data[follower]['replies']
        else:
            reply_url = f"{BASE_URL}/search?l=&q=from%3A{follower}&src=typd&lang=nl"
            all_replies[follower] = scrape_replies_from_url(driver, reply_url)

    return all_replies

def compare_replies(main_user_replies, all_replies):
    similar_replies = {}

    for follower, replies in all_replies.items():
        for reply in replies:
            for main_reply in main_user_replies:
                similarity = SequenceMatcher(None, main_reply, reply).ratio()
                if similarity > 0.7:
                    if follower not in similar_replies:
                        similar_replies[follower] = []
                    similar_replies[follower].append({
                        'main_user_reply': main_reply,
                        'follower_reply': reply,
                        'similarity_score': similarity
                    })

    return similar_replies

if __name__ == "__main__":
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    filename = 'followers_data.json'
    existing_data = load_existing_data(filename)

    username_input = input("Enter the username of the main user: ")

    email = "<Email>"
    username = "<@Username>"
    password = "<Password>"

    automated_login(driver, email, username, password)

    main_user_replies = scrape_main_user_replies_with_skip(driver, username_input, existing_data)

    followers_url = f"{BASE_URL}/{username_input}"
    main_user_followers = scrape_followers_with_skip(driver, followers_url, username_input, existing_data)

    all_replies = scrape_replies_for_followers_with_skip(driver, main_user_followers, existing_data)

    similar_replies = compare_replies(main_user_replies, all_replies)

    existing_data[username_input] = {
        'followers': main_user_followers,
        'main_user_replies': main_user_replies,
        'similar_replies': similar_replies
    }

    for follower, replies in all_replies.items():
        if follower not in existing_data:
            existing_data[follower] = {}
        existing_data[follower]['replies'] = replies

    update_json_file(filename, existing_data)

    driver.quit()
