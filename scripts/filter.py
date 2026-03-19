import os
import json
import gspread
import time
from google import genai
from oauth2client.service_account import ServiceAccountCredentials

# 1. Setup Gemini with the NEW library
client_ai = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def process_and_filter():
    # Connect to Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(os.environ["GCP_SERVICE_ACCOUNT_KEY"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    gc = gspread.authorize(creds)
    
    db = gc.open_by_key(os.environ["GOOGLE_SHEET_ID"])
    raw_sheet = db.worksheet("Raw_Items")
    review_sheet = db.worksheet("Review")

    # Get all news
    records = raw_sheet.get_all_records()
    if not records:
        print("No news to filter.")
        return

    # Prepare a list of headlines for the AI
    headlines_list = "\n".join([f"- {r['Title']}" for r in records])

    prompt = f"""
    You are a senior news editor. Review this list of news headlines:
    {headlines_list}

    Score each headline from 1-10 based on global significance and geopolitical impact.
    Return ONLY a JSON list of numbers in the exact same order as the headlines.
    Example output: [3, 8, 1, 10, 5]
    """

    print(f"AI is analyzing {len(records)} articles in one batch...")
    
    # Send ONE request for ALL headlines
    response = client_ai.models.generate_content(
        model="gemini-2.0-flash", 
        contents=prompt
    )
    
    try:
        # Clean up the response text in case the AI adds markdown backticks
        raw_output = response.text.replace("```json", "").replace("```", "").strip()
        scores = json.loads(raw_output)
        
        for i, score in enumerate(scores):
            if score >= 7:
                article = records[i]
                review_sheet.append_row([article['Title'], article['URL'], article['Source'], score])
                print(f"✅ Kept: {article['Title'][:50]}... (Score: {score})")
        
        # Clear raw sheet after successful processing
        raw_sheet.delete_rows(2, len(records) + 1)
        print("Success! High-quality news moved to 'Review' tab.")

    except Exception as e:
        print(f"Error parsing AI response: {e}")
        print(f"AI actually said: {response.text}")

if __name__ == "__main__":
    process_and_filter()
