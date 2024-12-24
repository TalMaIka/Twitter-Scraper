# Twitter Scraper Tool

## Overview
The Twitter Scraper Tool is a Python-based automation script leveraging Selenium to scrape data from Twitter (now X). It collects followers, tweets, and replies for a specified main user and their followers. Additionally, the tool compares replies to identify similarities using the SequenceMatcher algorithm.

## Features
- **Automated Login**: Log in to Twitter with provided credentials.
- **Followers Scraping**: Retrieve a list of followers for the main user.
- **Replies Scraping**: Collect replies from the main user and their followers.
- **Reply Comparison**: Identify similar replies between the main user and their followers based on a similarity threshold.
- **Data Persistence**: Save scraped data to a JSON file and skip re-scraping existing data.

## Requirements
- Python 3.7+
- Selenium WebDriver
- Google Chrome
- Chromedriver (compatible with the installed Chrome version)

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/twitter-scraper.git
   cd twitter-scraper
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Download Chromedriver:
   - Ensure compatibility with your Chrome version.
   - Place `chromedriver.exe` in the project directory.

## Configuration
### Login Credentials
Update the `email`, `username`, and `password` variables in the `__main__` section of the script.

### File Paths
Specify the path to `chromedriver.exe` in the `Service` initialization.

### Similarity Threshold
The similarity threshold is used to determine if two replies are similar. It is set to `0.7` by default but can be modified in the `compare_replies` function:
```python
similarity = SequenceMatcher(None, main_reply, reply).ratio()
if similarity > 0.7:  # Adjust this value to set the threshold
```
- Increase the threshold to make comparisons stricter.
- Decrease the threshold to allow for more lenient comparisons.

## Usage
1. Run the script:
   ```bash
   python3 TwitterScraper.py
   ```
2. Enter the username of the main user when prompted.
3. View scraped data in the `followers_data.json` file.

## Output
- **followers_data.json**:
  - Stores followers, replies, and similarity results.
  - Example structure:
    ```json
    {
        "main_user": {
            "followers": ["@follower1", "@follower2"],
            "main_user_replies": ["Main reply 1", "Main reply 2"],
            "similar_replies": {
                "@follower1": [
                    {
                        "main_user_reply": "Main reply 1",
                        "follower_reply": "Follower reply similar to main reply",
                        "similarity_score": 0.8
                    }
                ]
            }
        }
    }
    ```

## Limitations
- Scraping is dependent on Twitter’s website structure and may break if elements are updated.
- Ensure compliance with Twitter’s terms of service while using this tool.
