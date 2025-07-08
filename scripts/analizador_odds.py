import json
from datetime import datetime
from statistics import mean
import os

def calcular_probabilidad_implícita(odds):
    """Convierte odds decimales a probabilidad implícita"""
    return 1 / odds if odds else None

def calcular_valor_esperado(prob_modelo, odds_mercado):
    """Calcula el valor esperado de una apuesta"""
    if not odds_mercado or not prob_modelo:
        return 0
    prob_implícita = calcular_probabilidad_implícita(odds_mercado)
    return (prob_modelo - prob_implícita) / prob_implícita if prob_implícita else 0

def obtener_archivo_mas_reciente(directorio):
    """Encuentra el archivo de odds más reciente en el directorio"""
    try:
        archivos = [f for f in os.listdir(directorio) 
                   if f.startswith('odds_completas_') and f.endswith('.json')]
        if not archivos:
            return None
        # Ordenar por fecha en el nombre del archivo
        archivos.sort(reverse=True)
        return os.path.join(directorio, archivos[0])
    except Exception as e:
        print(f"Error buscando archivos: {str(e)}")
        return None

def procesar_odds(odds_data):
    """Consolida odds de diferentes bookmakers para todos los mercados"""
    if isinstance(odds_data, list):
        if len(odds_data) == 0:
            raise ValueError("La lista de odds está vacía")
        odds_data = odds_data[0]
    
    if not isinstance(odds_data, dict) or 'bookmakers' not in odds_data:
        raise ValueError("Formato de datos de odds incorrecto")
    
    consolidated = {
        'moneyline': {'home': [], 'away': []},
        'spread': {'home': [], 'away': [], 'points': []},
        'total': {'over': [], 'under': [], 'points': []}
    }
    
    for bookmaker in odds_data.get('bookmakers', []):
        for market in bookmaker.get('markets', []):
            if market['key'] == 'h2h':
                for outcome in market.get('outcomes', []):
                    if outcome['name'] == odds_data['home_team']:
                        consolidated['moneyline']['home'].append(outcome['price'])
                    else:
                        consolidated['moneyline']['away'].append(outcome['price'])
            
            elif market['key'] == 'spreads':
                for outcome in market.get('outcomes', []):
                    if outcome['name'] == odds_data['home_team']:
                        consolidated['spread']['home'].append(outcome['price'])
                        consolidated['spread']['points'].append(outcome['point'])
                    else:
                        consolidated['spread']['away'].append(outcome['price'])
            
            elif market['key'] == 'totals':
                for outcome in market.get('outcomes', []):
                    if outcome['name'] == 'Over':
                        consolidated['total']['over'].append(outcome['price'])
                        consolidated['total']['points'].append(outcome['point'])
                    else:
                        consolidated['total']['under'].append(outcome['price'])
    
    # Calcular promedios
    for market in consolidated:
        for key in consolidated[market]:
            if consolidated[market][key]:
                if key == 'points':
                    try:
                        consolidated[market][key] = mean(consolidated[market][key])
                    except:
                        consolidated[market][key] = consolidated[market][key][0] if consolidated[market][key] else None
                else:
                    try:
                        consolidated[market][key] = mean(consolidated[market][key])
                    except:
                        consolidated[market][key] = None
            else:
                consolidated[market][key] = None
    
    return consolidated

def generar_recomendaciones(predicciones, odds_consolidadas, odds_data):
    """Genera recomendaciones basadas en valor esperado"""
    recomendaciones = []
    
    for prediccion in predicciones:
        if not isinstance(prediccion, dict):
            continue
            
        try:
            if prediccion.get('prediction_type') == 'is_win':
                team_type = 'home' if prediccion.get('team') == odds_data.get('home_team') else 'away'
                if odds_consolidadas['moneyline'][team_type]:
                    valor = calcular_valor_esperado(
                        prediccion.get('probability', 0),
                        odds_consolidadas['moneyline'][team_type]
                    )
                    
                    recomendaciones.append({
                        'game_id': prediccion.get('game_id', ''),
                        'market': 'moneyline',
                        'selection': prediccion.get('team', ''),
                        'model_prob': prediccion.get('probability', 0),
                        'implied_prob': calcular_probabilidad_implícita(odds_consolidadas['moneyline'][team_type]),
                        'odds': odds_consolidadas['moneyline'][team_type],
                        'value': valor,
                        'confidence': prediccion.get('confidence', 0),
                        'recommendation': 'STRONG BET' if valor > 0.15 else ('BET' if valor > 0.05 else 'NO BET')
                    })
        except Exception as e:
            print(f"Error procesando predicción: {str(e)}")
            continue
    
    return recomendaciones

def generar_json_integrado(predicciones, odds_data, odds_consolidadas, recomendaciones):
    return {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'game_id': odds_data.get('id', ''),
            'home_team': odds_data.get('home_team', ''),
            'away_team': odds_data.get('away_team', ''),
            'commence_time': odds_data.get('commence_time', ''),
            'data_source': odds_data.get('source', 'API')
        },
        'model_predictions': predicciones,
        'odds_consolidadas': odds_consolidadas,
        'value_analysis': recomendaciones,
        'top_recommendation': max(recomendaciones, key=lambda x: x.get('value', 0)) if recomendaciones else None
    }

def imprimir_resumen(analisis):
    print("\n=== RESUMEN DE ANÁLISIS ===")
    print(f"Partido: {analisis.get('metadata', {}).get('home_team', 'Desconocido')} vs {analisis.get('metadata', {}).get('away_team', 'Desconocido')}")
    print(f"Fecha: {analisis.get('metadata', {}).get('commence_time', 'Desconocida')}")
    print(f"Fuente: {analisis.get('metadata', {}).get('data_source', 'Desconocida')}")
    
    print("\nODDS CONSOLIDADAS:")
    print(f"Moneyline - {analisis.get('metadata', {}).get('home_team', 'Local')}: {analisis.get('odds_consolidadas', {}).get('moneyline', {}).get('home', 'N/A'):.2f}")
    print(f"Moneyline - {analisis.get('metadata', {}).get('away_team', 'Visitante')}: {analisis.get('odds_consolidadas', {}).get('moneyline', {}).get('away', 'N/A'):.2f}")
    
    print("\nMEJOR RECOMENDACIÓN:")
    top_rec = analisis.get('top_recommendation')
    if top_rec:
        print(f"Mercado: {top_rec.get('market', '')} - {top_rec.get('selection', '')}")
        print(f"Odds: {top_rec.get('odds', 0):.2f} | Valor: {top_rec.get('value', 0)*100:.1f}%")
        print(f"Confianza modelo: {top_rec.get('confidence', 0)*100:.0f}%")
        print(f"Recomendación: {top_rec.get('recommendation', '')}")
    else:
        print("No hay recomendaciones con valor positivo")

def analizar_odds(datos_modelo, odds_data):
    """Devuelve el análisis completo de odds y predicciones."""

    odds_api = odds_data[0] if isinstance(odds_data, list) else odds_data
    odds_consolidadas = procesar_odds(odds_api)
    recomendaciones = generar_recomendaciones(
        datos_modelo['predictions'], odds_consolidadas, odds_api
    )
    analisis_completo = generar_json_integrado(
        datos_modelo['predictions'], odds_api, odds_consolidadas, recomendaciones
    )
    return analisis_completo


def main(datos_modelo_path, odds_api_path):
    """Ejemplo de uso cargando archivos locales."""

    try:
        with open(datos_modelo_path, 'r', encoding='utf-8') as f:
            datos_modelo = json.load(f)
        with open(odds_api_path, 'r', encoding='utf-8') as f:
            odds_data = json.load(f)

        analisis = analizar_odds(datos_modelo, odds_data)
        imprimir_resumen(analisis)
        return analisis

    except FileNotFoundError as e:
        print(f"\nERROR: {str(e)}")
    except json.JSONDecodeError:
        print("\nERROR: Archivo JSON inválido")
    except Exception as e:
        print(f"\nERROR inesperado: {str(e)}")


if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    datos_modelo_path = os.path.join(BASE_DIR, 'data', 'json', 'datos_modelo.json')
    odds_dir = os.path.join(BASE_DIR, 'json', 'odds_extraidas')
    odds_file = obtener_archivo_mas_reciente(odds_dir)
    if odds_file:
        main(datos_modelo_path, odds_file)
