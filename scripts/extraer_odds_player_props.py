import requests
import os
import json
from datetime import datetime

# Palabras clave de mercados a guardar (amplia si quieres agregar más)
MERCADOS_CLAVE = [
    "total points",
    "total rebounds",
    "total assists",
    "total 3-point",
    "total steals",
    "total blocks",
    "total turnovers",
    "double double",
    "triple double",
    "total points plus rebounds",
    "total points plus assists",
    "total rebounds plus assists",
    "total points plus assists plus rebounds"
]

def es_mercado_interesante(nombre_mercado):
    # Normaliza para evitar errores por mayúsculas/minúsculas
    nombre = nombre_mercado.lower()
    for clave in MERCADOS_CLAVE:
        if clave in nombre:
            return True
    return False

def filtrar_player_props(data):
    salida = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "event_id": data.get("sport_event_players_props", {}).get("sport_event", {}).get("id", ""),
            "teams": [c["name"] for c in data.get("sport_event_players_props", {}).get("sport_event", {}).get("competitors", [])]
        },
        "players_props": []
    }
    for player in data.get("sport_event_players_props", {}).get("players_props", []):
        jugador = {
            "player_id": player["player"]["id"],
            "player_name": player["player"]["name"],
            "team_id": player["player"]["competitor_id"],
            "markets": []
        }
        for market in player.get("markets", []):
            if es_mercado_interesante(market.get("name", "")):
                mkt = {
                    "market_id": market.get("id"),
                    "market_name": market.get("name"),
                    "books": []
                }
                for book in market.get("books", []):
                    book_entry = {
                        "book_id": book.get("id"),
                        "book_name": book.get("name"),
                        "outcomes": []
                    }
                    for outcome in book.get("outcomes", []):
                        book_entry["outcomes"].append({
                            "type": outcome.get("type"),
                            "odds_decimal": float(outcome.get("odds_decimal", 0)),
                            "total": float(outcome.get("total", 0))
                        })
                    mkt["books"].append(book_entry)
                jugador["markets"].append(mkt)
        # Solo guarda el jugador si tiene al menos un mercado útil
        if jugador["markets"]:
            salida["players_props"].append(jugador)
    return salida

def main(event_id):
    # DATOS DE LA API
    
    url = f"https://api.sportradar.com/oddscomparison-player-props/trial/v2/en/sport_events/sr%3Asport_event%3A{event_id}/players_props.json"
    headers = {
        "accept": "application/json",
        "x-api-key": "36gjsCXhNXNHAlY5GpJmnULsBVVRtglNholUq3Sa"
    }
    print("Solicitando datos a la API de SportRadar...")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error al obtener los datos: {response.status_code}")
        print(response.text)
        return

    data = response.json()

    # FILTRAR SOLO MERCADOS IMPORTANTES
    filtrado = filtrar_player_props(data)

    # GUARDAR RESULTADO
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, "json", "odds_extraidas")
    os.makedirs(output_dir, exist_ok=True)
    output_filename = "odds_completas_player_props.json"
    output_path = os.path.join(output_dir, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(filtrado, f, ensure_ascii=False, indent=2)
    
    print(f"Player props filtrados guardados en: {output_path}")
    print(f"Jugadores procesados: {len(filtrado['players_props'])}")

if __name__ == "__main__":
    main("56930759")
