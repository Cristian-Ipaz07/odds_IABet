import os
import json
import requests
from datetime import datetime, timedelta

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_DIR = os.path.join(BASE_DIR, 'json')
ODDS_DIR = os.path.join(JSON_DIR, 'odds_extraidas')

# Crear directorios si no existen
os.makedirs(ODDS_DIR, exist_ok=True)

class OddsExtractor:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
    
    def obtener_todas_odds(self, fecha=None, region="us"):
        """
        Extrae TODOS los mercados (h2h, spreads, totals) en una sola llamada
        """
        try:
            endpoint = f"{self.base_url}/sports/basketball_nba/odds"
            params = {
                'apiKey': self.api_key,
                'regions': region,
                'markets': 'h2h,spreads,totals',  # Solicitar todos los mercados
                'oddsFormat': 'decimal',
                'dateFormat': 'iso'
            }
            
            if fecha:
                params['date'] = fecha
            
            print(f"Obteniendo TODOS los mercados para {'fecha ' + fecha if fecha else 'próximos eventos'}...")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            # Verificar créditos restantes
            remaining = response.headers.get('x-requests-remaining', 'Desconocido')
            print(f"Requests restantes este mes: {remaining}")
            
            odds_data = response.json()
            
            # Guardar en archivo único con todos los mercados
            fecha_archivo = fecha.replace("-", "_") if fecha else "proximos"
            archivo_salida = os.path.join(ODDS_DIR, f"odds_completas_{fecha_archivo}.json")
            
            with open(archivo_salida, 'w') as f:
                json.dump(odds_data, f, indent=2)
            
            print(f"Odds completas guardadas en: {archivo_salida}")
            return odds_data
        
        except Exception as e:
            print(f"Error al obtener odds: {str(e)}")
            return None
    
    def procesar_odds_completas(self, odds_data):
        """Procesa todos los mercados de una sola respuesta API"""
        if not odds_data:
            return None
        
        processed = []
        for game in odds_data:
            game_info = {
                "game_id": game.get('id'),
                "date": game.get('commence_time'),
                "home_team": game.get('home_team'),
                "away_team": game.get('away_team'),
                "odds": {
                    "moneyline": {"home": None, "away": None},
                    "spread": {"home": None, "away": None, "points": None},
                    "total": {"over": None, "under": None, "points": None}
                }
            }
            
            # Procesar todos los bookmakers
            for bookmaker in game.get('bookmakers', []):
                for market in bookmaker.get('markets', []):
                    if market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            if outcome['name'] == game['home_team']:
                                game_info['odds']['moneyline']['home'] = outcome['price']
                            else:
                                game_info['odds']['moneyline']['away'] = outcome['price']
                    
                    elif market['key'] == 'spreads':
                        for outcome in market['outcomes']:
                            if outcome['name'] == game['home_team']:
                                game_info['odds']['spread']['home'] = outcome['price']
                                game_info['odds']['spread']['points'] = outcome['point']
                            else:
                                game_info['odds']['spread']['away'] = outcome['price']
                    
                    elif market['key'] == 'totals':
                        for outcome in market['outcomes']:
                            if outcome['name'] == 'Over':
                                game_info['odds']['total']['over'] = outcome['price']
                                game_info['odds']['total']['points'] = outcome['point']
                            else:
                                game_info['odds']['total']['under'] = outcome['price']
            
            processed.append(game_info)
        
        return processed


if __name__ == '__main__':
    api_key = "9551b637acf113c4c45a0226aa620831"  # ¡Recuerda proteger tu API key!
    
    extractor = OddsExtractor(api_key)
    
    # Ejemplo de uso mejorado
    fechas_prueba = [
        datetime.now().strftime("%Y-%m-%d"),  # Hoy
        (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")  # Mañana
    ]
    
    for fecha in fechas_prueba:
        print(f"\nProcesando fecha: {fecha if fecha else 'Próximos eventos'}")
        
        # Una sola llamada para todos los mercados
        odds_crudas = extractor.obtener_todas_odds(fecha)
        
        if odds_crudas:
            odds_procesadas = extractor.procesar_odds_completas(odds_crudas)
            print(f"Procesados {len(odds_procesadas)} partidos con todos los mercados")
            
            # Ejemplo de output para el primer partido
            if odds_procesadas:
                primer_partido = odds_procesadas[0]
                print("\nEjemplo de datos procesados:")
                print(f"Partido: {primer_partido['home_team']} vs {primer_partido['away_team']}")
                print(f"Moneyline: {primer_partido['odds']['moneyline']}")
                print(f"Spread: {primer_partido['odds']['spread']}")
                print(f"Total: {primer_partido['odds']['total']}")