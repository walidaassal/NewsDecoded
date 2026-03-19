import os
import json
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. Load Secrets from GitHub
GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY")
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
GCP_CREDS_JSON = os.environ.get("GCP_SERVICE_ACCOUNT_KEY")

def fetch_news():
    print("Fetching news from GNews...")
    url = f"https://gnews.io/api/v4/top-headlines?category=world&lang=en&max=10&apikey={GNEWS_API_KEY}"
    response = requests.get(url)
    
    if response.status_code != 200:
        print("Failed to fetch news:", response.text)
        return []
        
    data = response.json()
    return data.get("articles", [])

def save_to_sheets(articles):
    print("Connecting to Google Sheets...")
    # Setup Google Sheets access
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(GCP_CREDS_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # Open the sheet and select the Raw_Items tab
    sheet = client.open_by_key(SHEET_ID).worksheet("Raw_Items")
    
    print(f"Saving {len(articles)} articles to the database...")
    for article in articles:
        # We need to structure it to match our headers: ID, Title, URL, Source, Published_Date, Category
        # We will use the URL as a unique ID
        row = [
            article['url'], 
            article['title'], 
            article['url'], 
            article['source']['name'], 
            article['publishedAt'], 
            "World"
        ]
        sheet.append_row(row)
    print("Done! Data saved successfully.")

if __name__ == "__main__":
    news_articles = fetch_news()
    if news_articles:
        save_to_sheets(news_articles)
    else:
        print("No articles found.")
