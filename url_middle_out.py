import os

import sqlite3
import time
from agents.url_collector import URLCollector
from agents.url_scraper import URLScraper
from agents.openrouter_agent import OpenRouterAgent
from agents.intent_filter_agent import IntentFilterAgent
from agents.report_generator_agent import ReportGeneratorAgent
from agents.content_strategy_agent import ContentStrategyAgent
import json
import re
import concurrent.futures
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime

def create_db(db_path: str):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Drop existing tables if they exist
    c.execute("DROP TABLE IF EXISTS queries")
    c.execute("DROP TABLE IF EXISTS summaries")
    
    # Create fresh tables with content_strategy in queries table
    c.execute('''CREATE TABLE queries
                 (id INTEGER PRIMARY KEY,
                  query TEXT,
                  content_strategy TEXT,
                  run_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE summaries
                 (id INTEGER PRIMARY KEY,
                  url TEXT,
                  summary TEXT,
                  collected_at DATETIME,
                  source TEXT)''')
    conn.commit()
    conn.close()

def save_to_db(db_path: str, data: dict):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO summaries 
                 (url, summary) VALUES (?, ?)''', 
             (data['url'], data['summary']))
    conn.commit()
    conn.close()

def middle_out_summary(agent: OpenRouterAgent, content: str, strategy: str) -> str:
    if not content:
        return "No content available for summary"
    
    prompt = f"""Extract key points from this content that answer these verification questions:

{strategy}

Content to analyze:
{content}

Rules:
1. Only extract information that answers the verification questions
2. Keep each point concise (1 sentence max)
3. Focus on factual information only
4. Format as bullet points"""
    
    try:
        return agent.summarize(prompt.format(content=content[:5000]))
    except Exception as e:
        return f"AI processing error: {str(e)}"

def verify_ai_connection(agent: OpenRouterAgent):
    print("\n[AI] Verifying OpenRouter connection...")
    try:
        # Use standard prompt format the API expects
        test_content = "Test connection - please respond with 'OK'"
        response = agent.summarize(test_content)
        if response.strip():  # Check for any valid response
            print("[AI] Connection verified successfully")
            return True
        raise ConnectionError("Empty response from API")
    except Exception as e:
        print(f"[AI] CRITICAL ERROR: Check API key and network - {str(e)}")
        return False

def sanitize_filename(name: str) -> str:
    """Convert query to safe filename"""
    return re.sub(r'[^a-zA-Z0-9_]', '_', name).strip('_')[:50]

def process_url_with_agent(url: str, content: Dict, agent: OpenRouterAgent, db_path: str, url_entry: Dict) -> None:
    if content['content']:
        # Extract key points instead of full summary
        key_points = middle_out_summary(agent, content['content'], url_entry['strategy'])
        save_to_db(db_path, {
            'url': url,
            'summary': key_points,
            'collected_at': url_entry['collected_at'],
            'source': url_entry['source']
        })
    else:
        save_to_db(db_path, {
            'url': url,
            'summary': "No content available",
            'collected_at': url_entry['collected_at'],
            'source': url_entry['source']
        })

def print_progress(current: int, total: int):
    progress = int((current / total) * 50)
    print(f"\rProcessing content with AI: [{'=' * progress}{' ' * (50 - progress)}] {current}/{total}", end="")

def process_url_content(url, content, agent, strategy):
    if not content:
        return url, "No content available"
    try:
        key_points = middle_out_summary(agent, content, strategy)
        return url, key_points if key_points else "No relevant information found"
    except Exception as e:
        return url, f"Error processing content: {str(e)}"

def process_query(user_query: str, agent: OpenRouterAgent, db_path: str):
    # Get data directory from db_path
    data_dir = os.path.dirname(db_path)
    
    # Create content strategy first and store it
    print("\nCreating content strategy...")
    content_agent = ContentStrategyAgent(agent.api_key, agent.model)
    strategy = content_agent.create_content_strategy(user_query)
    
    # Continue with URL collection
    print(f"\nFinding URLs for: {user_query}")
    collector = URLCollector()
    urls = [item['url'] for item in collector.get_serp_results(user_query)]
    
    # Generate sanitized filename component
    file_tag = sanitize_filename(user_query)
    report_path = os.path.join(data_dir, f'{file_tag}_final_summary.txt')
    
    # Define database path
    db_path = os.path.join(data_dir, f'{file_tag}_data.db')
    create_db(db_path)

    print("\nScraping and processing URLs...")
    scraper = URLScraper()
    total_urls = len(urls)
    successful_urls = []
    processed_count = 0
    scraping_count = 0

    # Create connection for DB writes
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Insert query AND strategy BEFORE processing
    c.execute('''INSERT INTO queries (query, content_strategy, run_at) 
        VALUES (?, ?, ?)''', (user_query, strategy, datetime.datetime.now().isoformat()))
    conn.commit()

    # Create two thread pools - one for scraping and one for processing
    with ThreadPoolExecutor(max_workers=5) as scrape_executor, \
         ThreadPoolExecutor(max_workers=5) as process_executor:
        
        # Track all futures
        scraping_futures = {}
        processing_futures = {}
        
        # Submit all URLs for scraping
        for url in urls:
            future = scrape_executor.submit(scraper.scrape_url_content, url)
            scraping_futures[future] = url
        
        print("\nScraping and Processing URLs...")
        print("Progress:")
        
        # Process scraping results as they complete
        for future in as_completed(scraping_futures):
            try:
                url = scraping_futures[future]
                content = future.result()
                scraping_count += 1
                
                if content and content['content']:
                    successful_urls.append(url)
                    # Immediately submit for AI processing
                    process_future = process_executor.submit(
                        process_url_content, 
                        url, 
                        content['content'], 
                        agent, 
                        strategy
                    )
                    processing_futures[process_future] = url
                
                # Update both progress bars on same line
                print(f"\rScraping: [{('=' * scraping_count) + (' ' * (total_urls - scraping_count))}] {scraping_count}/{total_urls} "
                      f"| Processing: [{('=' * processed_count) + (' ' * (len(successful_urls) - processed_count))}] {processed_count}/{len(successful_urls)}", 
                      end='', flush=True)
                
            except Exception as e:
                print(f"\nError scraping {url}: {str(e)}")
                continue

            # Check for completed processing tasks
            for process_future in list(processing_futures.keys()):
                if process_future.done():
                    try:
                        url = processing_futures[process_future]
                        url, key_points = process_future.result()
                        
                        if key_points:
                            c.execute('''INSERT INTO summaries
                                (url, summary, collected_at, source)
                                VALUES (?, ?, ?, ?)''',
                                (url, key_points, datetime.datetime.now().isoformat(), 'web')
                            )
                            conn.commit()
                        
                        processed_count += 1
                        del processing_futures[process_future]
                        
                        # Update both progress bars
                        print(f"\rScraping: [{('=' * scraping_count) + (' ' * (total_urls - scraping_count))}] {scraping_count}/{total_urls} "
                              f"| Processing: [{('=' * processed_count) + (' ' * (len(successful_urls) - processed_count))}] {processed_count}/{len(successful_urls)}", 
                              end='', flush=True)
                        
                    except Exception as e:
                        print(f"\nError processing {url}: {str(e)}")
                        continue

        # Wait for any remaining processing tasks
        for future in as_completed(processing_futures):
            try:
                url = processing_futures[future]
                url, key_points = future.result()
                
                if key_points:
                    c.execute('''INSERT INTO summaries
                        (url, summary, collected_at, source)
                        VALUES (?, ?, ?, ?)''',
                        (url, key_points, datetime.datetime.now().isoformat(), 'web')
                    )
                    conn.commit()
                
                processed_count += 1
                # Final progress update
                print(f"\rScraping: [{('=' * total_urls)}] {total_urls}/{total_urls} "
                      f"| Processing: [{('=' * processed_count) + (' ' * (len(successful_urls) - processed_count))}] {processed_count}/{len(successful_urls)}", 
                      end='', flush=True)
                
            except Exception as e:
                print(f"\nError processing {url}: {str(e)}")
                continue

    conn.close()
    print("\nProcessing complete")

def main():
    print("Starting Project OverWatch")
    
    # Clear existing data
    data_dir = 'data'
    if os.path.exists(data_dir):
        for file in os.listdir(data_dir):
            file_path = os.path.join(data_dir, file)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                    print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    else:
        os.makedirs(data_dir)
    
    print("\nAll previous data cleared. Starting fresh analysis...")
    
    # Prompt user for keyword query
    user_query = input("Enter your search query: ").strip()
    if not user_query:
        print("Error: No query entered")
        return
    
    # Initialize agents
    with open('config.json') as config_file:
        config = json.load(config_file)
    
    # Create OpenRouter agent for summarization
    openrouter_agent = OpenRouterAgent(
            config['openrouter']['api_key'],
            config['openrouter']['model']
    )
    
    # Determine domain expert without extra printing
    intent_filter = IntentFilterAgent(
        config['openrouter']['api_key'],
        config['openrouter']['model']
    )
    domain_expert = intent_filter.determine_domain(user_query)
    print(f"\nDomain Expert: {domain_expert.strip()}")  # Strip any extra newlines
    
    # Process query with OpenRouter agent
    process_query(user_query, openrouter_agent, os.path.join(data_dir, f'{sanitize_filename(user_query)}_data.db'))

if __name__ == "__main__":
    main() 