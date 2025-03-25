import re
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

def extract_key_facts(question_text):
    """
    Extract key facts from the question text using a combination of
    NLP techniques and GPT-4 assistance.
    """
    # Use GPT-4 to identify key facts in the question
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Identify key pieces of factual information in the following question. "
                        "Key facts typically include numbers, proper nouns, dates, measurements, "
                        "or any specific information that will likely be cited in an answer. "
                        "Return only a JSON array of strings, each string containing one fact. "
                        "Keep the facts concise and identify only the most relevant information."
                    )
                },
                {"role": "user", "content": question_text}
            ],
            temperature=0.1,
            max_tokens=300
        )
        
        # Extract facts from the response
        facts_text = response.choices[0].message.content
        
        # Try to parse as JSON array
        try:
            import json
            facts = json.loads(facts_text)
            if not isinstance(facts, list):
                facts = [facts_text]  # Fallback if not a list
        except json.JSONDecodeError:
            # Fallback to regex if not valid JSON
            facts = re.findall(r'"([^"]+)"', facts_text)
            if not facts:  # If regex also fails
                facts = [line.strip() for line in facts_text.split('\n') if line.strip()]
        
        return facts
        
    except Exception as e:
        print(f"Error extracting facts: {str(e)}")
        # Fallback to simple NLP approach
        # Extract capitalized terms, numbers, and quoted phrases
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', question_text)
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', question_text)
        quotes = re.findall(r'"([^"]+)"', question_text)
        
        # Combine all extracted facts
        facts = capitalized + numbers + quotes
        # Remove duplicates and sort by position in text
        unique_facts = []
        for fact in facts:
            if fact not in unique_facts and len(fact) > 1:  # Avoid single characters
                unique_facts.append(fact)
        
        return unique_facts

def parse_and_tag(question_text):
    """
    Parse the question and tag key facts with XML tags.
    """
    # Extract key facts
    facts = extract_key_facts(question_text)
    
    # Insert XML tags around each fact
    tagged_text = question_text
    
    # Sort facts by length (descending) to avoid tagging substrings of longer facts
    facts.sort(key=len, reverse=True)
    
    # Tag each fact in the text
    for i, fact in enumerate(facts, start=1):
        # Escape special characters for regex
        escaped_fact = re.escape(fact)
        # Create a pattern that matches the whole fact
        pattern = r'\b' + escaped_fact + r'\b'
        # Replace with tagged version
        tag_open = f"<fact{i}>"
        tag_close = f"</fact{i}>"
        # Replace only the first occurrence to avoid overlapping tags
        tagged_text = re.sub(pattern, f"{tag_open}{fact}{tag_close}", tagged_text, count=1)
    
    return tagged_text

# Example usage for testing
if __name__ == "__main__":
    test_question = "Jenna starts out with 8 sapphires. She trades 3 sapphires for two rubies. If sapphires are worth $800 and rubies $1200, how much are all her jewels worth?"
    tagged = parse_and_tag(test_question)
    print(tagged)
