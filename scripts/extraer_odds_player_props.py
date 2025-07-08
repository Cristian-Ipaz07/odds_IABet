import json
import requests
from datetime import datetime
from scripts.config import SPORTRADAR_API_KEY

# Palabras clave de mercados a guardar (amplia si quieres agregar más)
MERCADOS_CLAVE = [
    # total de puntos
    "total points",
    # asistencias
    "total assists",
    # rebotes
    "total rebounds",
    # triples
    "total 3-point",
    # robos
    "total steals",
    # bloqueos
    "total blocks",
    # perdidas
    "total turnovers",
    # dobles (2-point shots)
    "total 2-point",
    # dobles dobles
    "double double",
    # triples dobles
    "triple double",
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

def get_player_props(event_id, api_key=SPORTRADAR_API_KEY):
    """Obtiene y filtra los player props para un evento."""

    url = (
        "https://api.sportradar.com/oddscomparison-player-props/trial/v2/en/"
        f"sport_events/sr%3Asport_event%3A{event_id}/players_props.json"
    )
    headers = {"accept": "application/json", "x-api-key": api_key}
    print("Solicitando datos a la API de SportRadar...")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise ValueError(
            f"Error al obtener los datos: {response.status_code} {response.text}"
        )

    data = response.json()

    # FILTRAR SOLO MERCADOS IMPORTANTES
    filtrado = filtrar_player_props(data)

    return filtrado


if __name__ == "__main__":
    sample_event = "56930759"
    props = get_player_props(sample_event)
    print(json.dumps(props, indent=2, ensure_ascii=False))
