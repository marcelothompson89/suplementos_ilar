import pandas as pd
import re
from typing import Tuple, Optional, List

def extraer_referencias(valor: str) -> Tuple[str, List[str]]:
    """
    Extrae las referencias de un valor y devuelve el valor limpio y las referencias
    Ejemplo: "180 - 3000 [1]" -> ("180 - 3000", ["1"])
    """
    if pd.isna(valor) or valor == '':
        return str(valor), []
    
    valor_str = str(valor).strip()
    
    # Buscar referencias como [1], [2, 4, 5], etc.
    referencias_match = re.findall(r'\[([^\]]+)\]', valor_str)
    referencias = []
    
    for match in referencias_match:
        # Dividir por comas para manejar múltiples referencias
        refs = [ref.strip() for ref in match.split(',')]
        referencias.extend(refs)
    
    # Limpiar el valor removiendo las referencias
    valor_limpio = re.sub(r'\s*\[[^\]]+\]', '', valor_str).strip()
    
    return valor_limpio, referencias

def parsear_rango(valor: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Parsea rangos de valores como '180 - 3000', 'No establecido - 1000', '0,8-6', etc.
    Maneja casos especiales como 'may-15', 'ene-50', 'dic-00'
    
    CORREGIDO: Cuando hay "No establecido - X" o "X - No establecido",
    completa el valor X en ambos campos (mínimo y máximo)
    
    También maneja rangos sin espacios como "0,8-6"
    
    Retorna (minimo, maximo) como tupla de floats o None
    """
    if pd.isna(valor) or valor == '' or valor == 'No establecidos' or valor == 'No establecido':
        return None, None
        
    # Limpiar valor
    valor = str(valor).strip()
    
    # Casos especiales de fechas mal interpretadas por Excel
    casos_especiales = {
        'may-15': '5 - 15',
        'may-25': '5 - 25', 
        'ene-50': '1 - 50',
        'feb-20': '2 - 20',
        'feb-60': '2 - 60',
        'abr-35': '4 - 35',
        'dic-00': '12 - 0',
        '1-dic': '1 - 12',
        'mar-40': '3 - 40'
    }
    
    # Reemplazar casos especiales
    for caso, reemplazo in casos_especiales.items():
        if caso in valor.lower():
            valor = valor.lower().replace(caso, reemplazo)
    
    # Buscar patrones como "180 - 3000", "0,8-6" o "No establecido - 1000"
    if ' - ' in valor:
        # Caso con espacios: "180 - 3000"
        partes = valor.split(' - ')
    elif '-' in valor and 'no establecido' not in valor.lower():
        # Caso sin espacios: "0,8-6" 
        partes = valor.split('-')
    else:
        partes = None

    if partes and len(partes) == 2:
        min_val = partes[0].strip()
        max_val = partes[1].strip()
        
        # Procesar mínimo
        if 'no establecido' in min_val.lower() or min_val == '':
            min_num = None
        else:
            # Reemplazar comas por puntos para decimales
            min_clean = min_val.replace(',', '.')
            try:
                min_num = float(min_clean)
            except:
                min_num = None
        
        # Procesar máximo
        if 'no establecido' in max_val.lower() or max_val == '':
            max_num = None
        else:
            max_clean = max_val.replace(',', '.')
            try:
                max_num = float(max_clean)
            except:
                max_num = None
        
        # CORRECCIÓN: Si uno de los valores es None pero el otro tiene valor,
        # usar el valor numérico disponible para ambos campos
        if min_num is None and max_num is not None:
            # Caso: "No establecido - 3000" -> (3000, 3000)
            return max_num, max_num
        elif max_num is None and min_num is not None:
            # Caso: "0,3 - No establecido" -> (0.3, 0.3)
            return min_num, min_num
        else:
            # Caso normal con ambos valores o ambos None
            return min_num, max_num
    else:
        # Valor único
        if 'none' in valor.lower() or 'no establecido' in valor.lower():
            return None, None
        
        valor_clean = valor.replace(',', '.')
        try:
            num = float(valor_clean)
            return num, num
        except:
            return None, None


def parsear_guatemala(valor: str) -> List[dict]:
    """
    Parsea los valores complejos de Guatemala que tienen formato AL:x-y / PF:z-w
    CORREGIDO: Ahora utiliza parsear_rango() para manejar correctamente los valores numéricos
    """
    if pd.isna(valor) or 'No establecidos' in str(valor):
        return []
    
    valor_str = str(valor).strip()
    resultados = []
    
    # Dividir por /
    partes = valor_str.split('/')
    
    for parte in partes:
        parte = parte.strip()
        if ':' in parte:
            tipo, rango = parte.split(':', 1)
            tipo = tipo.strip()
            
            # Mapear tipos
            tipo_completo = {
                'AL': 'Suplementos Alimenticios',
                'PF': 'Productos Farmacéuticos',
                'UL': 'Límite Superior'
            }.get(tipo, tipo)
            
            # CORRECCIÓN: Usar parsear_rango() para procesar correctamente el rango
            minimo, maximo = parsear_rango(rango.strip())
            
            resultados.append({
                'categoria': tipo_completo,
                'minimo': minimo,
                'maximo': maximo
            })
    
    return resultados

def normalizar_datos_suplementos():
    """
    Normaliza los datos completos de vitaminas y minerales de América Latina
    """
    datos_normalizados = []
    
    # DATOS COMPLETOS DE VITAMINAS (basado en tu tabla)
    vitaminas_raw = {
        'Argentina': {
            'Vitamina A / Retinol (µg)': '180 - 3000 [1]',
            'Ácido Fólico (µg)': '72 - 1000 [2]',
            'Beta Caroteno (mg)': '1,08 - 17,96 [3]',
            'Biotina (µg)': '9 - 2500 [4]',
            'Vit B1 / Tiamina (mg)': '0,36 - 100 [5]',
            'Vit B2 / Riboflavina (mg)': '0,39 - 200 [6]',
            'Vit B3 / Niacina (mg)': '4,8 - 500 [7]',
            'Vit B5 / Ac. Pantoténico (mg)': '1,5 - 1000 [8]',
            'Vit B6 / Piridoxina (mg)': '0,39 - 100 [9]',
            'Vit B12 / Cianocobalamina (µg)': '0,72 - 3000 [10]',
            'Vit C / Ac. Ascórbico (mg)': '13,5 - 2000 [11]',
            'Vitamina D (µg)': '1,5 - 100 [12]',
            'Vitamina E /d-tocoferol (mg)': '3 - 1000 [13]',
            'Vitamina K (µg)': '19,5 - 10000 [14]',
            'Colina (mg)': 'No establecidos'
        },
        'Brasil': {
            'Vitamina A / Retinol (µg)': '135 - 2623,61 [15]',
            'Ácido Fólico (µg)': '60 - 1281,5 [16]',
            'Beta Caroteno (mg)': '0,8 - 12,12 [17]',
            'Biotina (µg)': '4,5 - 5,64 [18]',
            'Vit B1 / Tiamina (mg)': '0,18 - 2,02 [19]',
            'Vit B2 / Riboflavina (mg)': '0,2 - 2,74 [20]',
            'Vit B3 / Niacina (mg)': '2,4 - 35 [21]',
            'Vit B5 / Ac. Pantoténico (mg)': '0,75 - 5,64 [22]',
            'Vit B6 / Piridoxina (mg)': '0,26 - 98,60 [23]',
            'Vit B12 / Cianocobalamina (µg)': '0,36 - 9,64 [24]',
            'Vit C / Ac. Ascórbico (mg)': '13,5 - 1916,02 [25]',
            'Vitamina D (µg)': '3 - 50 [26]',
            'Vitamina E /d-tocoferol (mg)': '2,25 - 1000 [27]',
            'Vitamina K (µg)': '0,18 - 149,06 [28]',
            'Colina (mg)': '82,5 - 3235,15'
        },
        'Chile': {
            'Vitamina A / Retinol (µg)': '200 - 1000',
            'Ácido Fólico (µg)': '100 - 500',
            'Beta Caroteno (mg)': 'may-15',
            'Biotina (µg)': '30 - 150',
            'Vit B1 / Tiamina (mg)': '0,7 - 6',
            'Vit B2 / Riboflavina (mg)': '0,8 - 6',
            'Vit B3 / Niacina (mg)': '4,5 - 20',
            'Vit B5 / Ac. Pantoténico (mg)': 'may-25',
            'Vit B6 / Piridoxina (mg)': 'ene-50',
            'Vit B12 / Cianocobalamina (µg)': '1-dic',
            'Vit C / Ac. Ascórbico (mg)': '60 - 1000',
            'Vitamina D (µg)': 'feb-20',
            'Vitamina E /d-tocoferol (mg)': '20 - 500',
            'Vitamina K (µg)': '80 - 600',
            'Colina (mg)': '275 - 2000'
        },
        'Colombia': {
            'Vitamina A / Retinol (µg)': 'No establecido - 3000 [29]',
            'Ácido Fólico (µg)': 'No establecido - 1000',
            'Beta Caroteno (mg)': 'No establecido - 72',
            'Biotina (µg)': 'No establecido - 900',
            'Vit B1 / Tiamina (mg)': 'No establecido - 100 [30]',
            'Vit B2 / Riboflavina (mg)': 'No establecido - 40',
            'Vit B3 / Niacina (mg)': 'No establecido - 35',
            'Vit B5 / Ac. Pantoténico (mg)': 'No establecido - 200',
            'Vit B6 / Piridoxina (mg)': 'No establecido - 100',
            'Vit B12 / Cianocobalamina (µg)': 'No establecido - 2000 [31]',
            'Vit C / Ac. Ascórbico (mg)': 'No establecido - 1000',
            'Vitamina D (µg)': 'No establecido - 50',
            'Vitamina E /d-tocoferol (mg)': 'No establecido - 1000',
            'Vitamina K (µg)': 'No establecido - 1000 [32]',
            'Colina (mg)': 'No establecidos'
        },
        'Costa Rica': {
            'Vitamina A / Retinol (µg)': '300 - 3000',
            'Ácido Fólico (µg)': '80 - 1000',
            'Beta Caroteno (mg)': 'No establecido - 25',
            'Biotina (µg)': '60 - No establecido',
            'Vit B1 / Tiamina (mg)': '0,3 - No establecido',
            'Vit B2 / Riboflavina (mg)': '0,34 - No establecido',
            'Vit B3 / Niacina (mg)': 'abr-35',
            'Vit B5 / Ac. Pantoténico (mg)': '2 - No establecido',
            'Vit B6 / Piridoxina (mg)': '0,4 - 100',
            'Vit B12 / Cianocobalamina (µg)': '1,2 - No establecido',
            'Vit C / Ac. Ascórbico (mg)': 'dic-00',
            'Vitamina D (µg)': 'feb-60',
            'Vitamina E /d-tocoferol (mg)': '4 - 1000',
            'Vitamina K (µg)': '16 - No establecido',
            'Colina (mg)': 'None'
        },
        'República Dominicana': {
            'Vitamina A / Retinol (µg)': 'No establecido',
            'Ácido Fólico (µg)': 'No establecido',
            'Beta Caroteno (mg)': 'No establecido',
            'Biotina (µg)': 'No establecido',
            'Vit B1 / Tiamina (mg)': 'No establecido',
            'Vit B2 / Riboflavina (mg)': 'No establecido',
            'Vit B3 / Niacina (mg)': 'No establecido',
            'Vit B5 / Ac. Pantoténico (mg)': 'No establecido',
            'Vit B6 / Piridoxina (mg)': 'No establecido',
            'Vit B12 / Cianocobalamina (µg)': 'No establecido',
            'Vit C / Ac. Ascórbico (mg)': 'No establecido',
            'Vitamina D (µg)': 'No establecido',
            'Vitamina E /d-tocoferol (mg)': 'No establecido',
            'Vitamina K (µg)': 'No establecido',
            'Colina (mg)': 'No establecido'
        },
        'Ecuador': {
            'Vitamina A / Retinol (µg)': '120 - 3000 [33]',
            'Ácido Fólico (µg)': '30 - 1000 [34]',
            'Beta Caroteno (mg)': '0,72 - No establecido [35]',
            'Biotina (µg)': '45 - No establecido [36]',
            'Vit B1 / Tiamina (mg)': '0,21 - No establecido [37]',
            'Vit B2 / Riboflavina (mg)': '0,24 - No establecido [38]',
            'Vit B3 / Niacina (mg)': '2,7 - 35 [39]',
            'Vit B5 / Ac. Pantoténico (mg)': '1,5 - No establecido [40]',
            'Vit B6 / Piridoxina (mg)': '0,3 - 100 [41]',
            'Vit B12 / Cianocobalamina (µg)': '0,15 - No establecido [42]',
            'Vit C / Ac. Ascórbico (mg)': '9 - 2000 [43]',
            'Vitamina D (µg)': '0,75 - 100 [44]',
            'Vitamina E /d-tocoferol (mg)': '3 - 1000 [45]',
            'Vitamina K (µg)': '12 - No establecido [46]',
            'Colina (mg)': 'No establecido - 3500 [47]'
        },
        'Guatemala': {
            'Vitamina A / Retinol (µg)': 'AL:15-3000 / PF:160-3000 [48]',
            'Ácido Fólico (µg)': 'AL:66-1000 / PF:80-1000 [49]',
            'Beta Caroteno (mg)': 'No establecidos',
            'Biotina (µg)': 'UL:8-60 / PF:6-2,5 [50]',
            'Vit B1 / Tiamina (mg)': 'AL:0,02-0,15 / PF:0,24-100 [51]',
            'Vit B2 / Riboflavina (mg)': 'AL:0,32-2,4 / PF:0,24-200 [52]',
            'Vit B3 / Niacina (mg)': 'AL:0,32-900 / PF:3-35 [53]',
            'Vit B5 / Ac. Pantoténico (mg)': 'AL:1-7,5 / PF:1-1000 [54]',
            'Vit B6 / Piridoxina (mg)': 'AL:0,34-25 / PF:0,26-100 [55]',
            'Vit B12 / Cianocobalamina (µg)': 'AL:0,8-6 / PF:0,48-3000 [56]',
            'Vit C / Ac. Ascórbico (mg)': 'AL:22-165 / PF:20-2000 [57]',
            'Vitamina D (µg)': 'AL:3-100 / PF:3-50 [58]',
            'Vitamina E /d-tocoferol (mg)': 'AL:2,6-300 / PF:1,8-1000 [59]',
            'Vitamina K (µg)': 'AL:14-105 / PF:12-10000 [60]',
            'Colina (mg)': 'AL:80-600 / PF:NE-3500 [61]'
        },
        'Honduras': {
            'Vitamina A / Retinol (µg)': 'No establecidos',
            'Ácido Fólico (µg)': 'No establecidos',
            'Beta Caroteno (mg)': 'No establecidos',
            'Biotina (µg)': 'No establecidos',
            'Vit B1 / Tiamina (mg)': 'No establecidos',
            'Vit B2 / Riboflavina (mg)': 'No establecidos',
            'Vit B3 / Niacina (mg)': 'No establecidos',
            'Vit B5 / Ac. Pantoténico (mg)': 'No establecidos',
            'Vit B6 / Piridoxina (mg)': 'No establecidos',
            'Vit B12 / Cianocobalamina (µg)': 'No establecidos',
            'Vit C / Ac. Ascórbico (mg)': 'No establecidos',
            'Vitamina D (µg)': 'No establecidos',
            'Vitamina E /d-tocoferol (mg)': 'No establecidos',
            'Vitamina K (µg)': 'No establecidos',
            'Colina (mg)': 'No establecidos'
        },
        'México': {
            'Vitamina A / Retinol (µg)': 'No establecido - 1000',
            'Ácido Fólico (µg)': 'No establecido - 400',
            'Beta Caroteno (mg)': 'No establecido - 15',
            'Biotina (µg)': 'No establecido - 300',
            'Vit B1 / Tiamina (mg)': 'No establecido - 15',
            'Vit B2 / Riboflavina (mg)': 'No establecido - 18',
            'Vit B3 / Niacina (mg)': 'No establecido - 25',
            'Vit B5 / Ac. Pantoténico (mg)': 'No establecido - 20',
            'Vit B6 / Piridoxina (mg)': 'No establecido - 10',
            'Vit B12 / Cianocobalamina (µg)': 'No establecido - 12',
            'Vit C / Ac. Ascórbico (mg)': 'No establecido - 300',
            'Vitamina D (µg)': 'No establecido - 10',
            'Vitamina E /d-tocoferol (mg)': 'No establecido - 200',
            'Vitamina K (µg)': 'No establecido - 30',
            'Colina (mg)': 'No establecidos'
        },
        'Nicaragua': {
            'Vitamina A / Retinol (µg)': 'No establecido',
            'Ácido Fólico (µg)': 'No establecido',
            'Beta Caroteno (mg)': 'No establecido',
            'Biotina (µg)': 'No establecido',
            'Vit B1 / Tiamina (mg)': 'No establecido',
            'Vit B2 / Riboflavina (mg)': 'No establecido',
            'Vit B3 / Niacina (mg)': 'No establecido',
            'Vit B5 / Ac. Pantoténico (mg)': 'No establecido',
            'Vit B6 / Piridoxina (mg)': 'No establecido',
            'Vit B12 / Cianocobalamina (µg)': 'No establecido',
            'Vit C / Ac. Ascórbico (mg)': 'No establecido',
            'Vitamina D (µg)': 'No establecido',
            'Vitamina E /d-tocoferol (mg)': 'No establecido',
            'Vitamina K (µg)': 'No establecido',
            'Colina (mg)': 'No establecido'
        },
        'Panamá': {
            'Vitamina A / Retinol (µg)': 'No establecido',
            'Ácido Fólico (µg)': 'No establecido',
            'Beta Caroteno (mg)': 'No establecido',
            'Biotina (µg)': 'No establecido',
            'Vit B1 / Tiamina (mg)': 'No establecido',
            'Vit B2 / Riboflavina (mg)': 'No establecido',
            'Vit B3 / Niacina (mg)': 'No establecido',
            'Vit B5 / Ac. Pantoténico (mg)': 'No establecido',
            'Vit B6 / Piridoxina (mg)': 'No establecido',
            'Vit B12 / Cianocobalamina (µg)': 'No establecido',
            'Vit C / Ac. Ascórbico (mg)': 'No establecido',
            'Vitamina D (µg)': 'No establecido',
            'Vitamina E /d-tocoferol (mg)': 'No establecido',
            'Vitamina K (µg)': 'No establecido',
            'Colina (mg)': 'No establecido'
        },
        'Perú': {
            'Vitamina A / Retinol (µg)': 'No establecidos',
            'Ácido Fólico (µg)': 'No establecidos',
            'Beta Caroteno (mg)': 'No establecidos',
            'Biotina (µg)': 'No establecidos',
            'Vit B1 / Tiamina (mg)': 'No establecidos',
            'Vit B2 / Riboflavina (mg)': 'No establecidos',
            'Vit B3 / Niacina (mg)': 'No establecidos',
            'Vit B5 / Ac. Pantoténico (mg)': 'No establecidos',
            'Vit B6 / Piridoxina (mg)': 'No establecidos',
            'Vit B12 / Cianocobalamina (µg)': 'No establecidos',
            'Vit C / Ac. Ascórbico (mg)': 'No establecidos',
            'Vitamina D (µg)': 'No establecidos',
            'Vitamina E /d-tocoferol (mg)': 'No establecidos',
            'Vitamina K (µg)': 'No establecidos',
            'Colina (mg)': 'No establecidos'
        },
        'El Salvador': {
            'Vitamina A / Retinol (µg)': 'No establecido',
            'Ácido Fólico (µg)': 'No establecido',
            'Beta Caroteno (mg)': 'No establecido',
            'Biotina (µg)': 'No establecido',
            'Vit B1 / Tiamina (mg)': 'No establecido',
            'Vit B2 / Riboflavina (mg)': 'No establecido',
            'Vit B3 / Niacina (mg)': 'No establecido',
            'Vit B5 / Ac. Pantoténico (mg)': 'No establecido',
            'Vit B6 / Piridoxina (mg)': 'No establecido',
            'Vit B12 / Cianocobalamina (µg)': 'No establecido',
            'Vit C / Ac. Ascórbico (mg)': 'No establecido',
            'Vitamina D (µg)': 'No establecido',
            'Vitamina E /d-tocoferol (mg)': 'No establecido',
            'Vitamina K (µg)': 'No establecido',
            'Colina (mg)': 'No establecido'
        }
    }
    


    minerales_raw = {
        'Argentina': {
            'Magnesio (mg)': '78 - 400 [8]',
            'Cobre (mg)': '0,27 - 9 [3]',
            'Hierro (mg)': '4,2 - 60 [7]',
            'Calcio (mg)': '300 - 1500 [2]',
            'Cromo (µg)': '10,5 - 200 [4]',
            'Flúor (mg)': 'No Establecidos [5]',
            'Fósforo (mg)': '210 - 1500 [6]',
            'Manganeso (mg)': '0,69 - 10 [9]',
            'Molibdeno (µg)': '13,5 - 350 [10]',
            'Selenio (µg)': '10,2 - 200 [11]',
            'Yodo (µg)': '39 - 500 [12]',
            'Zinc (mg)': '2,1 - 30 [13]',
            'Boro (mg)': 'No establecido - 6 [1]',
            'Níquel (mg)': 'No estblecido',
            'Potasio (mg)': 'No establecido',
            'Silicio (mg)': 'No establecidos',
            'Sodio (mg)': 'No establecido',
            'Vanadio (mg)': 'No establecido'
        },
        'Brasil': {
            'Magnesio (mg)': '63 - 350 [20]',
            'Cobre (mg)': '135 - 8975,52 [16]',
            'Hierro (mg)': '2,7 - 34,31 [19]',
            'Calcio (mg)': '180 - 1534,67 [15]',
            'Cromo (µg)': '5,25 - 250 [17]',
            'Flúor (mg)': 'No establecidos',
            'Fósforo (mg)': '105 - 2083,89 [18]',
            'Manganeso (mg)': '0,35 - 1,66 [21]',
            'Molibdeno (µg)': '6,75 - 1955 [22]',
            'Selenio (µg)': '8,25 - 319,75 [24]',
            'Yodo (µg)': '22,5 - 919,02 [27]',
            'Zinc (mg)': '1,65 - 29,59 [28]',
            'Boro (mg)': 'No establecido - 8866 [14]',
            'Níquel (mg)': 'No establecido',
            'Potasio (mg)': 'No establecido [23]',
            'Silicio (mg)': 'No establecido [25]',
            'Sodio (mg)': 'None [26]',
            'Vanadio (mg)': 'No establecido'
        },
        'Chile': {
            'Magnesio (mg)': '75 - 400',
            'Cobre (mg)': '0,5 - 3,3',
            'Hierro (mg)': '3,5 - 25',
            'Calcio (mg)': '400 - 1600',
            'Cromo (µg)': '17,5 - 200',
            'Flúor (mg)': 'No establecido',
            'Fósforo (mg)': '400 - 1600',
            'Manganeso (mg)': '0,5 - 6',
            'Molibdeno (µg)': '25 - 600',
            'Selenio (µg)': '17,5 - 200',
            'Yodo (µg)': '30 - 150',
            'Zinc (mg)': '3,8 - 20',
            'Boro (mg)': 'No establecido',
            'Níquel (mg)': 'No establecido',
            'Potasio (mg)': 'No establecido - 3715 [29]',
            'Silicio (mg)': 'No establecido',
            'Sodio (mg)': 'No establecido - 1610 [30]',
            'Vanadio (mg)': 'No establecido'
        },
        'Colombia': {
            'Magnesio (mg)': 'No establecido - 350 [33]',
            'Cobre (mg)': 'No establecido - 10',
            'Hierro (mg)': 'No establecido - 45',
            'Calcio (mg)': 'No establecido - 1500 [31]',
            'Cromo (µg)': 'No establecido - 1000',
            'Flúor (mg)': 'No establecido - 10',
            'Fósforo (mg)': 'No establecido - 250 [32]',
            'Manganeso (mg)': 'No establecido - 11',
            'Molibdeno (µg)': 'No establecido - 2000',
            'Selenio (µg)': 'No establecido - 400',
            'Yodo (µg)': 'No establecido - 1100',
            'Zinc (mg)': 'No establecido - 40',
            'Boro (mg)': 'No establecido - 6',
            'Níquel (mg)': 'No establecido - 0,72',
            'Potasio (mg)': 'No establecido - 3700 [34]',
            'Silicio (mg)': 'No establecido - 700',
            'Sodio (mg)': 'No establecido - 2300',
            'Vanadio (mg)': 'No establecido - 0,05'
        },
        'Costa Rica': {
            'Magnesio (mg)': '80 - 400',
            'Cobre (mg)': '0,4 - 10 [35]',
            'Hierro (mg)': '3,6 - 60',
            'Calcio (mg)': '200 - 2500',
            'Cromo (µg)': '24 - No establecido',
            'Flúor (mg)': 'No establecido - 10',
            'Fósforo (mg)': '200 - 4000',
            'Manganeso (mg)': '0,4 - 10',
            'Molibdeno (µg)': '15 - 2000',
            'Selenio (µg)': '14 - 400',
            'Yodo (µg)': '30 - 1100',
            'Zinc (mg)': 'mar-40',  # 3-40 (mal interpretado por Excel)
            'Boro (mg)': 'No establecido - 20',
            'Níquel (mg)': 'None',
            'Potasio (mg)': 'None',
            'Silicio (mg)': 'None',
            'Sodio (mg)': 'None',
            'Vanadio (mg)': 'None'
            },
        'República Dominicana': {
            'Magnesio (mg)': 'No establecido',
            'Cobre (mg)': 'No establecido',
            'Hierro (mg)': 'No establecido',
            'Calcio (mg)': 'No establecido',
            'Cromo (µg)': 'No establecido',
            'Flúor (mg)': 'No establecido',
            'Fósforo (mg)': 'No establecido',
            'Manganeso (mg)': 'No establecido',
            'Molibdeno (µg)': 'No establecido',
            'Selenio (µg)': 'No establecido',
            'Yodo (µg)': 'No establecido',
            'Zinc (mg)': 'No establecido',
            'Boro (mg)': 'No establecido',
            'Níquel (mg)': 'No establecido',
            'Potasio (mg)': 'No establecido',
            'Silicio (mg)': 'No establecido',
            'Sodio (mg)': 'No establecido',
            'Vanadio (mg)': 'No establecido'
            },
        'Ecuador': {
            'Magnesio (mg)': '45 - 350 [43]',
            'Cobre (mg)': '0,3 - 10 [38]',
            'Hierro (mg)': '2,1 - No establecido [42]',
            'Calcio (mg)': '120 - 2500 [37]',
            'Cromo (µg)': '18 - No establecido [39]',
            'Flúor (mg)': 'No establecido - 10 [40]',
            'Fósforo (mg)': '150 - 4000 [41]',
            'Manganeso (mg)': '0,3 - 11 [44]',
            'Molibdeno (µg)': '11,25 - 2000 [45]',
            'Selenio (µg)': '10,5 - 400 [48]',
            'Yodo (µg)': '22,5 - 1100 [52]',
            'Zinc (mg)': '2,25 - 40 [53]',
            'Boro (mg)': 'No establecido - 20 [36]',
            'Níquel (mg)': 'No establecido - 1,0 [46]',
            'Potasio (mg)': '525 - No establecido [47]',
            'Silicio (mg)': 'No establecido [49]',
            'Sodio (mg)': 'No establecido - 2300 [50]',
            'Vanadio (mg)': 'No establecido - 1,8 [51]'
            },
        'Guatemala': {
            'Magnesio (mg)': 'AL:70-250 / PF:62-400 [61]',
            'Cobre (mg)': 'AL:0,32-5 / PF: 0,9-10 [56]',
            'Hierro (mg)': 'AL:1,4-10,5 / PF:3,6-45 [60]',
            'Calcio (mg)': 'AL:200-2500 /PF:200-2500 [55]',
            'Cromo (µg)': 'AL: ND / PF: 7-1000 [57]',
            'Flúor (mg)': 'AL:0,68-7 / PF:2-10 [58]',
            'Fósforo (mg)': 'AL:110-825 / PF:140-4000 [59]',
            'Manganeso (mg)': 'AL:0,6-4,5 / PF:0,6-10 [62]',
            'Molibdeno (µg)': 'AL:13-600 / PF:9-2000 [63]',
            'Selenio (µg)': 'AL:14-300 / PF:12-400 [66]',
            'Yodo (µg)': 'AL:30-600 / PF:30-1100 [70]',
            'Zinc (mg)': 'AL:2,34-25 / PF:2,6-40 [71]',
            'Boro (mg)': 'AL:ND / PF:NE-20 [54]',
            'Níquel (mg)': 'AL:NE / PF: NE-1 [64]',
            'Potasio (mg)': 'AL:700-5250/PF:0,94-NE [65]',
            'Silicio (mg)': 'AL:ND / PF:ND [67]',
            'Sodio (mg)': 'AL:400-3000 / PF:300-NE [68]',
            'Vanadio (mg)': 'AL: ND / PF:ND [69]'
            },
        'Honduras': {
            'Magnesio (mg)': 'No establecidos',
            'Cobre (mg)': 'No establecidos',
            'Hierro (mg)': 'No establecidos',
            'Calcio (mg)': 'No establecidos',
            'Cromo (µg)': 'No establecidos',
            'Flúor (mg)': 'No establecidos',
            'Fósforo (mg)': 'No establecidos',
            'Manganeso (mg)': 'No establecidos',
            'Molibdeno (µg)': 'No establecidos',
            'Selenio (µg)': 'No establecidos',
            'Yodo (µg)': 'No establecidos',
            'Zinc (mg)': 'No establecidos',
            'Boro (mg)': 'No establecidos',
            'Níquel (mg)': 'No establecidos',
            'Potasio (mg)': 'No establecidos',
            'Silicio (mg)': 'No establecidos',
            'Sodio (mg)': 'No establecidos',
            'Vanadio (mg)': 'No establecidos'
            },
        'México': {
            'Magnesio (mg)': 'No establecido - 500',
            'Cobre (mg)': 'No establecido - 3',
            'Hierro (mg)': 'No establecido - 20',
            'Calcio (mg)': 'No establecido - 1200',
            'Cromo (µg)': 'No establecido - 200',
            'Flúor (mg)': 'No establecido - 1',
            'Fósforo (mg)': 'No establecido - 1200',
            'Manganeso (mg)': 'No establecido - 7,5',
            'Molibdeno (µg)': 'No establecido - 250',
            'Selenio (µg)': 'No establecido - 100',
            'Yodo (µg)': 'No establecido - 200',
            'Zinc (mg)': 'No establecido - 20 [72]',
            'Boro (mg)': 'No establecidos',
            'Níquel (mg)': 'No establecidos',
            'Potasio (mg)': 'No establecidos',
            'Silicio (mg)': 'No establecidos',
            'Sodio (mg)': 'No establecidos',
            'Vanadio (mg)': 'No establecidos'
            },
        'Nicaragua': {
            'Magnesio (mg)': 'No establecido',
            'Cobre (mg)': 'No establecido',
            'Hierro (mg)': 'No establecido',
            'Calcio (mg)': 'No establecido',
            'Cromo (µg)': 'No establecido',
            'Flúor (mg)': 'No establecido',
            'Fósforo (mg)': 'No establecido',
            'Manganeso (mg)': 'No establecido',
            'Molibdeno (µg)': 'No establecido',
            'Selenio (µg)': 'No establecido',
            'Yodo (µg)': 'No establecido',
            'Zinc (mg)': 'No establecido',
            'Boro (mg)': 'No establecido',
            'Níquel (mg)': 'No establecido',
            'Potasio (mg)': 'No establecido',
            'Silicio (mg)': 'No establecido',
            'Sodio (mg)': 'No establecido',
            'Vanadio (mg)': 'No establecido'
            },
        'Panamá': {
            'Magnesio (mg)': 'No establecido',
            'Cobre (mg)': 'No establecido',
            'Hierro (mg)': 'No establecido',
            'Calcio (mg)': 'No establecido',
            'Cromo (µg)': 'No establecido',
            'Flúor (mg)': 'No establecido',
            'Fósforo (mg)': 'No establecido',
            'Manganeso (mg)': 'No establecido',
            'Molibdeno (µg)': 'No establecido',
            'Selenio (µg)': 'No establecido',
            'Yodo (µg)': 'No establecido',
            'Zinc (mg)': 'No establecido',
            'Boro (mg)': 'No establecido',
            'Níquel (mg)': 'No establecido',
            'Potasio (mg)': 'No establecido',
            'Silicio (mg)': 'No establecido',
            'Sodio (mg)': 'No establecido',
            'Vanadio (mg)': 'No establecido'
            },
        'Perú': {
            'Magnesio (mg)': 'No establecidos',
            'Cobre (mg)': 'No establecidos',
            'Hierro (mg)': 'No establecidos',
            'Calcio (mg)': 'No establecidos',
            'Cromo (µg)': 'No establecidos',
            'Flúor (mg)': 'No establecidos',
            'Fósforo (mg)': 'No establecidos',
            'Manganeso (mg)': 'No establecidos',
            'Molibdeno (µg)': 'No establecidos',
            'Selenio (µg)': 'No establecidos',
            'Yodo (µg)': 'No establecidos',
            'Zinc (mg)': 'No establecidos',
            'Boro (mg)': 'No establecidos',
            'Níquel (mg)': 'No establecidos',
            'Potasio (mg)': 'No establecidos',
            'Silicio (mg)': 'No establecidos',
            'Sodio (mg)': 'No establecidos',
            'Vanadio (mg)': 'No establecidos'
            },
        'El Salvador': {
            'Magnesio (mg)': 'No establecido',
            'Cobre (mg)': 'No establecido',
            'Hierro (mg)': 'No establecido',
            'Calcio (mg)': 'No establecido',
            'Cromo (µg)': 'No establecido',
            'Flúor (mg)': 'No establecido',
            'Fósforo (mg)': 'No establecido',
            'Manganeso (mg)': 'No establecido',
            'Molibdeno (µg)': 'No establecido',
            'Selenio (µg)': 'No establecido',
            'Yodo (µg)': 'No establecido',
            'Zinc (mg)': 'No establecido',
            'Boro (mg)': 'No establecido',
            'Níquel (mg)': 'No establecido',
            'Potasio (mg)': 'No establecido',
            'Silicio (mg)': 'No establecido',
            'Sodio (mg)': 'No establecido',
            'Vanadio (mg)': 'No establecido'
            }
        }

    
    # Procesar datos de vitaminas
    for pais, vitaminas in vitaminas_raw.items():
        for vitamina, valor_original in vitaminas.items():
                # Extraer unidad del nombre
                unidad_match = re.search(r'\((.*?)\)', vitamina)
                unidad = unidad_match.group(1) if unidad_match else 'unidad'
                
                # Limpiar nombre del ingrediente
                nombre_limpio = re.sub(r'\s*\(.*?\)', '', vitamina).strip()
                
                # Extraer referencias y valor limpio
                valor_limpio, referencias = extraer_referencias(valor_original)
                
                # Caso especial: Guatemala con múltiples categorías
                if pais == 'Guatemala' and ('AL:' in valor_limpio or 'PF:' in valor_limpio or 'UL:' in valor_limpio):
                    categorias_guatemala = parsear_guatemala(valor_limpio)
                    
                    for categoria_data in categorias_guatemala:
                        datos_normalizados.append({
                            'pais': pais,
                            'ingrediente': nombre_limpio,
                            'tipo': 'Vitamina',
                            'unidad': unidad,
                            'minimo': categoria_data['minimo'],
                            'maximo': categoria_data['maximo'],
                            'establecido': categoria_data['minimo'] is not None or categoria_data['maximo'] is not None,
                            'categoria_regulacion': categoria_data['categoria'],
                            'referencias': ','.join(referencias) if referencias else None,
                            'valor_original': valor_original
                        })
                else:
                    # Parsear rango normal
                    minimo, maximo = parsear_rango(valor_limpio)
                    
                    datos_normalizados.append({
                        'pais': pais,
                        'ingrediente': nombre_limpio,
                        'tipo': 'Vitamina',
                        'unidad': unidad,
                        'minimo': minimo,
                        'maximo': maximo,
                        'establecido': minimo is not None or maximo is not None,
                        'categoria_regulacion': 'Estándar',
                        'referencias': ','.join(referencias) if referencias else None,
                        'valor_original': valor_original
                    })
        
    # Procesar datos de minerales
    for pais, minerales in minerales_raw.items():
        for mineral, valor_original in minerales.items():
                # Extraer unidad del nombre
                unidad_match = re.search(r'\((.*?)\)', mineral)
                unidad = unidad_match.group(1) if unidad_match else 'unidad'
                
                # Limpiar nombre del ingrediente
                nombre_limpio = re.sub(r'\s*\(.*?\)', '', mineral).strip()
                
                # Extraer referencias y valor limpio
                valor_limpio, referencias = extraer_referencias(valor_original)
                
                # Parsear rango
                minimo, maximo = parsear_rango(valor_limpio)
                
                datos_normalizados.append({
                    'pais': pais,
                    'ingrediente': nombre_limpio,
                    'tipo': 'Mineral',
                    'unidad': unidad,
                    'minimo': minimo,
                    'maximo': maximo,
                    'establecido': minimo is not None or maximo is not None,
                    'categoria_regulacion': 'Estándar',
                    'referencias': ','.join(referencias) if referencias else None,
                    'valor_original': valor_original
                })
        
    # Crear DataFrame
    df = pd.DataFrame(datos_normalizados)
    
    return df

def crear_tablas_referencias_separadas():
    """
    Crea tablas de referencias separadas para vitaminas y minerales
    """
    
    # Referencias específicas de VITAMINAS (1-61 del conjunto original)
    referencias_vitaminas = {
        '1': 'Como Retinol Equivalente (RE).',
        '2': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '3': '1 mcg beta-caroteno = 0,167 mcg RE.',
        '4': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '5': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '6': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '7': 'Niacina: niacina preformada (ácido nicotínico + nicotinamida). Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '8': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '9': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '10': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '11': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '12': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '13': 'Como Tocoferol equivalente (TE). Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '14': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '15': 'Valores establecidos para poblaciones iguales o mayores a 19 años. Como equivalente de actividad de retinol (RAE). 1 RAE = 3,33 UI de vitamina A.',
        '16': 'Valores establecidos para poblaciones iguales o mayores a 19 años. Como equivalente de folato dietético (EFD).',
        '17': 'Valores establecidos para poblaciones iguales o mayores a 19 años. Considerar factor de conversión 1 mcg beta-caroteno = 0,167 mcg RE.',
        '18': 'Valores establecidos para poblaciones iguales o mayores a 19 años.',
        '19': 'Valores establecidos para poblaciones iguales o mayores a 19 años.',
        '20': 'Valores establecidos para poblaciones iguales o mayores a 19 años.',
        '21': 'Valores establecidos para poblaciones iguales o mayores a 19 años.',
        '22': 'Valores establecidos para poblaciones iguales o mayores a 19 años.',
        '23': 'Valores establecidos para poblaciones iguales o mayores a 19 años.',
        '24': 'Valores establecidos para poblaciones iguales o mayores a 19 años.',
        '25': 'Valores establecidos para poblaciones iguales o mayores a 19 años.',
        '26': 'Valores establecidos para poblaciones iguales o mayores a 19 años. Como Colecalciferol. 1 μg colecalciferol = 40 UI vitamina D.',
        '27': 'Valores establecidos para poblaciones iguales o mayores a 19 años. Como α-tocoferol.',
        '28': 'Valores establecidos para poblaciones iguales o mayores a 19 años.',
        '29': 'Se debe incluir frase de advertencia especifica en el rotulo sobre el consumo de este ingrediente.',
        '30': 'Se debe incluir frase de advertencia especifica en el rotulo sobre el consumo de este ingrediente.',
        '31': 'Se debe incluir frase de advertencia especifica en el rotulo sobre el consumo de este ingrediente.',
        '32': 'Se debe incluir frase de advertencia especifica en el rotulo sobre el consumo de este ingrediente.',
        '33': 'Valor máximo establecido para hombres a partir de 19 años.',
        '34': 'Valor máximo establecido para hombres a partir de 19 años.',
        '35': 'Valor máximo establecido para hombres a partir de 19 años.',
        '36': 'Valor máximo establecido para hombres a partir de 19 años.',
        '37': 'Valor máximo establecido para hombres a partir de 19 años.',
        '38': 'Valor máximo establecido para hombres a partir de 19 años.',
        '39': 'Valor máximo establecido para hombres a partir de 19 años.',
        '40': 'Valor máximo establecido para hombres a partir de 19 años.',
        '41': 'Valor máximo establecido para hombres a partir de 19 años.',
        '42': 'Valor máximo establecido para hombres a partir de 19 años.',
        '43': 'Valor máximo establecido para hombres a partir de 19 años.',
        '44': 'Valor máximo establecido para hombres a partir de 19 años.',
        '45': 'Valor máximo establecido para hombres a partir de 19 años.',
        '46': 'Valor máximo establecido para hombres a partir de 19 años.',
        '47': 'Valor máximo establecido para hombres a partir de 19 años.',
        '48': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '49': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '50': 'UL: Límite Superior PF: Productos farmacéuticos',
        '51': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '52': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '53': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '54': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '55': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '56': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '57': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '58': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '59': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '60': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '61': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos) NE: No establecido.'
    }
    
    # Referencias específicas de MINERALES (1-72 reutilizando algunas + nuevas específicas)
    referencias_minerales = {
        '1': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '2': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '3': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '4': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '5': 'El nutriente no se encuentra descrito en la lista de vitaminas y minerales permitidos en suplementos alimentarios del Artículo 1381 del CAA.',
        '6': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '7': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '8': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '9': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '10': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '11': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '12': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '13': 'Para embarazadas, lactantes y niños no se deberá exceder la IDR establecida en el Artículo 1387 del CAA.',
        '14': 'Aprobado solo para productos destinados a poblaciones iguales o superiores a 19 años de edad.',
        '15': 'Valor establecido para poblaciones iguales o mayores a 19 años. Valores para otros grupos poblacionales: a. 0 - 6 meses: 30 - 800 mg b. 7 - 11 meses: 39 - 1240 mg c. 1 - 3 años: 105 - 1800 mg d. 4 - 8 años: 150 - 1500 mg e. 9 - 18 años: 195 - 2516,59 mg f. Gestantes: 195 - 2015,51 mg g. Lactantes: 195 - 2082,58 mg Observaciones: la relación mínima calcio/fósforo debe ser de 1:1 y la máxima de 2:1 cuando ambos minerales están presentes en el producto.',
        '16': 'Valor establecido para poblaciones iguales o mayores a 19 años. Valores para otros grupos poblacionales: a. 0 - 11 meses: No autorizado b. 1 - 3 años: 51 - 660 mg c. 4 - 8 años: 66 - 2560 mg d. 9 - 18 años: 133,5 - 3960,51 mg e. Gestantes: 150 - 6935,01 mg f. Lactantes: 195 - 7036,33 mg',
        '17': 'Valor establecido para poblaciones iguales o mayores a 19 años. Valores para otros grupos poblacionales: a. 0 - 6 meses: 0,03 - 0,03 mg b. 7 - 11 meses: 0,825 - 8,25 c. 1 - 3 años: 1,65 - 16,5 mg d. 4 - 8 años: 2,25 - 22,5 mg e. 9 - 18 años: 5,25 - 52,5 mg f. Gestantes: 4,5 - 45 mg g. Lactantes: 6,75 - 67,5 mg',
        '18': 'Valor establecido para poblaciones iguales o mayores a 19 años. Valores para otros grupos poblacionales: a. 0 - 11 meses: No autorizado b. 1 - 3 años: 69 - 2540 mg c. 4 - 8 años: 75 - 2500 mg d. 9 - 18 años: 187,5 - 3077,54 mg e. Gestantes: 187,5 - 2533,15 mg f. Lactantes: 187,5 - 3123,51 mg Observaciones: la relación calcio/fósforo mínima debe ser de 1:1 y la máxima de 2:1 cuando ambos minerales están presentes en el producto.',
        '19': 'Valor establecido para poblaciones iguales o mayores a 19 años. Valores para otros grupos poblacionales: a. 0 - 6 meses: 0,04 - 39,73 mg b. 7 - 11 meses: 1,65 - 29 mg c. 1 - 3 años: 1,05 - 33 mg d. 4 - 8 años: 1,5 - 30 mg e. 9 - 18 años: 2,25 - 29 mg f. Gestantes: 4,05 - 34,71 mg g. Lactantes: 1,5 - 24,96 mg',
        '20': 'Valor establecido para poblaciones iguales o mayores a 19 años. Valores para otros grupos poblacionales: a. 0 - 11 meses: No autorizado b. 1 - 3 años: 12 - 65 mg c. 4 - 8 años: 19,5 - 110 mg d. 9 - 18 años: 63 - 350 mg e. Gestantes: 60 - 350 mg f. Lactantes: 54 - 350 mg',
        '21': 'Valor establecido para poblaciones iguales o mayores a 19 años. Valores para otros grupos poblacionales: a. 0 - 11 meses: No autorizado b. 1 - 3 años: No autorizado c. 4 - 8 años: No autorizado d. 9 - 18 años: No autorizado e. Gestantes: No autorizado f. Lactantes: No autorizado',
        '22': 'Valor establecido para poblaciones iguales o mayores a 19 años. Valores para otros grupos poblacionales: a. 0 - 11 meses: No autorizado b. 1 - 3 años: 2,55 - 283 mg c. 4 - 8 años: 3,3 - 578 mg d. 9 - 18 años: 6,45 - 1057 mg e. Gestantes: 7,5 - 1650 mg f. Lactantes: 7,5 - 1650 mg',
        '23': 'La regulación establece restricciones para el uso del ingrediente.',
        '24': 'Valor establecido para poblaciones iguales o mayores a 19 años. Valores para otros grupos poblacionales: a. 0 - 6 meses: 2,25 - 30 mg b. 7 - 11 meses: 3 - 40 c. 1 - 3 años: 3 - 70 mg d. 4 - 8 años: 4,5 - 120 mg e. 9 - 18 años: 8,25 - 202,46 mg f. Gestantes: 9 - 309,65 mg g. Lactantes: 10,5 - 320,20 mg',
        '25': 'El ingrediente se encuentra autorizado dentro de las sustancias bioactivas.',
        '26': 'La regulación establece restricciones para el uso del ingrediente.',
        '27': 'Valor establecido para poblaciones iguales o mayores a 19 años. Valores para otros grupos poblacionales: a. 0 - 11 meses: No autorizado b. 1 - 3 años: 13,5 - 110 mg c. 4 - 8 años: 13,5 - 210 mg d. 9 - 18 años: 63 - 350 mg e. Gestantes: 33 - 717,56 mg f. Lactantes: 43,5 - 724,36 mg',
        '28': 'Valor establecido para poblaciones iguales o mayores a 19 años. Valores para otros grupos poblacionales: a. 0 - 6 meses: 0,3 - 2 mg b. 7 - 11 meses: 0,45 - 2 mg c. 1 - 3 años: 0,45 - 4 mg d. 4 - 8 años: 0,75 - 7 mg e. 9 - 18 años: 1,65 - 12,77 mg f. Gestantes: 1,8 - 23,50 mg g. Lactantes: 1,95 - 24,45 mg',
        '29': 'Solo permitido en productos que recaen como alimentos para atletas.',
        '30': 'Solo permitido en productos que recaen como alimentos para atletas.',
        '31': 'Se debe incluir frase de advertencia especifica en el rotulo sobre el consumo de este ingrediente.',
        '32': 'Se debe incluir frase de advertencia especifica en el rotulo sobre el consumo de este ingrediente.',
        '33': 'Se debe incluir frase de advertencia especifica en el rotulo sobre el consumo de este ingrediente.',
        '34': 'Se debe incluir frase de advertencia especifica en el rotulo sobre el consumo de este ingrediente.',
        '35': 'La regulación presenta typos en la unidad correspondiente al valor mínimo, haciendo mención a microgramos (µg) siendo la unidad correcta miligramos (mg).',
        '36': 'Valor máximo establecido para hombres a partir de 19 años. Para otros grupos poblacionales los límites máximos son los siguientes: Mujeres 19: 20 Embarazadas: 20 Lactantes: 20',
        '37': 'Valor máximo establecido para hombres a partir de 19 años. Para otros grupos poblacionales los límites máximos son los siguientes: Mujeres 19: 2500 Embarazadas: 2500 Lactantes: 2500',
        '38': 'Valor máximo establecido para hombres a partir de 19 años. Para otros grupos poblacionales los límites máximos son los siguientes: Mujeres 19: 10 Embarazadas: 10 Lactantes: 10',
        '39': 'Valor máximo establecido para hombres a partir de 19 años. Para otros grupos poblacionales los límites máximos son los siguientes: Mujeres 19: No establecido Embarazadas: No establecido Lactantes: No establecido',
        '40': 'Valor máximo establecido para hombres a partir de 19 años. Para otros grupos poblacionales los límites máximos son los siguientes: Mujeres 19: 10 Embarazadas: 10 Lactantes: 10',
        '41': 'Valor máximo establecido para hombres a partir de 19 años. Para otros grupos poblacionales los límites máximos son los siguientes: Mujeres 19: 4000 Embarazadas: 3500 Lactantes: 4000',
        '42': 'Valor máximo establecido para hombres a partir de 19 años. Para otros grupos poblacionales los límites máximos son los siguientes: Mujeres 19: No establecido Embarazadas: No establecido Lactantes: No establecido',
        '43': 'Valor máximo establecido para hombres a partir de 19 años. Para otros grupos poblacionales los límites máximos son los siguientes: Mujeres 19: 350 Embarazadas: 350 Lactantes: 350',
        '44': 'Valor máximo establecido para hombres a partir de 19 años. Para otros grupos poblacionales los límites máximos son los siguientes: Mujeres 19: 11 Embarazadas: 11 Lactantes: 11',
        '45': 'Valor máximo establecido para hombres a partir de 19 años. Para otros grupos poblacionales los límites máximos son los siguientes: Mujeres 19: 2000 Embarazadas: 2000 Lactantes: 2000',
        '46': 'Valor máximo establecido para hombres a partir de 19 años. Para otros grupos poblacionales los límites máximos son los siguientes: Mujeres 19: 1,0 Embarazadas: 1,0 Lactantes: 1,0',
        '47': 'Valor máximo establecido para hombres a partir de 19 años. Para otros grupos poblacionales los límites máximos son los siguientes: Mujeres 19: No establecido Embarazadas: No establecido Lactantes: No establecido',
        '48': 'Valor máximo establecido para hombres a partir de 19 años. Para otros grupos poblacionales los límites máximos son los siguientes: Mujeres 19: 400 Embarazadas: 400 Lactantes: 400',
        '49': 'Valor máximo establecido para hombres a partir de 19 años. Para otros grupos poblacionales los límites máximos son los siguientes: Mujeres 19: No establecido Embarazadas: No establecido Lactantes: No establecido',
        '50': 'Valor máximo establecido para hombres a partir de 19 años. Para otros grupos poblacionales los límites máximos son los siguientes: Mujeres 19: 2300 Embarazadas: 2300 Lactantes: 2300',
        '51': 'Valor máximo establecido para hombres a partir de 19 años. Para otros grupos poblacionales los límites máximos son los siguientes: Mujeres 19: 1,8 Embarazadas: No establecido Lactantes: No establecido',
        '52': 'Valor máximo establecido para hombres a partir de 19 años. Para otros grupos poblacionales los límites máximos son los siguientes: Mujeres 19: 1100 Embarazadas: 1100 Lactantes: 1100',
        '53': 'Valor máximo establecido para hombres a partir de 19 años. Para otros grupos poblacionales los límites máximos son los siguientes: Mujeres 19: 40 Embarazadas:40 Lactantes: 40',
        '54': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos) ND: No descrito. NE: No establecido.',
        '55': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '56': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '57': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos) NE: No establecido.',
        '58': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '59': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '60': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '61': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '62': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '63': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '64': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos) NE: No establecido.',
        '65': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos) NE: No establecido.',
        '66': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '67': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos) ND: No descrito.',
        '68': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos) NE: No establecido.',
        '69': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos) ND: No descrito.',
        '70': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '71': 'AL: Suplementos alimenticios (alimentos) PF: Suplementos dietéticos (productos farmacéuticos)',
        '72': 'Valores solo de referencia'
    }
    
    # Crear DataFrames separados
    df_referencias_vitaminas = pd.DataFrame([
        {'referencia': key, 'descripcion': value, 'tipo': 'Vitamina'}
        for key, value in referencias_vitaminas.items()
    ])
    
    df_referencias_minerales = pd.DataFrame([
        {'referencia': key, 'descripcion': value, 'tipo': 'Mineral'}
        for key, value in referencias_minerales.items()
    ])
    
    return df_referencias_vitaminas, df_referencias_minerales

# Función principal
def main():
    """Ejecuta la normalización y exporta los datos"""
    print("🔄 Normalizando datos completos de suplementos...")
    
    # Normalizar datos
    df = normalizar_datos_suplementos()
    
    # Crear tabla de referencias
    df_referencias_vitaminas, df_referencias_minerales = crear_tablas_referencias_separadas()
    df_referencias = pd.concat([df_referencias_vitaminas, df_referencias_minerales], ignore_index=True)
    
    # Mostrar estadísticas básicas
    print(f"✅ Datos normalizados exitosamente!")
    print(f"📊 Total de registros: {len(df)}")
    print(f"🌎 Países: {df['pais'].nunique()}")
    print(f"🧪 Ingredientes únicos: {df['ingrediente'].nunique()}")
    print(f"💊 Vitaminas: {len(df[df['tipo'] == 'Vitamina'])}")
    print(f"⚗️  Minerales: {len(df[df['tipo'] == 'Mineral'])}")
    print(f"✅ Establecidos: {df['establecido'].sum()}")
    print(f"❌ No establecidos: {(~df['establecido']).sum()}")
    
    # Contar referencias
    referencias_con_datos = df[df['referencias'].notna()]
    print(f"🔖 Registros con referencias: {len(referencias_con_datos)}")
    
    # Mostrar categorías de regulación
    categorias = df['categoria_regulacion'].value_counts()
    print(f"\n📋 Categorías de regulación:")
    for categoria, count in categorias.items():
        print(f"  • {categoria}: {count}")
    
    # Exportar datos principales
    archivo_principal = 'suplementos_normalizados_completo.csv'
    df.to_csv(archivo_principal, index=False, encoding='utf-8')
    print(f"\n💾 Datos principales exportados a: {archivo_principal}")
    
    # Exportar referencias
    archivo_referencias_vitaminas = 'referencias_suplementos_vitaminas.csv'
    df_referencias_vitaminas.to_csv(archivo_referencias_vitaminas, index=False, encoding='utf-8')
    print(f"📚 Referencias vitaminas exportadas a: {archivo_referencias_vitaminas}")
    
    archivo_referencias_minerales = 'referencias_suplementos_minerales.csv'
    df_referencias_minerales.to_csv(archivo_referencias_minerales, index=False, encoding='utf-8')
    print(f"📚 Referencias minerales exportadas a: {archivo_referencias_minerales}")
    
    # Mostrar muestra de datos
    print(f"\n📋 Muestra de datos normalizados:")
    columnas_muestra = ['pais', 'ingrediente', 'tipo', 'minimo', 'maximo', 'establecido', 'referencias']
    print(df[columnas_muestra].head(10).to_string(index=False))
    
    return df, df_referencias

if __name__ == "__main__":
    df, df_referencias = main()