import os
import joblib
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone

# Configuration
MODEL_PATH = "agri_model_lgbm.joblib"
OWM_API_KEY = os.getenv("OWM_API_KEY", "YOUR_OPENWEATHERMAP_API_KEY")
OWM_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
OWM_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
YIELD_GAIN_THRESHOLD = 0.25
RAIN_UPCOMING_SKIP_MM = 15.0

# Load model
print(f"Loading model from {MODEL_PATH}...")
model = joblib.load(MODEL_PATH)
print("Model ready.")

def _owm_condition_to_label(description: str) -> str:
    """Map OpenWeatherMap description → model's Weather_Condition categories."""
    desc = description.lower()
    if any(w in desc for w in ["rain", "drizzle", "shower", "thunder"]):
        return "Rainy"
    if any(w in desc for w in ["cloud", "overcast", "haze", "mist", "fog"]):
        return "Cloudy"
    return "Sunny"

def fetch_weekly_weather(lat: float, lon: float) -> dict:
    """
    Fetch weather data for approximately the current week.
    """
    params = {"lat": lat, "lon": lon, "appid": OWM_API_KEY, "units": "metric"}

    # Current weather
    cur_resp = requests.get(OWM_CURRENT_URL, params=params, timeout=10)
    cur_resp.raise_for_status()
    current = cur_resp.json()

    current_temp = current["main"]["temp"]
    current_rain = current.get("rain", {}).get("1h", 0.0)
    current_cond = _owm_condition_to_label(current["weather"][0]["description"])

    # Forecast
    fcast_resp = requests.get(OWM_FORECAST_URL, params=params, timeout=10)
    fcast_resp.raise_for_status()
    forecast = fcast_resp.json()

    now_utc = datetime.now(timezone.utc)
    cutoff_48h = now_utc + timedelta(hours=48)

    temps, rains, conditions = [current_temp], [current_rain], [current_cond]
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

    # Summarise daily
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
    """Run the LightGBM model and return predicted yield (tonnes/ha)."""
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
    """
    Combine model output and weather context into a recommendation.
    """
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
    """
    Get irrigation advice.
    """
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