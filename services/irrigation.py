import os
import time
import joblib
import pandas as pd
import httpx
from collections import deque
from datetime import datetime, timedelta, timezone

# Configuration
MODEL_PATH = os.getenv("MODEL_PATH", "agri_model_lgbm.joblib")
OWM_API_KEY = os.getenv("OWM_API_KEY", "YOUR_OPENWEATHERMAP_API_KEY")
OWM_FORECAST_URL = os.getenv("OWM_FORECAST_URL", "https://api.openweathermap.org/data/2.5/forecast")
OWM_CURRENT_URL = os.getenv("OWM_CURRENT_URL", "https://api.openweathermap.org/data/2.5/weather")
YIELD_GAIN_THRESHOLD = float(os.getenv("YIELD_GAIN_THRESHOLD", "0.25"))
RAIN_UPCOMING_SKIP_MM = float(os.getenv("RAIN_UPCOMING_SKIP_MM", "15.0"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "40"))
API_CALL_TIMESTAMPS: deque[datetime] = deque()

# Load model
print(f"Loading model from {MODEL_PATH}...")
model = joblib.load(MODEL_PATH)
print("Model ready.")


def _owm_condition_to_label(description: str) -> str:
    desc = description.lower()
    if any(w in desc for w in ["rain", "drizzle", "shower", "thunder"]):
        return "Rainy"
    if any(w in desc for w in ["cloud", "overcast", "haze", "mist", "fog"]):
        return "Cloudy"
    return "Sunny"


def _enforce_rate_limit() -> None:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=1)
    while API_CALL_TIMESTAMPS and API_CALL_TIMESTAMPS[0] < cutoff:
        API_CALL_TIMESTAMPS.popleft()
    if len(API_CALL_TIMESTAMPS) >= RATE_LIMIT_PER_MINUTE:
        raise ValueError("Weather API rate limit exceeded. Try again in a moment.")
    API_CALL_TIMESTAMPS.append(now)


def _fetch_json(url: str, params: dict) -> dict:
    last_error = None
    for attempt in range(1, 4):
        try:
            response = httpx.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            last_error = exc
            if response.status_code == 429 and attempt < 3:
                time.sleep(2 ** attempt)
            else:
                break
        except httpx.RequestError as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(2 ** attempt)
    raise ValueError(f"Could not fetch weather data: {last_error}")


def fetch_weekly_weather(lat: float, lon: float) -> dict:
    if not OWM_API_KEY or "YOUR_OPENWEATHERMAP_API_KEY" in OWM_API_KEY:
        raise ValueError("OpenWeatherMap API key is not configured.")

    _enforce_rate_limit()
    params = {"lat": lat, "lon": lon, "appid": OWM_API_KEY, "units": "metric"}

    current = _fetch_json(OWM_CURRENT_URL, params)
    forecast = _fetch_json(OWM_FORECAST_URL, params)

    current_temp = current["main"]["temp"]
    current_rain = current.get("rain", {}).get("1h", 0.0)
    current_cond = _owm_condition_to_label(current["weather"][0]["description"])

    now_utc = datetime.now(timezone.utc)
    cutoff_48h = now_utc + timedelta(hours=48)

    temps = [current_temp]
    rains = [current_rain]
    conditions = [current_cond]
    upcoming_rain_48h = current_rain
    days: dict[str, dict] = {}

    for entry in forecast["list"]:
        dt = datetime.fromtimestamp(entry["dt"], tz=timezone.utc)
        temp = entry["main"]["temp"]
        rain = entry.get("rain", {}).get("3h", 0.0)
        cond = _owm_condition_to_label(entry["weather"][0]["description"])
        day_key = dt.strftime("%Y-%m-%d")

        temps.append(temp)
        rains.append(rain)
        conditions.append(cond)

        if dt <= cutoff_48h:
            upcoming_rain_48h += rain

        if day_key not in days:
            days[day_key] = {"date": day_key, "temps": [], "rain_mm": 0.0, "conditions": []}
        days[day_key]["temps"].append(temp)
        days[day_key]["rain_mm"] += rain
        days[day_key]["conditions"].append(cond)

    days_summary = []
    for d in days.values():
        avg_t = sum(d["temps"]) / len(d["temps"])
        dominant = max(set(d["conditions"]), key=d["conditions"].count)
        days_summary.append({
            "date": d["date"],
            "avg_temp_c": round(avg_t, 1),
            "rain_mm": round(d["rain_mm"], 1),
            "condition": dominant,
        })

    total_rain = sum(rains)
    avg_temp = sum(temps) / len(temps)
    dom_condition = max(set(conditions), key=conditions.count)

    return {
        "total_rain_mm": round(total_rain, 1),
        "upcoming_rain_48h_mm": round(upcoming_rain_48h, 1),
        "avg_temp_c": round(avg_temp, 1),
        "dominant_condition": dom_condition,
        "days_summary": days_summary,
    }


def predict_yield(region, soil_type, crop_type, rainfall_mm, avg_temp,
                  fertilizer, irrigate, weather_condition, days_to_harvest) -> float:
    row = pd.DataFrame({
        "Region": [region],
        "Soil_Type": [soil_type],
        "Crop_Type": [crop_type],
        "Rainfall_mm_Season": [rainfall_mm],
        "Avg_Temp_C_Season": [avg_temp],
        "Fertilizer_Used": [fertilizer],
        "Irrigation_Used": [irrigate],
        "Weather_Condition": [weather_condition],
        "Days_to_Harvest": [days_to_harvest],
    })
    return float(model.predict(row)[0])


def build_recommendation(weather: dict, yield_with: float,
                          yield_without: float, upcoming_rain: float) -> dict:
    gain = yield_with - yield_without

    if upcoming_rain >= RAIN_UPCOMING_SKIP_MM:
        return {
            "should_irrigate": False,
            "confidence": "high",
            "reason": f"No irrigation needed — {upcoming_rain:.0f} mm of rain is forecast in the next 48 hours.",
            "yield_gain_tph": round(gain, 2),
        }

    if gain >= YIELD_GAIN_THRESHOLD:
        confidence = "high" if gain >= 0.6 else "medium"
        return {
            "should_irrigate": True,
            "confidence": confidence,
            "reason": f"Irrigate now — gain of {gain:.2f} t/ha.",
            "yield_gain_tph": round(gain, 2),
        }

    if gain > 0 and weather["dominant_condition"] == "Sunny":
        return {
            "should_irrigate": True,
            "confidence": "low",
            "reason": f"Consider irrigating — sunny with {weather['total_rain_mm']} mm rain.",
            "yield_gain_tph": round(gain, 2),
        }

    return {
        "should_irrigate": False,
        "confidence": "medium",
        "reason": f"No irrigation needed — conditions sufficient.",
        "yield_gain_tph": round(gain, 2),
    }


def get_irrigation_advice(lat: float, lon: float, crop_type: str, soil_type: str,
                          region: str = "North", fertilizer: bool = True, days_to_harvest: int = 90):
    try:
        weather = fetch_weekly_weather(lat, lon)
    except Exception as e:
        raise ValueError(f"Could not fetch weather: {e}")

    common = dict(
        region=region, soil_type=soil_type, crop_type=crop_type,
        rainfall_mm=weather["total_rain_mm"],
        avg_temp=weather["avg_temp_c"],
        fertilizer=fertilizer,
        weather_condition=weather["dominant_condition"],
        days_to_harvest=days_to_harvest,
    )
    yield_with = predict_yield(**common, irrigate=True)
    yield_without = predict_yield(**common, irrigate=False)

    rec = build_recommendation(weather, yield_with, yield_without, weather["upcoming_rain_48h_mm"])

    return {
        "should_irrigate": rec["should_irrigate"],
        "confidence": rec["confidence"],
        "reason": rec["reason"],
        "yield_with": round(yield_with, 2),
        "yield_without": round(yield_without, 2),
        "yield_gain": rec["yield_gain_tph"],
        "weather": weather,
    }