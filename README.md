# SelfGPT

A ChatGPT clone built with Python and Flask, now supporting both OpenAI and Anthropic Claude models.

![SelfGPT Screenshot](selfgpt2.png)

## Quick Start

1. Clone and enter directory:
   ```
   git clone https://github.com/plotJ/SelfGPT.git
   cd SelfGPT
   ```

2. Set up virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure:
   - Set `OPENAI_API_KEY` and `CLAUDE_API_KEY` in environment or `config.json`
   - Optional: Set `OPENAI_API_BASE` for custom OpenAI API endpoint

5. Run:
   ```
   python run.py
   ```

## Docker

Run with:
```
docker-compose up
```

## Features

- ChatGPT-like interface
- Support for OpenAI and Anthropic Claude models
- Theme changer
- User preference memory
- Conversation deletion with confirmation

## To Do

- Conversation import/export
- Speech input/output
- File loading
- Performance optimizations

## Future Enhancements

1. User authentication and conversation storage:
   - Implement login functionality
   - Store conversations linked to user accounts instead of using cookies

2. Additional AI models:
   - Integrate Google's Gemini model

3. User-provided API keys:
   - Allow users to input their own API keys during signup
   - Securely store and manage user-specific API keys

4. Image generation:
   - Implement AI-powered image generation capabilities

---