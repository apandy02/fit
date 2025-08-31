# Backend API Testing Guide

This guide lists handy curl/Python snippets to exercise the JSON API.

```bash
# cd to the fit project root
cd ~/src/fit
```


in one terminal:

```bash
uv run -m uvicorn fit.backend.main:app --reload --host 0.0.0.0 --port 5002
```

Note: Replace the base URL with your running API host/port (for example, `http://localhost:5002` if running a standalone FastAPI server, or `http://localhost:8000/api` if mounted under the web app).

## Auth: Login and set ACCESS

export the base URL:
```bash
export BASE=http://localhost:5002
```

Quick verify the server is responding:
```bash
curl -i "$BASE/auth/login" -H 'Content-Type: application/json' -d '{"user_id":42}'
```

Using jq:
```bash
ACCESS=$(curl -s "$BASE/auth/login" -H 'Content-Type: application/json' -d '{"user_id":42}' | jq -r .access_token)
```

Without jq (Python fallback):
```bash
curl -s "$BASE/auth/login" -H 'Content-Type: application/json' -d '{"user_id":42}' | tee /tmp/tokens.json
ACCESS=$(python - <<'PY'
import json;print(json.load(open('/tmp/tokens.json'))['access_token'])
PY
)
```

One-liner without jq and without writing a file:
```bash
ACCESS=$(curl -s "$BASE/auth/login" -H 'Content-Type: application/json' -d '{"user_id":42}' | python -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
```

## Get current user
```bash
curl -s "$BASE/me" -H "Authorization: Bearer $ACCESS"
```

If email/name are null, seed a profile quickly:
```bash
uv run python - <<'PY'
from fit.web.common import database_service
database_service.insert_profile({
  'user_id': 42,
  'name': 'John Doe',
  'email': 'john@example.com',
  'gender': 'MALE',
  'date_of_birth': '1990-01-01',
  'units': 'metric',
  'dietary_restrictions': '',
  'activity_level': 'moderate',
  'weight_goal': 'maintain',
  'fitness_goal': '',
  'onboarding_stage': 1
})
print('ok')
PY
```

## Create a meal
```bash
curl -s -X POST "$BASE/nutrition/meals" \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d '{
    "title":"Chicken Bowl","ingredients":"chicken,rice,veggies",
    "calories":600,"protein":45,"carbohydrates":60,"fat":18,"fiber":5,
    "vitamin_a":10,"vitamin_c":20,"vitamin_d":1,"calcium":100,"iron":5,"potassium":300,"sodium":700,"creatine":0,
    "meal_time":"12:30","date_entered":"2024-10-01"
  }'
```

## List meals
```bash
# today by default
curl -s "$BASE/nutrition/meals" -H "Authorization: Bearer $ACCESS"

# or for specific date
curl -s "$BASE/nutrition/meals?date_str=2024-10-01" -H "Authorization: Bearer $ACCESS"
```

## Delete a meal
```bash
curl -i -s -X DELETE "$BASE/nutrition/meals/1" -H "Authorization: Bearer $ACCESS"
```

## Analyze a meal (requires model config in your env)
```bash
curl -s -X POST "$BASE/nutrition/analyze-meal" \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d '{"text":"grilled chicken with rice and broccoli"}'
```

## Analyze a food image
```bash
curl -s -X POST "$BASE/nutrition/analyze-meal-image" \
  -H "Authorization: Bearer $ACCESS" \
  -F additional_context='omelet with spinach' \
  -F meal_time='08:15' \
  -F file=@/full/path/to/food.jpg
```

## Regenerate analysis with feedback
```bash
curl -s -X POST "$BASE/nutrition/regenerate-analysis" \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d '{
    "feedback": "Portion size was smaller; reduce calories and carbs slightly.",
    "original_breakdown": {
      "title": "Chicken Bowl",
      "ingredients": "chicken,rice,veggies",
      "calories": 600,
      "macronutrients": {
        "protein": 45,
        "carbohydrates": {"total": 60, "fiber": 5, "total_sugar": 0, "added_sugar": 0},
        "fat": {"total": 18, "saturated": 0, "trans": 0}
      },
      "micronutrients": {
        "vitamin_a": 10, "vitamin_c": 20, "vitamin_d": 1,
        "calcium": 100, "iron": 5, "potassium": 300, "sodium": 700
      },
      "conditional_nutrients": {"creatine": 0}
    }
  }'
```

## Generate daily overview
```bash
# For today
curl -s -X POST "$BASE/nutrition/overview/daily" -H "Authorization: Bearer $ACCESS"

# For a specific date
curl -s -X POST "$BASE/nutrition/overview/daily?date_str=2024-10-01" -H "Authorization: Bearer $ACCESS"
```

## Generate weekly overview
```bash
curl -s -X POST "$BASE/nutrition/overview/weekly" -H "Authorization: Bearer $ACCESS"
```

## Get nutrient suggestions
```bash
curl -s -X POST "$BASE/nutrition/suggestions/protein" -H "Authorization: Bearer $ACCESS"
```

## Supplements

Create a supplement (also logs as a meal on the given date/time):
```bash
curl -s -X POST "$BASE/nutrition/supplements" \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d '{
    "title": "Protein Shake",
    "time_consumed": "07:45",
    "calories": 200,
    "protein": 30,
    "carbohydrates": 8,
    "fat": 4,
    "fiber": 1,
    "vitamin_a": 0,
    "vitamin_c": 0,
    "vitamin_d": 0,
    "calcium": 150,
    "iron": 1,
    "potassium": 250,
    "sodium": 150,
    "date_entered": "2024-10-01"
  }'
```

List supplements:
```bash
curl -s "$BASE/nutrition/supplements" -H "Authorization: Bearer $ACCESS"
```

Log supplement consumption entry (by name):
```bash
curl -s -X POST "$BASE/nutrition/supplements/log" \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d '{
    "supplement_name": "Protein Shake",
    "time_consumed": "12:00",
    "servings": 1,
    "date_entered": "2024-10-01"
  }'
```

## Log water
```bash
curl -s -X POST "$BASE/nutrition/water" \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d '{
    "amount_ml": 500,
    "time_consumed": "09:30",
    "date_entered": "2024-10-01"
  }'
```

## Refresh token
```bash
REFRESH=$(python - <<'PY'
import json;print(json.load(open('/tmp/tokens.json'))['refresh_token'])
PY
)
curl -s "$BASE/auth/refresh" -H 'Content-Type: application/json' -d "{\"refresh_token\":\"$REFRESH\"}"
```

---

Tips:
- If you see Not authenticated, ensure $ACCESS is set (print it: `echo "$ACCESS"`).
- If jq is missing, use the Python fallback to extract fields from JSON.
- meal_time can be HH:MM; the backend normalizes it to HH:MM:SS for storage.
 - If you see JSONDecodeError extracting tokens, make sure you first wrote tokens to `/tmp/tokens.json` or use the one-liner that reads from stdin.
