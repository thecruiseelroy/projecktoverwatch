from colorama import Fore, Style
import os
from concurrent.futures import ThreadPoolExecutor
from agents.url_collector import URLCollector
from agents.openrouter_agent import OpenRouterAgent
import json
import datetime
import itertools
import sys
import threading
import time
import pytz
from agents.url_scraper import URLScraper
import sqlite3

# Initialize colorama
from colorama import init
init()

class Spinner:
    def __init__(self):
        self.spinner_chars = ['/', '-', '\\', '|']
        self.running = False
        self.spinner_thread = None

    def spin(self):
        while self.running:
            for char in self.spinner_chars:
                sys.stdout.write(Fore.YELLOW + '\b' + char + Style.RESET_ALL)
                sys.stdout.flush()
                time.sleep(0.1)

    def start(self):
        self.running = True
        self.spinner_thread = threading.Thread(target=self.spin)
        self.spinner_thread.start()

    def stop(self):
        self.running = False
        if self.spinner_thread:
            self.spinner_thread.join()
        sys.stdout.write('\b \b')
        sys.stdout.flush()

def process_url(url):
    spinner = Spinner()
    spinner.start()
    try:
        with open('config.json') as config_file:
            config = json.load(config_file)
        
        agent = OpenRouterAgent(
            config['openrouter']['api_key'],
            config['openrouter']['model']
        )
        
        scraper = URLScraper()
        content = scraper.scrape_url_content(url)
        
        # Generate AI overview for every URL
        overview = agent.summarize(content) if content else "No content available for overview"
        
        # Save to database
        # Remove database operations since we're not using them anymore
        print(f"✅ Processed: {url}")
        return url
    except Exception as e:
        print(f"❌ Error processing {url}: {str(e)}")
        return None
    finally:
        spinner.stop()

def final_summary(keyword):
    with open('config.json') as config_file:
        config = json.load(config_file)
    
    agent = OpenRouterAgent(
        config['openrouter']['api_key'],
        config['openrouter']['model']
    )
    
    # Remove database operations since we're not using them anymore
    print("\nFinal analysis complete")

def clear_database():
    # Remove this function since we're not using database anymore
    print("Database operations removed")

def print_header(text):
    print(Fore.WHITE + "\n" + text)
    print("=" * len(text) + Style.RESET_ALL)

def print_step(text, status=None):
    print(Fore.WHITE + f"\n{text}", end='')
    if status:
        print(Fore.YELLOW + f"/{status}" + Style.RESET_ALL)
    print()

def create_db(db_path: str):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scraped_data
                 (id INTEGER PRIMARY KEY, 
                  url TEXT UNIQUE, 
                  title TEXT, 
                  content TEXT)''')
    conn.commit()
    conn.close()

def save_to_db(db_path: str, data: dict):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    for url, content in data.items():
        c.execute('INSERT OR IGNORE INTO scraped_data (url, title, content) VALUES (?, ?, ?)', 
                 (url, content['title'], content['content']))
    conn.commit()
    conn.close()

def main():
    print("Starting Project OverWatch")
    collector = URLCollector()
    scraper = URLScraper()
    
    print("Finding URLs...")
    urls = collector.get_serp_results("us president", 10)
    print(f"Found {len(urls)} URLs")
    
    print("\nScraping URLs:")
    scraped_data = {}
    for url in urls:
        print(f"- {url}")  # Print each URL being scraped
        content = scraper.scrape_url_content(url)
        scraped_data[url] = content
    
    db_path = 'data/scraped_data.db'
    os.makedirs('data', exist_ok=True)
    create_db(db_path)
    save_to_db(db_path, scraped_data)
    print(f"\nDatabase saved to: {db_path}")

if __name__ == "__main__":
    main() 