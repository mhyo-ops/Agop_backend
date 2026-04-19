"""
Agri-Optimize — Irrigation Advisor API
======================================
Mobile backend that answers the farmer's daily question:
"Should I irrigate my crops today?"

It fetches this week's real weather data (past + forecast),
runs the LightGBM model under two scenarios (irrigate / don't irrigate),
and returns a clear, actionable recommendation.

Requirements:
    pip install flask joblib pandas requests lightgbm

Usage:
    1. Set your OpenWeatherMap API key below (free tier works).
    2. Run:  python app.py
    3. Call: GET /advice?lat=36.19&lon=5.41&crop=Potato&soil=Clay
                        &region=North&fertilizer=true&days_to_harvest=115
"""

import os
import joblib
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

MODEL_PATH          = "agri_model_lgbm.joblib"
OWM_API_KEY         = os.getenv("OWM_API_KEY", "YOUR_OPENWEATHERMAP_API_KEY")
OWM_FORECAST_URL    = "https://api.openweathermap.org/data/2.5/forecast"
OWM_CURRENT_URL     = "https://api.openweathermap.org/data/2.5/weather"
OWM_HISTORY_URL     = "https://api.openweathermap.org/data/2.5/onecall/timemachine"  # paid plan

# How much extra yield (tonnes/ha) from irrigation must the model predict
# before we recommend irrigating.  Keeps recommendation conservative.
YIELD_GAIN_THRESHOLD = 0.25

# If more than this much rain (mm) is forecast in the NEXT 48 h,
# irrigation may not be necessary.
RAIN_UPCOMING_SKIP_MM = 15.0

# ─────────────────────────────────────────────
# LOAD MODEL ONCE AT STARTUP
# ─────────────────────────────────────────────

print(f"Loading model from {MODEL_PATH}...")
model = joblib.load(MODEL_PATH)
print("Model ready.")

app = Flask(__name__)


# ─────────────────────────────────────────────
# WEATHER HELPERS
# ─────────────────────────────────────────────

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
    Fetch weather data for approximately the current week:
      • Today's current conditions
      • 5-day / 3-hour forecast (free OWM tier)

    Returns a dict with:
        total_rain_mm         – total rainfall over the week
        upcoming_rain_48h_mm  – rainfall forecast in the next 48 hours
        avg_temp_c            – average temperature across the period
        dominant_condition    – 'Sunny' | 'Cloudy' | 'Rainy'
        days_summary          – list of per-day summaries (for display)
    """
    params = {"lat": lat, "lon": lon, "appid": OWM_API_KEY, "units": "metric"}

    # --- Current weather ---
    cur_resp = requests.get(OWM_CURRENT_URL, params=params, timeout=10)
    cur_resp.raise_for_status()
    current = cur_resp.json()

    current_temp  = current["main"]["temp"]
    current_rain  = current.get("rain", {}).get("1h", 0.0)
    current_cond  = _owm_condition_to_label(current["weather"][0]["description"])

    # --- 5-day / 3-hour forecast ---
    fcast_resp = requests.get(OWM_FORECAST_URL, params=params, timeout=10)
    fcast_resp.raise_for_status()
    forecast = fcast_resp.json()

    now_utc = datetime.now(timezone.utc)
    cutoff_48h = now_utc + timedelta(hours=48)

    temps, rains, conditions = [current_temp], [current_rain], [current_cond]
    upcoming_rain_48h = current_rain  # rain already falling counts as "upcoming"
    days: dict[str, dict] = {}

    for entry in forecast["list"]:
        dt      = datetime.fromtimestamp(entry["dt"], tz=timezone.utc)
        temp    = entry["main"]["temp"]
        rain    = entry.get("rain", {}).get("3h", 0.0)
        cond    = _owm_condition_to_label(entry["weather"][0]["description"])
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

    # Summarise daily entries
    days_summary = []
    for d in days.values():
        avg_t = sum(d["temps"]) / len(d["temps"])
        dominant = max(set(d["conditions"]), key=d["conditions"].count)
        days_summary.append({
            "date":           d["date"],
            "avg_temp_c":     round(avg_t, 1),
            "rain_mm":        round(d["rain_mm"], 1),
            "condition":      dominant,
        })

    total_rain   = sum(rains)
    avg_temp     = sum(temps) / len(temps)
    dom_condition = max(set(conditions), key=conditions.count)

    return {
        "total_rain_mm":        round(total_rain, 1),
        "upcoming_rain_48h_mm": round(upcoming_rain_48h, 1),
        "avg_temp_c":           round(avg_temp, 1),
        "dominant_condition":   dom_condition,
        "days_summary":         days_summary,
    }


# ─────────────────────────────────────────────
# PREDICTION HELPER
# ─────────────────────────────────────────────

def predict_yield(region, soil_type, crop_type, rainfall_mm, avg_temp,
                  fertilizer, irrigate, weather_condition, days_to_harvest) -> float:
    """Run the LightGBM model and return predicted yield (tonnes/ha)."""
    row = pd.DataFrame({
        "Region":               [region],
        "Soil_Type":            [soil_type],
        "Crop_Type":            [crop_type],
        "Rainfall_mm_Season":   [rainfall_mm],
        "Avg_Temp_C_Season":    [avg_temp],
        "Fertilizer_Used":      [fertilizer],
        "Irrigation_Used":      [irrigate],
        "Weather_Condition":    [weather_condition],
        "Days_to_Harvest":      [days_to_harvest],
    })
    return float(model.predict(row)[0])


# ─────────────────────────────────────────────
# DECISION ENGINE
# ─────────────────────────────────────────────

def build_recommendation(weather: dict, yield_with: float,
                          yield_without: float, upcoming_rain: float) -> dict:
    """
    Combine model output and weather context into a human-readable decision.

    Returns:
        should_irrigate  – True / False
        confidence       – 'high' | 'medium' | 'low'
        reason           – one-sentence explanation
        yield_gain       – extra tonnes/ha from irrigating
    """
    gain = yield_with - yield_without

    # Heavy rain coming — skip irrigation
    if upcoming_rain >= RAIN_UPCOMING_SKIP_MM:
        return {
            "should_irrigate": False,
            "confidence":      "high",
            "reason":          (
                f"No irrigation needed — {upcoming_rain:.0f} mm of rain "
                "is forecast in the next 48 hours. Save water and energy."
            ),
            "yield_gain_tph":  round(gain, 2),
        }

    # Model says irrigation clearly helps
    if gain >= YIELD_GAIN_THRESHOLD:
        confidence = "high" if gain >= 0.6 else "medium"
        return {
            "should_irrigate": True,
            "confidence":      confidence,
            "reason":          (
                f"Irrigate now — the model predicts a gain of "
                f"{gain:.2f} t/ha. Current conditions: "
                f"{weather['dominant_condition']}, "
                f"{weather['avg_temp_c']} °C avg, "
                f"{weather['total_rain_mm']} mm total rain this week."
            ),
            "yield_gain_tph":  round(gain, 2),
        }

    # Model says marginal benefit — let weather decide
    if gain > 0 and weather["dominant_condition"] == "Sunny":
        return {
            "should_irrigate": True,
            "confidence":      "low",
            "reason":          (
                f"Consider irrigating — sunny weather with only "
                f"{weather['total_rain_mm']} mm rain this week. "
                f"Expected yield gain: {gain:.2f} t/ha."
            ),
            "yield_gain_tph":  round(gain, 2),
        }

    # Default: no irrigation needed
    return {
        "should_irrigate": False,
        "confidence":      "medium",
        "reason":          (
            f"No irrigation needed — conditions are sufficient "
            f"({weather['dominant_condition']}, "
            f"{weather['total_rain_mm']} mm rain this week). "
            f"Yield difference: {gain:.2f} t/ha."
        ),
        "yield_gain_tph":  round(gain, 2),
    }


# ─────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────

@app.route("/advice", methods=["GET"])
def get_irrigation_advice():
    """
    Main endpoint for the mobile app.

    Query parameters:
        lat             (float)  – Farm latitude           [required]
        lon             (float)  – Farm longitude          [required]
        crop            (str)    – Crop type               [default: Wheat]
        soil            (str)    – Soil type               [default: Clay]
        region          (str)    – Region name             [default: North]
        fertilizer      (bool)   – Using fertilizer?       [default: true]
        days_to_harvest (int)    – Days remaining          [default: 90]

    Returns JSON:
        should_irrigate, confidence, reason, yield_with_irrigation,
        yield_without_irrigation, yield_gain_tph, weather_summary, days_forecast
    """
    # --- Parse params ---
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
    except (KeyError, ValueError):
        return jsonify({"error": "lat and lon are required numeric parameters."}), 400

    crop            = request.args.get("crop",            "Wheat")
    soil            = request.args.get("soil",            "Clay")
    region          = request.args.get("region",          "North")
    fertilizer      = request.args.get("fertilizer",      "true").lower() == "true"
    days_to_harvest = int(request.args.get("days_to_harvest", 90))

    # --- Fetch weather ---
    try:
        weather = fetch_weekly_weather(lat, lon)
    except requests.HTTPError as e:
        return jsonify({"error": f"Weather API error: {e}"}), 502
    except Exception as e:
        return jsonify({"error": f"Could not fetch weather data: {e}"}), 500

    # --- Run model (two scenarios) ---
    common = dict(
        region=region, soil_type=soil, crop_type=crop,
        rainfall_mm=weather["total_rain_mm"],
        avg_temp=weather["avg_temp_c"],
        fertilizer=fertilizer,
        weather_condition=weather["dominant_condition"],
        days_to_harvest=days_to_harvest,
    )
    yield_with    = predict_yield(**common, irrigate=True)
    yield_without = predict_yield(**common, irrigate=False)

    # --- Build recommendation ---
    rec = build_recommendation(
        weather, yield_with, yield_without,
        upcoming_rain=weather["upcoming_rain_48h_mm"]
    )

    # --- Final response ---
    return jsonify({
        # ── Core answer (shown prominently in the mobile UI) ──
        "should_irrigate":          rec["should_irrigate"],
        "confidence":               rec["confidence"],
        "reason":                   rec["reason"],

        # ── Model numbers ──
        "yield_with_irrigation":    round(yield_with,    2),
        "yield_without_irrigation": round(yield_without, 2),
        "yield_gain_tph":           rec["yield_gain_tph"],

        # ── Weather context (shown in the UI weekly strip) ──
        "weather_summary": {
            "total_rain_mm":        weather["total_rain_mm"],
            "upcoming_rain_48h_mm": weather["upcoming_rain_48h_mm"],
            "avg_temp_c":           weather["avg_temp_c"],
            "dominant_condition":   weather["dominant_condition"],
        },
        "days_forecast":            weather["days_summary"],

        # ── Meta ──
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "farm_params": {
            "lat": lat, "lon": lon, "crop": crop, "soil": soil,
            "region": region, "fertilizer": fertilizer,
            "days_to_harvest": days_to_harvest,
        },
    })


@app.route("/health", methods=["GET"])
def health():
    """Health check — the mobile app can ping this to confirm the backend is alive."""
    return jsonify({"status": "ok", "model": MODEL_PATH})


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # In production, run behind gunicorn:
    #   gunicorn -w 2 -b 0.0.0.0:5000 app:app
    app.run(host="0.0.0.0", port=5000, debug=True)

#ColumnOptions:
# Region: East, North, South, West
# Soil_Type: Chalky, Clay, Loam, Peaty, Sandy, Silt
# Crop: Barley, Cotton, Maize, Rice, Soybean, Wheat
# Weather_Condition: Cloudy, Rainy, Sunny