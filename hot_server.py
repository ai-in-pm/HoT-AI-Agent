import os
import sys
import json
import http.server
import socketserver
import urllib.parse
import sqlite3
import re
import time
from datetime import datetime
from http import HTTPStatus

# Configuration
PORT = 8000
API_KEY = os.getenv('OPENAI_API_KEY')
DATABASE_PATH = './hot_history.db'

# Ensure we have API key
if not API_KEY:
    # Try to load from .env file
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    API_KEY = line.strip().split('=', 1)[1].strip('"\'')
                    break
    except Exception as e:
        print(f"Failed to load API key from .env file: {e}")
        
if not API_KEY:
    print("ERROR: No OpenAI API key found. Please set OPENAI_API_KEY environment variable or add it to .env file.")
    sys.exit(1)
else:
    print(f"OpenAI API key set: {'*' * (len(API_KEY) - 4) + API_KEY[-4:]}")

# Initialize database
def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        tagged_question TEXT,
        answer TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()
    print(f"Database initialized at {DATABASE_PATH}")

# Sample fact extraction function
def extract_key_facts(text):
    # This is a simplified version that extracts numerical values and key phrases
    facts = []
    
    # Extract numbers with their context
    number_pattern = r'\b\d+(?:\.\d+)?\s*(?:km|m|s|°C|liters|eggs|cows|chickens|million)?\b'
    for match in re.finditer(number_pattern, text):
        start = max(0, match.start() - 30)
        end = min(len(text), match.end() + 30)
        context = text[start:end].strip()
        facts.append(context)
    
    # Extract key phrases
    key_phrases = ['Earth', 'Sun', 'light travels', 'boiling point', 'water', 'sea level', 'Denver', 'farmer', 'produces', 'lays']
    for phrase in key_phrases:
        if phrase.lower() in text.lower():
            index = text.lower().find(phrase.lower())
            start = max(0, index - 20)
            end = min(len(text), index + len(phrase) + 20)
            context = text[start:end].strip()
            facts.append(context)
    
    # Remove duplicates while preserving order
    unique_facts = []
    for fact in facts:
        if fact not in unique_facts:
            unique_facts.append(fact)
    
    return unique_facts[:15]  # Limit to 15 facts

# Parse and tag facts function
def parse_and_tag(question_text):
    facts = extract_key_facts(question_text)
    tagged_text = question_text
    
    # Tag each fact in the question
    for i, fact in enumerate(facts, 1):
        if fact in tagged_text:
            tagged_text = tagged_text.replace(fact, f"<fact{i}>{fact}</fact{i}>")
    
    return tagged_text, facts

# Simulate OpenAI API for demo purposes
def simulate_openai_response(question, facts):
    # Create a simulated response that references the facts
    response_parts = []
    
    if "Earth" in question and "Sun" in question and "light" in question:
        response_parts = [
            "The ", "sum", " of", " <", "fact", "1", "><", "fact", "3", ">", "149.6 million km", "</", "fact", "3", "></", "fact", "1", ">", " and", " <", "fact", "2", ">", "299,792 km/s", "</", "fact", "2", ">", " allows us to calculate the time it takes for sunlight to reach Earth.\n\n",
            "To solve this problem, I'll use the equation: time = distance / speed\n\n",
            "time = <fact1><fact3>149.6 million km</fact3></fact1> / <fact2>299,792 km/s</fact2>\n\n",
            "First, I'll convert million to the standard form:\n149.6 million km = 149,600,000 km\n\n",
            "Now I can divide:\ntime = 149,600,000 km / 299,792 km/s\ntime ≈ 499.01 seconds\n\n",
            "Converting to minutes:\n499.01 seconds / 60 = 8.32 minutes\n\n",
            "Therefore, it takes approximately 8.32 minutes (or about 8 minutes and 19 seconds) for sunlight to reach Earth from the Sun."
        ]
    elif "farmer" in question and "cows" in question and "chickens" in question:
        response_parts = [
            "To determine the total weekly production on the farm, I need to calculate both the milk production from cows and egg production from chickens.\n\n",
            "First, let's calculate the milk production:\n<fact1>15 cows</fact1> × <fact2>28 liters per week</fact2> = 420 liters of milk per week\n\n",
            "Next, let's calculate the egg production:\n<fact3>27 chickens</fact3> × <fact4>5 eggs per week</fact4> = 135 eggs per week\n\n",
            "Therefore, the total weekly production on the farm is 420 liters of milk and 135 eggs."
        ]
    elif "boiling point" in question and "water" in question and "Denver" in question:
        response_parts = [
            "To find the boiling point of water in Denver, I'll use the relationship between altitude and boiling point.\n\n",
            "Given information:\n- <fact1>The boiling point of water is 100°C at sea level</fact1>\n- <fact2>The boiling point decreases by about 1°C for every 285m increase in altitude</fact2>\n- <fact3>Denver is 1609m above sea level</fact3>\n\n",
            "To calculate the decrease in boiling point, I'll divide Denver's altitude by the rate of decrease:\n<fact3>1609m</fact3> ÷ <fact4>285m per °C</fact4> ≈ 5.65°C\n\n",
            "Therefore, the boiling point at Denver would be:\n<fact1>100°C</fact1> - 5.65°C = 94.35°C\n\n",
            "The approximate boiling point of water in Denver is 94.35°C."
        ]
    else:
        response_parts = ["I don't have enough information to answer this question accurately."]
    
    return response_parts

# Custom HTTP Request Handler
class HoTRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(os.path.dirname(__file__), 'static'), **kwargs)
    
    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/query':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(post_data)
                question = data.get('question', '')
                
                if not question:
                    self.send_error(400, 'Missing question parameter')
                    return
                
                # Tag the question with facts
                tagged_question, facts = parse_and_tag(question)
                print(f"\nReceived question: {question}")
                print(f"Tagged question: {tagged_question}")
                
                # Store in database
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO queries (question, tagged_question) VALUES (?, ?)',
                    (question, tagged_question)
                )
                query_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                # Set response headers for streaming
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                # Simulate response chunks (in a real app, this would come from OpenAI)
                response_parts = simulate_openai_response(question, facts)
                
                full_response = ""
                for part in response_parts:
                    # Simulate API delay
                    time.sleep(0.2)
                    
                    # Send the chunk
                    self.wfile.write(f"data: {part}\n\n".encode('utf-8'))
                    self.wfile.flush()
                    
                    full_response += part
                
                # Update the database with the full response
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE queries SET answer = ? WHERE id = ?',
                    (full_response, query_id)
                )
                conn.commit()
                conn.close()
                
                # Signal the end of the stream
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
                
            except Exception as e:
                print(f"Error processing request: {e}")
                self.send_error(500, f'Internal Server Error: {str(e)}')
        else:
            # For all other POST requests, return 404
            self.send_error(404, 'Not Found')
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

# Main server function
def run_server():
    # Initialize the database
    init_db()
    
    # Start the server
    with socketserver.TCPServer(("", PORT), HoTRequestHandler) as httpd:
        print(f"\nServer running at http://localhost:{PORT}")
        print("To test the HoT AI Agent, open a web browser and navigate to the URL above")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped by user")

if __name__ == "__main__":
    run_server()
