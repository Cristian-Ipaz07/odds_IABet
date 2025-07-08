import requests
import os
import json

# Parámetros de la consulta
url = "https://api.sportradar.com/oddscomparison-prematch/trial/v2/en/sport_events/sr%3Asport_event%3A56328113/sport_event_markets.json"
api_key = "36gjsCXhNXNHAlY5GpJmnULsBVVRtglNholUq3Sa"

# Headers
headers = {
    "accept": "application/json",
    "x-api-key": api_key
}

# Realizar la petición GET
response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    sport_event = data.get("sport_event", {})
    markets = data.get("markets", [])
    
    # Extraer info del partido
    event_id = sport_event.get("id")
    commence_time = sport_event.get("start_time")
    home_team = ""
    away_team = ""
    competitors = sport_event.get("competitors", [])
    for team in competitors:
        if team.get("qualifier") == "home":
            home_team = team.get("name")
        elif team.get("qualifier") == "away":
            away_team = team.get("name")
    
    # Mapear los nombres de mercado SportRadar a tus claves estándar
    market_key_map = {
        "winner (incl. overtime)": "h2h",
        "1x2": "h2h",  # por si acaso hay 1x2
        "spread (incl. overtime)": "spreads",
        "handicap (incl. overtime)": "spreads",
        "total (incl. overtime)": "totals"
    }
    
    # Solo los que te interesan
    desired_markets = set(market_key_map.keys())
    
    # Procesar bookmakers y mercados
    bookmakers = []
    # Agrupamos por book
    books_dict = {}
    for market in markets:
        m_name = market.get("name")
        m_key = market_key_map.get(m_name)
        if m_key:
            for book in market.get("books", []):
                # Usamos el nombre normalizado como key para agrupar
                book_key = book.get("name", "").lower().replace(" ", "")
                book_title = book.get("name")
                # Inicializar si es la primera vez que lo vemos
                if book_key not in books_dict:
                    books_dict[book_key] = {
                        "key": book_key,
                        "title": book_title,
                        "last_update": None,  # puedes ajustar si el json tiene esta info
                        "markets": []
                    }
                # Outcomes de este mercado
                outcomes = []
                for outcome in book.get("outcomes", []):
                    outcome_dict = {
                        "name": None,
                        "price": float(outcome.get("odds_decimal", 0))
                    }
                    # Para h2h: home/away, para totals: over/under, para spreads: home/away + point
                    if m_key == "h2h":
                        if outcome.get("type") == "home":
                            outcome_dict["name"] = home_team
                        elif outcome.get("type") == "away":
                            outcome_dict["name"] = away_team
                        else:
                            continue  # ignora "draw" y otros
                    elif m_key == "spreads":
                        if outcome.get("type") == "home_handicap":
                            outcome_dict["name"] = home_team
                            outcome_dict["point"] = float(outcome.get("handicap"))
                        elif outcome.get("type") == "away_handicap":
                            outcome_dict["name"] = away_team
                            outcome_dict["point"] = float(outcome.get("handicap"))
                        else:
                            continue
                    elif m_key == "totals":
                        if outcome.get("type") in ["over", "under"]:
                            outcome_dict["name"] = outcome.get("type").capitalize()
                            outcome_dict["point"] = float(outcome.get("total"))
                        else:
                            continue
                    outcomes.append(outcome_dict)
                # Si hay outcomes, añadir el mercado
                if outcomes:
                    books_dict[book_key]["markets"].append({
                        "key": m_key,
                        "last_update": None,
                        "outcomes": outcomes
                    })
    # Pasar a lista
    bookmakers = list(books_dict.values())
    
    # Armar estructura final
    result = [{
        "id": event_id,
        "sport_key": "basketball",  # puedes ajustar si tienes info de la liga
        "sport_title": "Basketball",
        "commence_time": commence_time,
        "home_team": home_team,
        "away_team": away_team,
        "bookmakers": bookmakers
    }]
    
    # Guardar el JSON
    output_dir = "json/odds_extraidas"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"odds_completas_{event_id.replace(':','_')}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Odds guardadas en '{output_file}'")
else:
    print(f"Error {response.status_code}: {response.text}")
