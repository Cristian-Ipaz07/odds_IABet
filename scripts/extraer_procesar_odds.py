import json
import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.config import SPORTRADAR_API_KEY

import requests

class SportRadarTeamOdds:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.sportradar.us/nba/trial/v8/en"
        self.current_season = "2024"
    
    def get_daily_schedule(self, date_str):
        try:
            endpoint = f"{self.base_url}/games/{date_str}/schedule.json"
            params = {'api_key': self.api_key}
            print(f"Obteniendo calendario para {date_str}...")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            schedule_data = response.json()
            return schedule_data
        except Exception as e:
            print(f"Error al obtener calendario: {str(e)}")
            return None

    def get_game_odds(self, game_id):
        try:
            endpoint = f"{self.base_url}/games/{game_id}/odds.json"
            params = {'api_key': self.api_key}
            print(f"Obteniendo odds para el juego {game_id}...")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            odds_data = response.json()
            return odds_data
        except Exception as e:
            print(f"Error al obtener odds: {str(e)}")
            return None

    def get_live_game_stats(self, game_id):
        try:
            endpoint = f"{self.base_url}/games/{game_id}/summary.json"
            params = {'api_key': self.api_key}
            print(f"Obteniendo estadísticas en vivo para el juego {game_id}...")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            live_data = response.json()
            return live_data
        except Exception as e:
            print(f"Error al obtener estadísticas en vivo: {str(e)}")
            return None

    def _process_odds_data(self, market):
        processed = {
            "moneyline": {"home": None, "away": None},
            "spread": {"home": None, "away": None, "points": None},
            "total": {"over": None, "under": None, "points": None}
        }

        if market['name'] == "moneyline":
            for outcome in market.get('outcomes', []):
                if outcome['designation'] == 'home':
                    processed['moneyline']['home'] = outcome.get('odds')
                elif outcome['designation'] == 'away':
                    processed['moneyline']['away'] = outcome.get('odds')

        elif market['name'] == "spread":
            for outcome in market.get('outcomes', []):
                if outcome['designation'] == 'home':
                    processed['spread']['home'] = outcome.get('odds')
                    processed['spread']['points'] = outcome.get('point_spread')
                elif outcome['designation'] == 'away':
                    processed['spread']['away'] = outcome.get('odds')

        elif market['name'] == "total":
            for outcome in market.get('outcomes', []):
                if outcome['designation'] == 'over':
                    processed['total']['over'] = outcome.get('odds')
                    processed['total']['points'] = outcome.get('total')
                elif outcome['designation'] == 'under':
                    processed['total']['under'] = outcome.get('odds')
                    processed['total']['points'] = outcome.get('total')

        return processed

    def process_daily_odds(self, date_str):
        schedule = self.get_daily_schedule(date_str)
        if not schedule or 'games' not in schedule:
            return None

        results = []
        for game in schedule['games']:
            game_id = game['id']
            odds_data = self.get_game_odds(game_id)
            if odds_data and 'bookmakers' in odds_data:
                for bookmaker in odds_data['bookmakers']:
                    markets = bookmaker.get('markets', [])
                    game_odds = {}
                    for market in markets:
                        data = self._process_odds_data(market)
                        for key in data:
                            game_odds[key] = data[key]
                    results.append({
                        "game_id": game_id,
                        "home_team": game['home']['name'],
                        "away_team": game['away']['name'],
                        "odds": game_odds
                    })
        return results

if __name__ == '__main__':
    extractor = SportRadarTeamOdds(SPORTRADAR_API_KEY)

    fecha_hoy = "2024-06-10"
    print(f"\nProcesando odds para {fecha_hoy}")
    odds_hoy = extractor.process_daily_odds(fecha_hoy)

    if odds_hoy:
        print(f"\nResumen de odds para hoy:")
        for game in odds_hoy:
            print(f"\n{game['home_team']} vs {game['away_team']}")
            print(f"Moneyline: {game['odds']['moneyline']}")
            print(f"Spread: {game['odds']['spread']}")
            print(f"Total: {game['odds']['total']}")
