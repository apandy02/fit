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
  'weight_goal': 0,
  'fitness_goal': '',
  'onboarding_stage': 1
})
print('ok')
PY
```

## Create a meal
```bash
curl -s -X POST "$BASE/meals" \
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
curl -s "$BASE/meals" -H "Authorization: Bearer $ACCESS"

# or for specific date
curl -s "$BASE/meals?date_str=2024-10-01" -H "Authorization: Bearer $ACCESS"
```

## Delete a meal
```bash
curl -i -s -X DELETE "$BASE/meals/1" -H "Authorization: Bearer $ACCESS"
```

## Analyze a meal (requires model config in your env)
```bash
curl -s -X POST "$BASE/nutrition/analyze" \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d '{"text":"grilled chicken with rice and broccoli"}'
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
