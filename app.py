import os
from flask import Flask, request, jsonify, Response, stream_with_context
import openai
from dotenv import load_dotenv
from modules.question_parser import parse_and_tag

# Load environment variables
load_dotenv()

# Configure OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')
print(f"OpenAI API key set: {'*' * (len(os.getenv('OPENAI_API_KEY', '')) - 8) + os.getenv('OPENAI_API_KEY', '')[-4:] if os.getenv('OPENAI_API_KEY') else 'Not found'}")

# Initialize Flask app
app = Flask(__name__, static_folder='static')

# Add CORS headers manually
@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/query', methods=['POST'])
def query():
    # Get the question from the request
    data = request.json
    question = data.get('question', '')
    
    print(f"Received question: {question}")
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    # Parse and tag the question
    try:
        tagged_question = parse_and_tag(question)
        print(f"Tagged question: {tagged_question}")
    except Exception as e:
        print(f"Error parsing question: {str(e)}")
        return jsonify({'error': f'Error parsing question: {str(e)}'}), 500
    
    # Set up the system message for HoT prompting
    system_message = (
        "You are an expert reasoner using Highlighted Chain-of-Thought (HoT). "
        "You will be given a question with certain parts marked as <fact1>, <fact2>, ... "
        "Your job is to produce a step-by-step answer, using the same <fact> tags in your "
        "answer to refer to those facts. Make sure each <factN> in your answer corresponds "
        "to the same content tagged in the question. Explain the reasoning clearly and "
        "arrive at a solution."
    )
    
    # Example to demonstrate the format
    examples = (
        "Example question: <fact1>42</fact1> is the answer to life, the universe, and everything. "
        "What is half of that number?\n"
        "Example answer: Half of <fact1>42</fact1> is 21."
    )
    
    # Define the function to stream the response
    def generate():
        try:
            # Call OpenAI API with streaming enabled
            print("Calling OpenAI API...")
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": examples},
                    {"role": "user", "content": tagged_question}
                ],
                stream=True,
                temperature=0.2,
                max_tokens=1000
            )
            
            print("Stream started...")
            # Stream the response
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(f"Yielding content: {content[:30]}...")
                    yield f"data: {content}\n\n"
            
            print("Stream complete")
            yield "data: [DONE]\n\n"
        except Exception as e:
            print(f"Error in generate: {str(e)}")
            yield f"data: Error: {str(e)}\n\n"
    
    # Return the response as a stream
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
