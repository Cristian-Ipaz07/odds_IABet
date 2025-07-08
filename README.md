# odds_IABet

Proyecto sencillo para extraer y analizar cuotas de la NBA usando la API de SportRadar.

## Requisitos
- Python 3.8 o superior
- Instalar dependencias con:
  ```bash
  pip install -r requirements.txt
  ```

## Configuración
1. Abre `scripts/config.py`.
2. Reemplaza `SPORTRADAR_API_KEY` por tu clave actual de SportRadar.
3. Actualiza `CURRENT_NBA_SEASON` si es necesario.

## Uso de las funciones principales
Los scripts están pensados para importarse y utilizarse como funciones. A continuación se muestran algunos ejemplos básicos.

### Obtener odds prematch
```python
from scripts.extraer_odds_prematch import get_prematch_odds

odds = get_prematch_odds("56328113")
print(odds)
```

### Obtener player props
```python
from scripts.extraer_odds_player_props import get_player_props

props = get_player_props("56930759")
print(props)
```

### Analizar odds con un modelo
```python
from scripts.analizador_odds import analizar_odds
import json

with open('data/json/datos_modelo.json') as f:
    modelo = json.load(f)
with open('json/odds_extraidas/odds_evento_56328113.json') as f:
    odds = json.load(f)

analisis = analizar_odds(modelo, odds)
print(analisis)
```

### Analizar player props
```python
from scripts.analizador_odds_player_props import generar_analisis_player_props
import json

with open('data/json/datos_modelo_player_props.json') as f:
    modelo = json.load(f)
with open('json/odds_extraidas/odds_completas_player_props.json') as f:
    odds = json.load(f)

analisis = generar_analisis_player_props(modelo['predictions'], odds['players_props'], odds['metadata'])
print(analisis)
```

## Datos de ejemplo
- `data/json/` contiene ejemplos de modelos y análisis.
- `json/odds_extraidas/` almacena respuestas de la API para pruebas locales.

Este README ofrece una visión rápida para comenzar a trabajar con el proyecto.
