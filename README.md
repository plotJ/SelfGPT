# SelfGPT

ChatGPT clone built with Python and Flask.

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
   - Set `OPENAI_API_KEY` in environment or `config.json`
   - Optional: Set `OPENAI_API_BASE` for custom API endpoint

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
- Theme changer
- User preference memory
- Conversation deletion with confirmation

## To Do

- Conversation import/export
- Speech input/output
- File loading
- Performance optimizations

