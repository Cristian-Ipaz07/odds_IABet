import json
import os
from datetime import datetime

def calcular_probabilidad_implicita(odds):
    return 1 / odds if odds else None

def calcular_valor_esperado(prob_modelo, odds_mercado):
    if not odds_mercado or not prob_modelo:
        return 0
    prob_implicita = calcular_probabilidad_implicita(odds_mercado)
    return (prob_modelo - prob_implicita) / prob_implicita if prob_implicita else 0

def obtener_mejor_odds(books, tipo, linea):
    """Busca la mejor cuota para ese tipo (over/under) y línea"""
    mejores = []
    for book in books:
        for out in book['outcomes']:
            if out['type'] == tipo and float(out['total']) == float(linea):
                mejores.append(out['odds_decimal'])
    return max(mejores) if mejores else None

def analizar_player_props(predicciones, odds_player_props):
    recomendaciones = []
    for pred in predicciones:
        player_id = pred['player_id']
        market_name = pred['market']
        tipo = pred['prediction_type']  # over/under
        linea = pred['line']

        # Busca jugador y mercado en odds
        jugador = next((p for p in odds_player_props if p['player_id'] == player_id), None)
        if not jugador:
            continue
        mercado = next((m for m in jugador['markets'] if m['market_name'] == market_name), None)
        if not mercado:
            continue

        odds = obtener_mejor_odds(mercado['books'], tipo, linea)
        if not odds:
            continue

        valor = calcular_valor_esperado(pred['probability'], odds)
        recomendaciones.append({
            'player_id': player_id,
            'player_name': pred['player_name'],
            'team': pred['team'],
            'market': market_name,
            'type': tipo,
            'line': linea,
            'model_prob': pred['probability'],
            'implied_prob': calcular_probabilidad_implicita(odds),
            'odds': odds,
            'value': valor,
            'confidence': pred.get('confidence', 0),
            'recommendation': 'STRONG BET' if valor > 0.15 else ('BET' if valor > 0.05 else 'NO BET')
        })
    return recomendaciones

def imprimir_resumen_player_props(analisis):
    print("\n=== RESUMEN DE PLAYER PROPS ===")
    if not analisis['value_analysis']:
        print("No hay recomendaciones con valor positivo.")
        return

    for rec in analisis['value_analysis']:
        print(f"\nJugador: {rec['player_name']} ({rec['team']})")
        print(f"Mercado: {rec['market']} | Línea: {rec['line']} | Tipo: {rec['type'].upper()}")
        print(f"Odds: {rec['odds']:.2f} | Valor Esperado: {rec['value']*100:.1f}%")
        print(f"Prob. modelo: {rec['model_prob']*100:.1f}% | Prob. implícita: {rec['implied_prob']*100:.1f}%")
        print(f"Confianza: {rec['confidence']*100:.0f}% | Recomendación: {rec['recommendation']}")

def analizar_player_props_archivos(odds_player_props_path, modelo_player_props_path):
    """Carga datos desde archivos y devuelve el análisis."""

    with open(odds_player_props_path, 'r', encoding='utf-8') as f:
        odds_data = json.load(f)
    with open(modelo_player_props_path, 'r', encoding='utf-8') as f:
        modelo_data = json.load(f)

    analisis = generar_analisis_player_props(modelo_data['predictions'], odds_data['players_props'], odds_data.get('metadata', {}))
    imprimir_resumen_player_props(analisis)
    return analisis


def generar_analisis_player_props(predicciones, odds_props, metadata=None):
    """Genera el análisis de player props y devuelve un diccionario."""
    recomendaciones = analizar_player_props(predicciones, odds_props)
    return {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'event_id': metadata.get('event_id', '') if metadata else '',
            'teams': metadata.get('teams', []) if metadata else [],
            'data_source': 'API+modelo',
        },
        'model_predictions': predicciones,
        'odds_player_props': odds_props,
        'value_analysis': recomendaciones,
        'top_recommendation': max(recomendaciones, key=lambda x: x.get('value', 0)) if recomendaciones else None,
    }


if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_JSON_DIR = os.path.join(BASE_DIR, 'data', 'json')
    ODDS_JSON_DIR = os.path.join(BASE_DIR, 'json', 'odds_extraidas')
    odds_path = os.path.join(ODDS_JSON_DIR, 'odds_completas_player_props.json')
    modelo_path = os.path.join(DATA_JSON_DIR, 'datos_modelo_player_props.json')
    if os.path.isfile(odds_path) and os.path.isfile(modelo_path):
        analizar_player_props_archivos(odds_path, modelo_path)

