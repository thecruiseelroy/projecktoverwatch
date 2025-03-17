import sqlite3

from agents.openrouter_agent import OpenRouterAgent
from agents.report_generator_agent import ReportGeneratorAgent
import json
import os
import time
from datetime import datetime
import re

def generate_final_report(db_path: str, agent: OpenRouterAgent) -> str:
    print("\n=== REPORT GENERATOR READING DATABASE ===")
    
    current_time = datetime.now()  # Get current time when report is generated
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Get query and strategy from queries table
    c.execute("SELECT query, content_strategy FROM queries ORDER BY run_at DESC LIMIT 1")
    result = c.fetchone()
    if not result:
        print("Error: No query found in database")
        conn.close()
        return "Error: Database empty"
    
    query, strategy = result
    
    # Get summaries with error handling
    c.execute("SELECT url, summary, collected_at, source FROM summaries")
    summaries = c.fetchall()
    if not summaries:
        print("Error: No summaries found in database")
        conn.close()
        return "Error: No content found"
    
    structured_data = [{
        'source_id': idx + 1,
        'url': row[0],
        'content': row[1],
        'collected_at': row[2],
        'source': row[3]
    } for idx, row in enumerate(summaries)]
    
    report_agent = ReportGeneratorAgent(agent.api_key, agent.model)
    report = report_agent.generate_report(structured_data, query, strategy, current_time)
    
    conn.close()
    print("=== DATABASE READ COMPLETE ===")
    
    return report if report else "Error: Failed to generate report"

def sanitize_filename(name: str) -> str:
    """Convert query to safe filename"""
    return re.sub(r'[^a-zA-Z0-9_]', '_', name).strip('_')[:50]

def verify_database_schema(conn):
    c = conn.cursor()
    
    # Check queries table structure
    c.execute("PRAGMA table_info(queries)")
    queries_columns = {row[1] for row in c.fetchall()}
    required_queries_columns = {'query', 'run_at'}
    if not required_queries_columns.issubset(queries_columns):
        return False
        
    # Check summaries table structure
    c.execute("PRAGMA table_info(summaries)")
    summaries_columns = {row[1] for row in c.fetchall()}
    required_summaries_columns = {'url', 'summary', 'collected_at', 'source'}
    if not required_summaries_columns.issubset(summaries_columns):
        return False
        
    return True

def main():
    try:
        data_dir = 'data'
        
        # Find the most recent database file
        db_files = [f for f in os.listdir(data_dir) if f.endswith('_data.db')]
        if not db_files:
            print("Error: No database found. Run url_middle_out.py first")
            return
        
        # Use the most recent database
        db_path = os.path.join(data_dir, db_files[-1])
        
        # Verify database exists
        if not os.path.exists(db_path):
            print("Error: Database file not found")
            return
        
        # Verify database is not empty
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Check queries table
        c.execute("SELECT COUNT(*) FROM queries")
        if c.fetchone()[0] == 0:
            print("Error: No queries found in database")
            conn.close()
            return
        
        # Check summaries table
        c.execute("SELECT COUNT(*) FROM summaries")
        if c.fetchone()[0] == 0:
            print("Error: No summaries found in database")
            conn.close()
            return
        
        conn.close()
        
        # Get original query from database
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT query FROM queries ORDER BY run_at DESC LIMIT 1")
        original_query = c.fetchone()[0] or "unknown_query"
        conn.close()
        
        # Generate sanitized filename component
        file_tag = sanitize_filename(original_query)
        report_path = os.path.join(data_dir, f'{file_tag}_final_summary.txt')
        
        with open('config.json') as f:
            config = json.load(f)
        
        agent = OpenRouterAgent(
            config['openrouter']['api_key'],
            config['openrouter']['model']
        )
        
        # Generate and save report
        report = generate_final_report(db_path, agent)
        
        # Save report to file
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\nReport saved to: {report_path}")

    except Exception as e:
        print(f"\nError in main: {str(e)}")

if __name__ == "__main__":
    main() 