#!/usr/bin/env bash

# Sanity checks for the backend JSON API
# - Assumes the FastAPI server is already running
# - Runs curl commands inspired by src/fit/backend/BACKEND.md
# - Skips OAuth-related endpoints (and any clearly tracker-linked endpoints)
# - Prints status code per request and shows error bodies (>= 400)

set -u -o pipefail

BASE=${BASE:-http://localhost:5002}
echo "Using BASE=$BASE"

tmpdir=$(mktemp -d 2>/dev/null || mktemp -d -t 'fit_sanity')
cleanup() { rm -rf "$tmpdir" 2>/dev/null || true; }
trap cleanup EXIT

header() { echo; echo "== $1 =="; }

# Helper to run curl with auth and report status; extra curl args can be passed after the URL
call() {
  local label="$1"; shift
  local method="$1"; shift
  local url="$1"; shift
  local body_file="$tmpdir/body.$$.$RANDOM.json"
  echo "-- $label: $method $url"
  local status
  status=$(curl -s -o "$body_file" -w "%{http_code}" -X "$method" "$url" -H "Authorization: Bearer $ACCESS" "$@")
  echo "   -> HTTP $status"
  if [[ "$status" -ge 400 ]]; then
    echo "Response body:"; cat "$body_file"; echo
  fi
  # Show small success bodies too for convenience
  if [[ "$status" -lt 400 ]]; then
    # Print compact output (truncate if huge)
    local sz
    sz=$(wc -c < "$body_file" | tr -d ' ')
    if [[ "$sz" -gt 0 && "$sz" -le 4096 ]]; then
      echo "Body:"; cat "$body_file"; echo
    fi
  fi
  rm -f "$body_file"
}

header "Auth: login to obtain ACCESS token"
ACCESS=$(curl -s "$BASE/auth/login" -H 'Content-Type: application/json' -d '{"user_id":42}' | jq -r .access_token)
if [[ -z "${ACCESS:-}" ]]; then
  echo "ERROR: Failed to obtain access token from $BASE/auth/login" >&2
  exit 1
fi
echo "Access token acquired"

header "GET /me"
call "get_me" GET "$BASE/me"

header "Nutrition: create meal"
call "create_meal" POST "$BASE/nutrition/meals" -H 'Content-Type: application/json' \
  -d '{
    "title":"Chicken Bowl","ingredients":"chicken,rice,veggies",
    "calories":600,"protein":45,"carbohydrates":60,"fat":18,"fiber":5,
    "vitamin_a":10,"vitamin_c":20,"vitamin_d":1,"calcium":100,"iron":5,"potassium":300,"sodium":700,"creatine":0,
    "meal_time":"12:30","date_entered":"2024-10-01"
  }'

header "Nutrition: list meals (today)"
call "list_meals_today" GET "$BASE/nutrition/meals"

header "Nutrition: list meals (2024-10-01)"
call "list_meals_specific" GET "$BASE/nutrition/meals?date_str=2024-10-01"

header "Nutrition: delete meal by id (from last create)"
# Try to get the last created meal id from the specific date list
MEALS_JSON=$(curl -s "$BASE/nutrition/meals?date_str=2024-10-01" -H "Authorization: Bearer $ACCESS") || true
MEAL_ID=$(python - <<'PY'
import json,sys
try:
  arr=json.loads(sys.stdin.read())
  # pick the last entry if any
  if isinstance(arr, list) and arr:
    print(arr[-1].get('id',''))
  else:
    print('')
except Exception:
  print('')
PY
<<< "$MEALS_JSON")
if [[ -n "${MEAL_ID:-}" ]]; then
  call "delete_meal" DELETE "$BASE/nutrition/meals/$MEAL_ID"
else
  echo "No meal id found to delete; skipping"
fi

header "Nutrition: analyze meal (LLM)"
call "analyze_meal" POST "$BASE/nutrition/analyze-meal" -H 'Content-Type: application/json' \
  -d '{"text":"grilled chicken with rice and broccoli"}'

header "Nutrition: barcode lookup"
call "barcode_lookup" GET "$BASE/nutrition/barcode/3017620422003"

header "Nutrition: analyze meal image (skipped if file missing)"
if [[ -n "${FOOD_IMG:-}" && -f "$FOOD_IMG" ]]; then
  call "analyze_image" POST "$BASE/nutrition/analyze-meal-image" \
    -F additional_context='omelet with spinach' -F meal_time='08:15' -F file=@"$FOOD_IMG"
else
  echo "FOOD_IMG not set or file missing; skipping image analysis"
fi

header "Nutrition: regenerate analysis with feedback"
call "regenerate_analysis" POST "$BASE/nutrition/regenerate-analysis" -H 'Content-Type: application/json' \
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

header "Nutrition: daily overview (today)"
call "daily_overview" POST "$BASE/nutrition/overview/daily"

header "Nutrition: daily overview (specific date)"
call "daily_overview_date" POST "$BASE/nutrition/overview/daily?date_str=2024-10-01"

header "Nutrition: weekly overview"
call "weekly_overview" POST "$BASE/nutrition/overview/weekly"

header "Nutrition: suggestions (protein)"
call "suggestions_protein" POST "$BASE/nutrition/suggestions/protein"

header "Supplements: create"
call "supplements_create" POST "$BASE/nutrition/supplements" -H 'Content-Type: application/json' \
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

header "Supplements: list"
call "supplements_list" GET "$BASE/nutrition/supplements"

header "Supplements: log consumption"
call "supplements_log" POST "$BASE/nutrition/supplements/log" -H 'Content-Type: application/json' \
  -d '{
    "supplement_name": "Protein Shake",
    "time_consumed": "12:00",
    "servings": 1,
    "date_entered": "2024-10-01"
  }'

header "Water: log"
call "water_log" POST "$BASE/nutrition/water" -H 'Content-Type: application/json' \
  -d '{
    "amount_ml": 500,
    "time_consumed": "09:30",
    "date_entered": "2024-10-01"
  }'

header "Kitchen: list inventory"
call "kitchen_list" GET "$BASE/kitchen/inventory"

header "Kitchen: add inventory item"
call "kitchen_add" POST "$BASE/kitchen/inventory" -H 'Content-Type: application/json' \
  -d '{"title":"Bananas","quantity":6,"unit":"count","category":"Produce"}'

header "Kitchen: bulk add inventory"
call "kitchen_bulk" POST "$BASE/kitchen/inventory/bulk" -H 'Content-Type: application/json' \
  -d '{
    "items": [
      {"title":"Chicken Breast","quantity":2,"unit":"lb","category":"Meats & Fish"},
      {"title":"Spinach","quantity":1,"unit":"bag","category":"Produce"}
    ]
  }'

header "Kitchen: delete first inventory item if present"
INV_JSON=$(curl -s "$BASE/kitchen/inventory" -H "Authorization: Bearer $ACCESS") || true
ROWID=$(python - <<'PY'
import json,sys
try:
  inv=json.loads(sys.stdin.read())
  # inv is {category: [ {rowid,...}, ... ]}
  for _,items in inv.items():
    if isinstance(items, list) and items:
      rid=items[0].get('rowid')
      if rid is not None:
        print(rid)
        raise SystemExit(0)
  print('')
except Exception:
  print('')
PY
<<< "$INV_JSON")
if [[ -n "${ROWID:-}" ]]; then
  call "kitchen_delete" DELETE "$BASE/kitchen/inventory/$ROWID"
else
  echo "No inventory rowid found; skipping delete"
fi

header "Kitchen: parse inventory from text"
call "kitchen_from_text" POST "$BASE/kitchen/inventory/from-text" -H 'Content-Type: application/json' \
  -d '{"items_description":"3 apples, 2 lb chicken, 1 bag spinach"}'

header "Kitchen: parse inventory from image (skipped if file missing)"
if [[ -n "${KITCHEN_IMG:-}" && -f "$KITCHEN_IMG" ]]; then
  call "kitchen_from_image" POST "$BASE/kitchen/inventory/from-image" -F file=@"$KITCHEN_IMG"
else
  echo "KITCHEN_IMG not set or file missing; skipping image parse"
fi

header "Kitchen: generate grocery list"
call "kitchen_grocery" POST "$BASE/kitchen/grocery-list"

header "Performance/Rest: skipped (OAuth/linked trackers required)"
echo "Skipping: /performance/* and /rest/* endpoints"

header "Profile: get"
call "profile_get" GET "$BASE/profile"

header "Profile: update"
call "profile_update" POST "$BASE/profile" -H 'Content-Type: application/json' \
  -d '{
    "name":"Alex",
    "email":"alex@example.com",
    "units":"metric",
    "dietary_restrictions":["vegan","gluten_free"],
    "activity_level":"moderate",
    "weight_goal":"maintain"
  }'

header "Profile: restrictions add/remove"
call "profile_add_restriction" POST "$BASE/profile/restrictions/add" -H 'Content-Type: application/json' \
  -d '{"restriction":"dairy_free","existing_restrictions":["vegan"]}'
call "profile_remove_restriction" POST "$BASE/profile/restrictions/remove" -H 'Content-Type: application/json' \
  -d '{"restriction":"vegan","existing_restrictions":["vegan","gluten_free"]}'

header "Onboarding: status"
call "onboarding_status" GET "$BASE/onboarding/status"

header "Onboarding: complete profile"
call "onboarding_complete_profile" POST "$BASE/onboarding/complete_profile" -H 'Content-Type: application/json' \
  -d '{"name":"Alex","gender":"MALE","units":"metric"}'

header "Onboarding: complete measurements"
call "onboarding_complete_measurements" POST "$BASE/onboarding/complete_measurements" -H 'Content-Type: application/json' \
  -d '{"weight":180,"height_feet":5,"height_inches":11}'

header "Onboarding: complete dietary"
call "onboarding_complete_dietary" POST "$BASE/onboarding/complete_dietary" -H 'Content-Type: application/json' \
  -d '{"existing_restrictions":["vegan","gluten_free"]}'

header "Onboarding: activity selection"
call "onboarding_activity" POST "$BASE/onboarding/handle_activity_selection" -H 'Content-Type: application/json' \
  -d '{"activity_level":"moderate"}'

header "Onboarding: goals selection"
call "onboarding_goals" POST "$BASE/onboarding/handle_goals_selection" -H 'Content-Type: application/json' \
  -d '{"weight_goal":"maintain"}'

header "Auth: refresh (optional)"
REFRESH=$(curl -s "$BASE/auth/login" -H 'Content-Type: application/json' -d '{"user_id":42}' \
  | python - <<'PY'
import sys,json
j=json.load(sys.stdin)
print(j.get('refresh_token',''))
PY
) || true
if [[ -n "${REFRESH:-}" ]]; then
  echo "Attempting refresh..."
  curl -s "$BASE/auth/refresh" -H 'Content-Type: application/json' -d "{\"refresh_token\":\"$REFRESH\"}" | cat
  echo
else
  echo "No refresh token available; skipping refresh"
fi

echo
echo "All sanity checks completed."


