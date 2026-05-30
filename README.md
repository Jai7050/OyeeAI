# OyeAI Ultra Fixed

A futuristic desktop assistant with:
- AI chat using OpenRouter
- Voice input
- Voice output in browser
- Weather by city or current location
- Time, date, and day commands
- App opening on Windows: notepad, calculator, command prompt, paint, explorer
- Website opening: YouTube, Google, GitHub, ChatGPT

## Setup

1. Extract the zip
2. Open the folder in VS Code
3. Create a `.env` file in the project root
4. Copy the contents of `.env.example` into `.env`
5. Paste your new OpenRouter API key into `.env`

Example:
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxx

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Open:
http://127.0.0.1:5000

## Commands

- time
- date
- day
- weather in Mumbai
- weather  (after allowing location)
- open youtube
- open google
- open github
- open chatgpt
- open notepad
- open calculator
- open cmd
- open paint
- open explorer

## Important

If you exposed your old OpenRouter key publicly, revoke it and create a new one.
This project uses openrouter/free, which routes to currently available free models automatically.
