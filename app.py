from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os
import re
import subprocess
import requests
from urllib.parse import quote_plus
from datetime import datetime
import json
import os

MEMORY_FILE = "memory.json"
load_dotenv()

app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()

client = None
if OPENROUTER_API_KEY:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key="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",
        default_headers={
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "OyeAI"
        }
    )

WEATHER_CODE_MAP = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "dense freezing drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "slight snow",
    73: "moderate snow",
    75: "heavy snow",
    77: "snow grains",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail"
}

def build_response(text, speak=True, action=None, extra=None):
    payload = {"response": text, "speak": speak}
    if action:
        payload["action"] = action
    if extra:
        payload.update(extra)
    return jsonify(payload)

def get_time_text():
    return datetime.now().strftime("%I:%M %p")

def get_date_text():
    return datetime.now().strftime("%d %B %Y")

def get_day_text():
    return datetime.now().strftime("%A")

def open_local_app(app_name: str):
    app_name = app_name.lower().strip()
    commands = {
        "notepad": ["notepad"],
        "calculator": ["calc"],
        "calc": ["calc"],
        "command prompt": ["cmd"],
        "cmd": ["cmd"],
        "paint": ["mspaint"],
        "explorer": ["explorer"],
    }
    if app_name not in commands:
        return False, "I can open notepad, calculator, command prompt, paint, and explorer."
    try:
        subprocess.Popen(commands[app_name], shell=True)
        nice = "command prompt" if app_name == "cmd" else app_name
        return True, f"Opening {nice}."
    except Exception as e:
        return False, f"Could not open {app_name}: {e}"

def get_weather_by_city(city: str):
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={quote_plus(city)}&count=1&language=en&format=json"
    geo = requests.get(geo_url, timeout=12)
    geo.raise_for_status()
    geo_data = geo.json()

    results = geo_data.get("results") or []
    if not results:
        return None, f"I could not find the city {city}."

    place = results[0]
    lat = place["latitude"]
    lon = place["longitude"]
    place_name = place["name"]
    country = place.get("country", "")

    return get_weather_by_coords(lat, lon, f"{place_name}, {country}".strip(", "))

def get_weather_by_coords(lat, lon, label="your location"):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m"
        "&timezone=auto"
    )

    try:
        res = requests.get(url, timeout=12)
        res.raise_for_status()
        data = res.json()
    except requests.exceptions.RequestException:
        return None, "Weather service is temporarily unavailable. Please try again in a moment."

    current = data.get("current", {})
    if not current:
        return None, "Weather data is unavailable right now."

    temp = current.get("temperature_2m")
    feels = current.get("apparent_temperature")
    wind = current.get("wind_speed_10m")
    code = current.get("weather_code", -1)
    desc = WEATHER_CODE_MAP.get(code, "unknown conditions")

    text = (
        f"Current weather in {label}: {temp}°C, feels like {feels}°C, "
        f"{desc}, wind speed {wind} km/h."
    )
    return data, text

def handle_builtin_command(user_input: str, lat=None, lon=None):
    msg = user_input.lower().strip()

    if re.search(r"\btime\b", msg):
        return build_response(f"The time is {get_time_text()}.")

    if re.search(r"\bdate\b", msg):
        return build_response(f"Today's date is {get_date_text()}.")

    if re.search(r"\bday\b", msg):
        return build_response(f"Today is {get_day_text()}.")

    if re.search(r"\bopen youtube\b", msg):
        return build_response("Opening YouTube.", action="open_url", extra={"url": "https://www.youtube.com"})

    if re.search(r"\bopen google\b", msg):
        return build_response("Opening Google.", action="open_url", extra={"url": "https://www.google.com"})

    if re.search(r"\bopen github\b", msg):
        return build_response("Opening GitHub.", action="open_url", extra={"url": "https://github.com"})

    if re.search(r"\bopen chatgpt\b", msg):
        return build_response("Opening ChatGPT.", action="open_url", extra={"url": "https://chatgpt.com"})

    m = re.search(r"\bopen\s+(notepad|calculator|calc|command prompt|cmd|paint|explorer)\b", msg)
    if m:
        ok, text = open_local_app(m.group(1))
        return build_response(text, speak=True)

    city_match = re.search(r"\bweather(?:\s+in)?\s+([a-zA-Z\s]+)$", msg)
    if city_match:
        city = city_match.group(1).strip()
        try:
            _, text = get_weather_by_city(city)
            return build_response(text)
        except Exception as e:
            return build_response(f"Could not fetch weather for {city}: {e}")

    if "weather" in msg:
        if lat is not None and lon is not None:
            try:
                _, text = get_weather_by_coords(lat, lon)
                return build_response(text)
            except Exception as e:
                return build_response(f"Weather for {city} is unavailable right now.")
        return build_response("Please say weather in a city name, for example weather in Mumbai, or allow location access.")

    return None

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)

def add_to_memory(role, content):
    memory = load_memory()
    memory.append({"role": role, "content": content})

    # sirf last 20 messages rakho
    memory = memory[-20:]

    save_memory(memory)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    user_input = str(data.get("message", "")).strip()
    add_to_memory("user", user_input)
    memory = load_memory()
    lat = data.get("lat")
    lon = data.get("lon")
    # ✅ CUSTOM GREETING (YAHI ADD KAR)
    if user_input in ["hi", "hello", "hey","Hi.","Hello.","Hey"]:
        return jsonify({
            "response": "Hi Jai 👋, I am your AI assistant. How can I help you today?",
            "speak": True
        })


    if not user_input:
        return build_response("Please type or say something.")

    builtin = handle_builtin_command(user_input, lat=lat, lon=lon)
    if builtin is not None:
        return builtin

    if client is None:
        return build_response(
            "OpenRouter API key is missing. Add OPENROUTER_API_KEY in your .env file to enable AI chat.",
            speak=False
        )

    try:
        completion = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": (
                    "You are OyeAI, a friendly desktop assistant. "
                    "Keep answers concise, clear, and helpful."
                )},
                {"role": "user", "content": user_input}
            ] + memory
        )
        reply = completion.choices[0].message.content.strip()
        add_to_memory("assistant", reply)
        if not reply:
            reply = "I did not get a proper response from the AI."
        return build_response(reply)
    except Exception as e:
        return build_response(f"AI error: {e}", speak=False)

if __name__ == "__main__":
    app.run(debug=True)
