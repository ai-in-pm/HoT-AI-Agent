# Highlighted Chain-of-Thought (HoT) AI Agent

This is an implementation of an AI agent that utilizes the Highlighted Chain-of-Thought (HoT) reasoning framework. The agent helps users by providing transparent, PhD-level reasoning with highlighted references to facts from the original question.

The development of this repository was inspired by the paper "HoT: Highlighted Chain of Thought for Referencing Supporting Facts from Inputs".

To read the entire paper, visit https://arxiv.org/pdf/2503.02003.

## Features

- Question parsing and fact tagging
- Real-time streaming of responses with typing simulation
- Visual highlighting of facts in both questions and answers
- Transparent reasoning process that links answers to question facts
- Example question dropdown for quick demonstrations
- Dark/Light mode toggle for user preference
- SQLite database for storing question and answer history
- Enhanced UI with responsive design for better user experience
- Interactive web interface

## Setup

### Prerequisites

- Python 3.8 or higher
- OpenAI API key

### Installation

1. Ensure you are in the virtual environment:
   ```
   venv\Scripts\activate
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Configure your `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### Running the Application

1. Start the Flask server:
   ```
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

## Getting Started

### Prerequisites

- Python 3.6 or higher
- OpenAI API key (set in .env file)

### Installation

1. Clone this repository
2. Set up your OpenAI API key in a `.env` file:

```
OPENAI_API_KEY=your_api_key_here
```

3. Run the standalone server:

```bash
python hot_server.py
```

4. Open your browser and navigate to http://localhost:8000

## Usage

1. Choose one of the example questions from the dropdown, or enter your own question
2. Click "Submit Question" to generate a response
3. The agent will identify key facts in your question and highlight them
4. The answer will be streamed in real-time with references to the facts from your question
5. Hover over highlighted facts to see connections between the question and answer

## How It Works

1. When you submit a question, the backend parser identifies key facts in your question and tags them with XML-style tags (e.g., `<fact1>...</fact1>`)
2. These tagged facts are sent to GPT-4 along with specialized prompts that instruct it to use the same tags in its answer
3. The response is streamed back to the frontend, creating a typing effect
4. Facts in both the question and answer appear highlighted, making it easy to trace the reasoning

The HoT-AI Agent uses the following process:

1. **Fact Extraction**: When a question is submitted, the agent identifies key facts in the question.
2. **Fact Tagging**: Facts are tagged with unique identifiers (fact1, fact2, etc.)
3. **Answer Generation**: Using GPT-4, the agent generates a PhD-level answer that explicitly references the facts.
4. **Visual Highlighting**: Both the question and answer display highlighted facts, with interactive elements to show connections.

## Example Questions

Try these questions to see the agent in action:

- "If Earth is 149.6 million km from the Sun and light travels at 299,792 km/s, how long does it take for sunlight to reach Earth?"
- "A farmer has 15 cows and 27 chickens. If each cow produces 28 liters of milk per week and each chicken lays 5 eggs per week, what's the total weekly production?"
- "The boiling point of water is 100°C at sea level but decreases by about 1°C for every 285m increase in altitude. What is the approximate boiling point at Denver, which is 1609m above sea level?"
- Math problems with multiple variables and operations
- Logic puzzles requiring multi-step deductions
- Scientific questions needing methodical explanation
- Complex scenarios requiring analysis of multiple facts

## Architecture

The application follows a modular architecture:

- **Backend (Flask)**: Handles question parsing, fact tagging, and API calls to OpenAI
- **Frontend (HTML/CSS/JS)**: Provides the user interface, handles real-time updates, and displays highlighted facts

## Technical Details

- Frontend: HTML, CSS, JavaScript
- Backend: Python with standalone HTTP server
- Database: SQLite for persistent storage
- Response format: Server-Sent Events (SSE) for streaming responses

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## References

- [Highlighted Chain-of-Thought Paper](https://arxiv.org/abs/2305.08322)
- [Project Website](https://highlightedchainofthought.github.io/)
