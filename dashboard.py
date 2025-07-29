import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Suplementos América Latina",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
}

.country-card {
    background-color: #ffffff;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid #e0e0e0;
    margin-bottom: 1rem;
}

.vitamin-tag {
    background-color: #e3f2fd;
    color: #1976d2;
    padding: 0.2rem 0.5rem;
    border-radius: 0.3rem;
    font-size: 0.8rem;
    margin: 0.1rem;
    display: inline-block;
}

.mineral-tag {
    background-color: #f3e5f5;
    color: #7b1fa2;
    padding: 0.2rem 0.5rem;
    border-radius: 0.3rem;
    font-size: 0.8rem;
    margin: 0.1rem;
    display: inline-block;
}
.comparison-section {
    background-color: #f8f9fa;
    padding: 1.5rem;
    border-radius: 0.5rem;
    border-left: 4px solid #28a745;
    margin-bottom: 1rem;
}

.regulatory-item {
    background-color: #ffffff;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid #dee2e6;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    line-height: 1.4;
}

.country-header {
    background-color: #007bff;
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 0.3rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
}

.stMarkdown a {
    color: #1f77b4;
    text-decoration: none;
}

.stMarkdown a:hover {
    text-decoration: underline;
}
</style>
""", unsafe_allow_html=True)

# Datos regulatorios estructurados basados en el PDF
CATEGORIAS_REGULATORIAS = {
    "Definición e Instrumento Legal": {
        "Instrumento legal de referencia": "instrumento_legal",
        "Definición legal": "definicion_legal"
    },
    "Clasificación Regulatoria": {
        "Categoría": "categoria_regulatoria",
        "Proceso de autorización": "proceso_autorizacion"
    },
    "Proceso de Autorización": {
        "Proceso de registro/notificación": "proceso_registro",
        "Proceso y autoridades responsables": "autoridades_responsables",
        "Documentación": "documentacion",
        "Tasas": "tasas",
        "Tiempo de aprobación": "tiempo_aprobacion"
    },
    "Etiquetado": {
        "Requisitos de etiquetado general": "etiquetado_general",
        "Requisitos Etiquetado nutrimental": "etiquetado_nutricional",
        "Frases de advertencia obligatoria": "frases_advertencia",
        "Uso de Marcas Paraguas": "marcas_paraguas"
    },
    "Declaración de Propiedades": {
        "Declaración de propiedades de salud": "propiedades_salud",
        "Declaración de propiedades nutricionales": "propiedades_nutricionales"
    },
    "Requisitos de Manufactura Para Establecimientos": {
        "Buenas Prácticas de Manufactura": "bpm"
    },
    "Uso de ingredientes": {
        "Ingredientes permitidos": "ingredientes_permitidos",
        "Proceso para nuevos ingredientes": "nuevos_ingredientes"
    }
}

PAISES_DISPONIBLES = [
    "Argentina", "Brasil", "Chile", "Colombia", "Costa Rica", 
    "República Dominicana", "Ecuador", "Guatemala", "Honduras", 
    "México", "Nicaragua", "Panamá", "Perú", "El Salvador", "Alianza del Pacífico"
]

@st.cache_data
def cargar_datos():
    """Carga los datos desde los archivos CSV"""
    try:
        # Cargar datos principales, manteniendo las referencias como string
        df_principal = pd.read_csv('suplementos_normalizados_completo.csv', dtype={'referencias': 'str'})
        
        # Cargar referencias, manteniendo las referencias como string
        df_ref_vitaminas = pd.read_csv('referencias_suplementos_vitaminas.csv', dtype={'referencia': 'str'})
        df_ref_minerales = pd.read_csv('referencias_suplementos_minerales.csv', dtype={'referencia': 'str'})
        
        df_referencias = pd.concat([df_ref_vitaminas, df_ref_minerales], ignore_index=True)
        
        # Limpiar valores 'nan' en las referencias del dataset principal
        df_principal['referencias'] = df_principal['referencias'].replace('nan', pd.NA)
        
        return df_principal, df_referencias
    except FileNotFoundError as e:
        st.error(f"Error al cargar archivos: {e}")
        st.stop()

def crear_grafico_comparacion_rangos(df, ingrediente_seleccionado):
    """Crea gráfico de comparación de rangos entre países"""
    df_filtrado = df[
        (df['ingrediente'] == ingrediente_seleccionado) & 
        (df['establecido'] == True)
    ].copy()
    
    if df_filtrado.empty:
        return None
    
    # Ordenar por valor mínimo (valores NaN al final)
    df_filtrado = df_filtrado.sort_values('minimo', na_position='last')
    
    fig = go.Figure()
    
    # Agregar rangos como barras de error
    for idx, row in df_filtrado.iterrows():
        color = '#1f77b4' if row['tipo'] == 'Vitamina' else '#ff7f0e'
        
        # Manejar valores NaN
        minimo = row['minimo'] if pd.notna(row['minimo']) else 0
        maximo = row['maximo'] if pd.notna(row['maximo']) else minimo
        
        fig.add_trace(go.Scatter(
            x=[minimo, maximo],
            y=[row['pais'], row['pais']],
            mode='lines+markers',
            name=row['pais'],
            line=dict(color=color, width=6),
            marker=dict(size=8, color=color),
            showlegend=False,
            hovertemplate=f"<b>{row['pais']}</b><br>" +
                         f"Rango: {minimo:.2f} - {maximo:.2f} {row['unidad']}<br>" +
                         f"Categoría: {row['categoria_regulacion']}<extra></extra>"
        ))
    
    fig.update_layout(
        title=f"Comparación de Rangos: {ingrediente_seleccionado}",
        xaxis_title=f"Valores ({df_filtrado.iloc[0]['unidad']})",
        yaxis_title="País",
        height=max(400, len(df_filtrado) * 40),
        showlegend=False
    )
    
    return fig

def enriquecer_con_referencias(df, df_referencias):
    """Enriquece el DataFrame principal con las descripciones de las referencias"""
    df_enriquecido = df.copy()
    
    def obtener_descripcion_referencias(referencias_str, tipo):
        if pd.isna(referencias_str) or str(referencias_str) in ['', 'nan', 'None']:
            return ''
        
        # Convertir las referencias a lista
        try:
            # Asegurar que sea string y limpiar
            referencias_str = str(referencias_str).strip()
            if referencias_str in ['nan', 'None', '']:
                return ''
                
            referencias_list = referencias_str.split(',')
            descripciones = []
            
            for ref in referencias_list:
                ref = ref.strip()
                if ref == '' or ref in ['nan', 'None']:
                    continue
                
                # Buscar la descripción en df_referencias
                # Tanto ref como la columna referencia deben ser strings para la comparación
                ref_row = df_referencias[
                    (df_referencias['referencia'] == ref) & 
                    (df_referencias['tipo'] == tipo)
                ]
                
                if not ref_row.empty:
                    descripciones.append(f"[{ref}] {ref_row.iloc[0]['descripcion']}")
                else:
                    # Debug: veamos qué está pasando
                    descripciones.append(f"[{ref}] ⚠️ No encontrada (tipo: {tipo})")
            
            return ' | '.join(descripciones)
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    # Agregar columna con descripciones de referencias
    df_enriquecido['descripcion_referencias'] = df_enriquecido.apply(
        lambda row: obtener_descripcion_referencias(row['referencias'], row['tipo']), 
        axis=1
    )
    
    return df_enriquecido

def extraer_info_regulatoria_pdf():
    """
    Datos extraídos del PDF de regulaciones.
    """
    return {
        "Argentina": {
            "instrumento_legal": """1. [Código Alimentario Argentino](https://www.argentina.gob.ar/anmat/codigoalimentario) (CAA).
2. [Resolución Conjunta 3/2020](https://www.boletinoficial.gob.ar/detalleAviso/primera/239287/20201229), actualiza el [artículo 1381](https://www.argentina.gob.ar/sites/default/files/capitulo_xvii_dieteticos_actualiz_2022-11.pdf#page=36) del [Código Alimentario Argentino](https://www.argentina.gob.ar/anmat/codigoalimentario) en materia de requisitos de suplementos dietarios.
3. [Disposición ANMAT N° 4980 de 2005](http://www.anmat.gov.ar/webanmat/Legislacion/NormasGenerales/Disposicion_ANMAT_4980-2005.pdf). Normas Específicas para La Publicidad De Suplementos Dietarios (Anexo IV).
4. [Resolución Conjunta 10/2022](https://www.argentina.gob.ar/normativa/nacional/resoluci%C3%B3n-10-2022-375893/texto). Prorroga por 365 días más el plazo de adecuación para la industria. Nueva regulación vigente para nuevos productos, transición extendida hasta diciembre 2023.""",
            
            "definicion_legal": """**Suplementos dietarios**: productos destinados a incrementar la ingesta dietaria habitual, suplementando la incorporación de nutrientes y/u otros ingredientes en la dieta de las personas sanas que, no encontrándose en condiciones patológicas, presenten necesidades básicas dietarias no satisfechas o mayores a las habituales. Deberán ser de administración oral y podrán presentarse en formas sólidas (comprimidos, cápsulas, granulado, polvos u otras) o líquidas (gotas, solución, u otras), u otras formas para absorción gastrointestinal *(Artículo 1381 del CAA)*.""",
            "categoria_regulatoria": "Alimento",
            "proceso_autorizacion": """Los suplementos dietario se encuentran descritos bajo legislación de alimentos (Artículo 1381 del CAA, [Capitulo XVII](https://www.argentina.gob.ar/sites/default/files/anmat_caa_capitulo_xvii_dieteticosactualiz_2021-07.pdf))."""
        },
        "Brasil": {
            "instrumento_legal": """1. [Resolución RDC N° 243/2018](http://antigo.anvisa.gov.br/documents/10181/3898888/RDC_243_2018_COMP.pdf/b6903eb8-0afe-456d-a8ee-5fdd81e8d0cd). Requisitos sanitarios de los suplementos alimentarios (incluye actualizaciones posteriores).
2. [Instrucción Normativa N°28/2018](http://antigo.anvisa.gov.br/documents/10181/3898888/%287%29IN_28_2018_COMP.pdf/59fd99ad-1c35-4835-b5a3-abf61d145937). Listas de componentes, límites de uso, alegaciones y etiquetado adicional de los complementos alimenticios (incluye actualizaciones posteriores).
3. [Resolución RDC N° 239/2018](http://antigo.anvisa.gov.br/legislacao#/visualizar/378663). Lista de aditivos y coadyuvantes autorizados en suplementos alimentarios (incluye actualizaciones posteriores).""",
            
            "definicion_legal": """**Suplemento alimentario** *(Suplemento alimentar en portugués)*: producto de ingestión oral, presentado en formas farmacéuticas, destinado a complementar la dieta de individuos sanos con nutrientes, sustancias bioactivas, enzimas o probióticos, aislados o combinado *(Parágrafo VII, Artículo 3 de la [Resolución RDC N° 243/2018](http://antigo.anvisa.gov.br/documents/10181/3898888/RDC_243_2018_COMP.pdf/b6903eb8-0afe-456d-a8ee-5fdd81e8d0cd))*""",
            "categoria_regulatoria": "Alimento", 
            "proceso_autorizacion": """Los suplementos alimentarios se encuentran descritos bajo la regulación de Alimentos"""
        },

        "Chile": {
        "instrumento_legal": """1. [Decreto N° 977/96](https://dipol.minsal.cl/wp-content/uploads/2022/08/DECRETO_977_96_act_05-07-2022.pdf). Reglamento Sanitario de Alimentos (RSA).
2. [Resolución Exenta N° 860/2017](https://www.bcn.cl/leychile/navegar?idNorma=1105664). Norma Técnica N° 191 sobre directrices nutricionales para declarar propiedades saludables de los alimentos.
3. [Resolución Exenta N° 394/2002](http://www.repositoriodigital.minsal.cl/bitstream/handle/2015/1033/3053.pdf?sequence=1&isAllowed=y). Directrices Nutricionales sobre Suplementos Alimentarios y sus contenidos en Vitaminas y Minerales.""",
        
        "definicion_legal": """**Suplementos alimentarios**: son aquellos productos elaborados o preparados especialmente para suplementar la dieta con fines saludables y contribuir a mantener o proteger estados fisiológicos característicos tales como adolescencia, adultez o vejez.

Su composición podrá corresponder a un nutriente, mezcla de nutrientes y otros componentes presentes naturalmente en los alimentos, incluyendo compuestos tales como vitaminas, minerales, aminoácidos, lípidos, fibra dietética o sus fracciones.

Se podrán expender en diferentes formas de liberación convencional, tales como polvos, líquidos, granulados, grageas, comprimidos, tabletas, cápsulas u otras propias de los medicamentos *(Artículo 534 del RSA)*.""",
        "categoria_regulatoria": "Alimento",
        "proceso_autorizacion": """Los suplementos alimentarios se encuentran descritos bajo la regulación de alimentos en el Titulo XXIX del RSA (Artículos 534-538)."""
    },
    
    "Colombia": {
        "instrumento_legal": """1. [Decreto N° 3249/2006](https://normograma.invima.gov.co/normograma/docs/decreto_3249_2006.htm) Por el cual se reglamenta la fabricación, comercialización, envase, rotulado o etiquetado, régimen de registro sanitario, de control de calidad, de vigilancia sanitaria y control sanitario de los suplementos dietarios
2. [Decreto N° 3863/2008](https://normograma.invima.gov.co/normograma/docs/decreto_3863_2008.htm) Por el cual se modifica el Decreto N° 3249/2006 y se dictan otras disposiciones.
3. [Decreto N° 272/2009](https://normograma.invima.gov.co/normograma/docs/decreto_0272_2009.htm#1) Por el cual se modifica el parágrafo el artículo 24 del Decreto 3249 de 2006, modificado por el artículo 6o del Decreto 3863 de 2008.
4. [Resolución N° 3096/2007](https://normograma.invima.gov.co/normograma/docs/resolucion_minproteccion_3096_2007.htm) Por la cual se establece el reglamento técnico sobre las condiciones y requisitos que deben cumplir los suplementos dietarios que declaren o no información nutricional, propiedades nutricionales, propiedades de salud o cuando su descripción produzca el mismo efecto de las declaraciones de propiedades nutricionales o de las declaraciones de propiedades en salud.""",
        
        "definicion_legal": """**Suplemento dietario**: es aquel producto cuyo propósito es adicionar la dieta normal y que es fuente concentrada de nutrientes y otras sustancias con efecto fisiológico o nutricional que puede contener vitaminas, minerales, proteínas, aminoácidos, otros nutrientes y derivados de nutrientes, plantas, concentrados y extractos de plantas solas o en combinación *(Artículo 2 del Decreto 3249 de 2006)*.""",
        "categoria_regulatoria": "Categoría Intermedia",
        "proceso_autorizacion": """El producto clasificado como "Suplemento dietario" corresponde a una categoría específica no debe ajustarse a las definiciones establecidas en la legislación sanitaria vigente para alimentos, medicamentos, productos fitoterapéuticos o preparaciones farmacéuticas a base de recursos naturales y bebidas alcohólicas (Parágrafo 1, Artículo 3 del [Decreto 3249 de 2006](https://normograma.invima.gov.co/normograma/docs/decreto_3249_2006.htm) y modificado por el Decreto [3863 de 2008](https://normograma.invima.gov.co/normograma/docs/decreto_3863_2008.htm#1))."""
    },
    
    "Costa Rica": {
        "instrumento_legal": """1. [Decreto Ejecutivo: 36134 /2010](http://www.pgrweb.go.cr/scij/Busqueda/Normativa/Normas/nrm_texto_completo.aspx?param1=NRTC&nValor1=1&nValor2=68707&nValor3=107777&param2=1&strTipM=TC&lResultado=5&strSim=simp). Reglamento RTCR 436:2009 Suplementos a la Dieta. Requisitos de Registro Sanitario, Importación, Desalmacenaje, Etiquetado y Verificación.
2. [Decreto Ejecutivo: 36538 /2011](http://www.pgrweb.go.cr/scij/Busqueda/Normativa/Normas/nrm_texto_completo.aspx?param1=NRTC&nValor1=1&nValor2=70321&nValor3=84821&param2=1&strTipM=TC&lResultado=4&strSim=simp). Reforma Reglamento RTCR 436:2009 Suplementos a la Dieta Requisito de Registro Sanitario, Importación, Desalmacenaje, Etiquetado y Verificación.
3. [Decreto Ejecutivo: 40003/2016](http://www.pgrweb.go.cr/scij/Busqueda/Normativa/Normas/nrm_texto_completo.aspx?param1=NRTC&nValor1=1&nValor2=83143&nValor3=107764&param2=1&strTipM=TC&lResultado=3&strSim=simp). Reforma Reglamento RTCR 436:2009 Suplementos a la Dieta. Requisitos de Registro Sanitario, Importación, Desalmacenaje, Etiquetado y Verificación.
4. [Decreto Ejecutivo: 40233 /2017](http://www.pgrweb.go.cr/scij/Busqueda/Normativa/Normas/nrm_texto_completo.aspx?param1=NRTC&nValor1=1&nValor2=83745&nValor3=107763&param2=1&strTipM=TC&lResultado=2&strSim=simp). Reforma Reglamento RTCR 436:2009 Suplementos a la Dieta. Requisitos de Registro Sanitario, Importación, Desalmacenaje, Etiquetado y Verificación y su reforma.
5. [Decreto Ejecutivo: 41382/2018](http://www.pgrweb.go.cr/scij/Busqueda/Normativa/Normas/nrm_texto_completo.aspx?param1=NRTC&nValor1=1&nValor2=87648&nValor3=114247&param2=1&strTipM=TC&lResultado=1&strSim=simp). Reglamento técnico RTCR 492:2018 Suplementos a la dieta, requisitos y procedimiento para el reconocimiento del registro sanitario de otros países.""",
        
        "definicion_legal": """**Suplemento a la dieta**: Es aquel producto alimenticio cuya finalidad es suplir, adicionar, complementar o incrementar la dieta y la ingestión de nutrientes en la alimentación diaria. Se presenta como fuente concentrada de nutrientes y/u otras sustancias con efecto fisiológico o nutricional, solos o combinados, incluyendo compuestos tales como vitaminas, minerales, proteínas, aminoácidos, plantas, concentrados y extractos de plantas, probióticos, sustancias bioactivas u otros nutrientes y sus derivados. Pueden comercializarse en diferentes formas tales como comprimidos, cápsulas, tabletas, polvo, soluciones, jarabes entre otros, dosificados, para ser ingeridos exclusivamente por vía oral y no como alimentos convencionales. Su consumo no deberá representar un riesgo para la salud *(Ítem 3.15 del RTCR 436:2009 Suplementos a la Dieta - Reformado por el [Decreto Ejecutivo: 40003/2016](http://www.pgrweb.go.cr/scij/Busqueda/Normativa/Normas/nrm_texto_completo.aspx?param1=NRTC&nValor1=1&nValor2=83143&nValor3=107764&param2=1&strTipM=TC&lResultado=3&strSim=simp))*.""",
        "categoria_regulatoria": "Alimento",
        "proceso_autorizacion": """En Costa Rica los suplementos a la dieta se clasifican bajo la regulación de los alimentos."""
    },
    
    "República Dominicana": {
        "instrumento_legal": """Actualmente, no hay instrumento legal específico para la categoría de suplementos alimentarios en República Dominicana. El control y vigilancia de estos productos se enmarca en las siguientes regulaciones:

1. [Decreto N° 528 de 2001](https://repositorio.msp.gob.do/bitstream/handle/123456789/856/Dec.No.528-01.PDF?sequence=1&isAllowed=y), que aprueba el reglamento general para control de riesgos en alimentos y bebidas en la República Dominicana.
2. [Decreto N° 246 de 2006](https://repositorio.msp.gob.do/bitstream/handle/123456789/1491/Decreto2462006.pdf?sequence=1&isAllowed=y), que establece el Reglamento que regula la fabricación, elaboración, control de calidad, suministro, circulación, distribución, comercialización, información, publicidad, importación, almacenamiento, dispensación, evaluación, registro y donación de los medicamentos.""",
        
        "definicion_legal": """A pesar que estos productos se encuadren en las regulaciones antes mencionadas, **no hay una definición legal** para los mismos, ni en la regulación de alimentos, ni en la regulación de medicamentos.""",
        "categoria_regulatoria": "Alimento/Medicamento (Caso por caso)",
        "proceso_autorizacion": """Existe una línea muy delgada entre los suplementos alimentarios y los medicamentos, siendo poco clara las reglas que separan a los suplementos que recaen en la categoría de alimentos y los que recaen como medicamentos. Luego de contactar a las autoridades de la Dirección General de Medicamentos, Alimentos y Productos Sanitarios (DIGEMAPS), estas han mencionado que previo a la aplicación para obtener el registro sanitario, es preciso aplicar por el trámite denominado "Consulta de renglón o clasificación" en el cual la autoridad sanitaria evaluará la composición así como el etiquetado del producto para pronunciarse respecto a la clasificación correspondiente.
                De Acuerdo con la autoridad, las posibles clasificaciones son:
                - Alimentos
                - Producto farmacéutico
                - Producto natural (también dentro de la categoría de productos farmacéuticos). Generalmente los productos que contienen especies botánicas recaen en esta clasificación"""
    },
    
    "Ecuador": {
        "instrumento_legal": """1. [Resolución ARCSA-DE-028-2016-YMIH](https://www.controlsanitario.gob.ec/wp-content/uploads/downloads/2022/01/ARCSA-DE-028-2016-YMIH_NORMATIVA-SANITARIA-PARA-CONTROL-DE-SUPLEMENTOS-ALIMENTICIOS..pdf). Normativa Técnica Sanitaria para la obtención de la notificación sanitaria y control de suplementos alimenticios de los establecimientos en donde se fabrican, almacenan, distribuyen, importan y comercializan.
2. [Norma Técnica Ecuatoriana INEN 2983- 2016](https://www.normalizacion.gob.ec/buzon/normas/nte_inen_2983.pdf). Complementos Nutricionales. Requisitos.""",
        
        "definicion_legal": """**Suplementos alimenticios** *(también denominados complementos nutricionales)*: son productos alimenticios no convencionales destinados a complementar la ingesta dietaría mediante la incorporación de nutrientes en cantidades significativas u otras sustancias con efecto nutricional o fisiológico en la dieta de personas sanas. Los nutrientes no deben estar presentes en concentraciones que generen actividad terapéutica alguna a excepción de probióticos. Los nutrientes pueden estar presentes en forma aislada o en combinación. El uso de los suplementos alimenticios no debe ser aplicado a estados patológicos *(Artículo 3 de la [Resolución ARCSA-DE-028-2016-YMIH](https://www.controlsanitario.gob.ec/wp-content/uploads/downloads/2022/01/ARCSA-DE-028-2016-YMIH_NORMATIVA-SANITARIA-PARA-CONTROL-DE-SUPLEMENTOS-ALIMENTICIOS..pdf))*.""",
        "categoria_regulatoria": "Alimento",
        "proceso_autorizacion": """Los suplementos alimenticios se encuentran descritos bajo la regulación de alimentos (Artículo 5 de la [Resolución N° ARCSA-DE-067-2015-GGG](https://www.controlsanitario.gob.ec/wp-content/uploads/downloads/2019/04/ARCSA-DE-067-2015-GGG_NORMATIVA-TÉCNICA-SANITARIA-PARA-ALIMENTOS-PROCESADOS.pdf))."""
    },
    
    "Guatemala": {
        "instrumento_legal": """1. [Norma Técnica 001-2022](http://alertas.directoriolegislativo.org/wp-content/uploads/2022/08/norma-tecnica-001-2022.pdf), para la evaluación y obtención de registro sanitario de suplementos y complementos alimenticios para la población a partir de los tres años de edad.
2. [Norma Técnica 14-2022 Versión 2](https://alertas.directoriolegislativo.org/wp-content/uploads/2022/08/NORMA-T%C3%89CNICA-14.pdf), que regula las condiciones mediante las cuales el departamento otorgará el registro sanitario de suplementos dietéticos.""",
        
        "definicion_legal": """Según la clasificación regulatoria a la que pertenezca el producto, podrá ser denominado **complemento alimenticio**, **suplemento alimenticio** o **suplemento dietético**, correspondiendo a regulaciones distintas.

**Productos clasificados como alimentos**: La regulación describe dos tipos de productos de manera independiente:

• **Suplemento Alimenticio**: Es aquel producto alimenticio cuya finalidad es suplir o adicionar la dieta y la ingestión de nutrientes que la alimentación diaria, no logra. Se presenta como fuente concentrada de nutrientes y/u otras sustancias con efecto nutricional, solos o combinados, incluyendo compuestos tales como vitaminas, minerales, proteínas, aminoácidos u otros nutrientes y sus derivados.

• **Complemento Alimenticio**: son productos fuentes concentradas de vitaminas y minerales, solos o combinados, que se comercializan en formas como por ejemplo cápsulas, tabletas, polvo, soluciones, que está previsto que se tomen en pequeñas cantidades unitarias medidas y no como alimentos convencionales.

**Productos clasificados como farmacéuticos**:

• **Suplemento dietético**: Producto especialmente formulado y destinado a suplementar la incorporación de nutrientes en la dieta de personas sanas, que presentan necesidades dietéticas básicas no satisfechas o mayores a las habituales. Contienen algunos de los siguientes nutrientes: proteínas, lípidos, aminoácidos, glúcidos o carbohidratos, vitaminas, minerales, fibras dietéticas y hierbas.""",
        "categoria_regulatoria": "Alimento/Medicamento (Según composición)",
        "proceso_autorizacion": """En Guatemala los suplementos se clasifican como alimentos o como productos farmacéuticos, dependiendo de su composición. Para esta clasificación incluye los niveles de vitaminas, minerales y otros ingredientes que se encuentren en la composición del producto, sin embargo, el producto no podrá contener ingredientes en cantidades que supongan una actividad terapéutica, y mucho menos exhibir propiedades terapéuticas en su etiquetado."""
    },
    
    "Honduras": {
        "instrumento_legal": """1. [ACUERDO N°6 2005](https://honduras.eregulations.org/media/Acuerdo-06-2005-REGLAMENTO-PARA-EL-CONTROL-SANITARIO.pdf). Reglamento de Control Sanitario de Productos y Servicios
2. [COMUNICADO C-003-ARSA-2018](https://arsa.gob.hn/public/archivos/comunicado0032018.pdf).""",
        
        "definicion_legal": """Los suplementos nutricionales, también mencionados en el Reglamento de Control Sanitario de Productos y Servicios como Complementos y Suplementos dietéticos, se encuentran dentro de la categoría de **Productos Afines**, los cuales también contemplan los cosméticos, productos higiénicos, reactivos y pruebas de laboratorio, material y equipo odontológico y de laboratorios de salud, dispositivos, material y equipo médico quirúrgicos.

Vista la falta de una definición legal para los suplementos, la Agencia de Regulación Sanitaria emitió el [COMUNICADO C-003-ARSA-2018](https://arsa.gob.hn/public/archivos/comunicado0032018.pdf), en el cual introdujo una definición para estos productos en Honduras:

**Suplemento Nutricional**: también denominados complementos nutricionales, suplementos alimenticios o complementos dietarios, son productos alimenticios no convencionales destinados a complementar la ingesta dietaria mediante la incorporación de nutrientes en la dieta de personas sanas, en concentraciones que no generen indicaciones terapéuticas o sean aplicados a estados patológicos. Que se comercializan en formas sólidas (comprimidos, cápsulas, granulados, polvos u otras), semisólidas (galeas, geles u otras), líquidas (gotas, solución, jarabes u otras), u otras formas de absorción gastrointestinal.""",
        "categoria_regulatoria":"Alimento",
        "proceso_autorizacion": """En la actualidad, el control de los suplementos nutricionales los realiza el área de Alimentos y Bebidas de la Agencia de Regulación Sanitaria (ARSA). Cabe destacar que anteriormente, estos productos estaban bajo el control y vigilancia de los productos farmacéuticos, a pesar de que la definición legal introducida por el [COMUNICADO C-003-ARSA-2018](https://arsa.gob.hn/public/archivos/comunicado0032018.pdf) los ubicara como productos alimenticios."""    
    },
    
    "México": {
        "instrumento_legal": """1. [Ley General de Salud](https://www.diputados.gob.mx/LeyesBiblio/pdf/LGS.pdf) (LGS).
2. [Reglamento de Control Sanitario de Productos y Servicios](http://extwprlegs1.fao.org/docs/pdf/mex50634.pdf) (RCSPyS).
3. [NOM-251-SSA1-2009](https://www.dof.gob.mx/normasOficiales/3980/salud/salud.htm), Prácticas de higiene para el proceso de alimentos, bebidas y suplementos alimenticios.
4. [ACUERDO](https://www.dof.gob.mx/nota_detalle.php?codigo=4958062&fecha=15/12/1999#gsc.tab=0) por el que se determinan las plantas prohibidas o permitidas para tés, infusiones y aceites vegetales comestibles. (D.O.F. 15/12/99).
5. [ACUERDO](https://www.dof.gob.mx/nota_detalle.php?codigo=5259470&fecha=16/07/2012) por el que se determinan los aditivos y coadyuvantes en alimentos, bebidas y suplementos alimenticios, su uso y disposiciones sanitarias y sus modificaciones ([Continuación](https://www.dof.gob.mx/nota_detalle.php?codigo=5259472&fecha=16/07/2012)).
6. Farmacopea Herbolaría de los Estados Unidos Mexicanos.""",
        
        "definicion_legal": """**Suplementos alimenticios**: son los productos a base de hierbas, extractos vegetales, alimentos tradicionales, deshidratados o concentrados de frutas, adicionados o no, de vitaminas o minerales, que se puedan presentar en forma farmacéutica y cuya finalidad de uso sea incrementar la ingesta dietética total, complementarla o suplir alguno de sus componentes *(Artículo 215 Fracción V de la Ley General de Salud)*.""",
        "categoria_regulatoria": "Alimento (subcategoría específica)",
        "proceso_autorizacion": """Los suplementos alimenticios se encuentran descritos bajo la regulación de alimentos, sin embargo se los considera una sub-categoría dentro de esta, contando con reglas específicas."""
    },
    
    "Nicaragua": {
        "instrumento_legal": """1. [Resolución Administrativa N° 0562-2021](https://www.minsa.gob.ni/index.php/repository/Descargas-MINSA/Dirección-General-de-Regulación-Sanitaria/Dirección-de-Farmacia/Suplementos-Nutricionales/Resolución-de-Suplementos-Nutricionales/). Condiciones, requisitos y procedimiento para el registro sanitario, renovación, modificaciones posteriores al registro sanitario, importación, distribución y comercialización de los suplementos nutricionales, suplementos dietéticos, suplementos nutritivos, complementos alimenticios y suplementos vitamínicos.
2. [Resolución Administrativa N° 002-2021](https://www.minsa.gob.ni/index.php/repository/Descargas-MINSA/Dirección-General-de-Regulación-Sanitaria/Dirección-de-Farmacia/Suplementos-Nutricionales/Resolución-Administrativa-de-suplementos-002-2021/). Enmienda de la Resolución Administrativa N° 0562-2021 en relación al Anexo II "Concentración de Vitaminas y Minerales en Suplementos Nutricionales.
3. [Resolución Administrativa N° 005-2021](https://www.minsa.gob.ni/index.php/repository/Descargas-MMINSA/Dirección-General-de-Regulación-Sanitaria/Dirección-de-Farmacia/Suplementos-Nutricionales/RResolución-administrativa-N°-005-2021-Resolución-de-facturas-de-suplementos/). Enmienda al Resuelve Quinto de la Resolución Administrativa No. 0562-2021 de fecha 01 de febrero del año 2021.""",
        
        "definicion_legal": """**Suplementos nutricionales, suplementos dietéticos, suplementos nutritivos, complementos alimenticios y suplementos vitamínicos**: son sustancias o mezcla de sustancias destinadas a ser ingeridas por vía oral para complementar los nutrientes presentes normalmente en los alimentos, éstas pueden ser vitaminas, minerales, aminoácidos, carbohidratos, proteínas, grasas o mezclas de estas sustancias con extractos de origen vegetal, animal o enzimas, excepto hormonas y su combinación con vitaminas.""",
        "categoria_regulatoria": "Categoría Intermedia",
        "proceso_autorizacion": """Con la publicación de la [Resolución Administrativa N° 0562-2021](https://www.minsa.gob.ni/index.php/repository/Descargas-MINSA/Dirección-General-de-Regulación-Sanitaria/Dirección-de-Farmacia/Suplementos-Nutricionales/Resolución-de-Suplementos-Nutricionales/) y la creación de la Autoridad Nacional de Regulación Sanitaria mediante la [Ley No. 1068](http://extwprlegs1.fao.org/docs/pdf/nic201992.pdf), los suplementos nutricionales que antes eran clasificados como alimentos o productos farmacéuticos dependiendo de su composición, pasaron a estar bajo el control del Departamento de Productos Naturales Artesanales y Suplementos Nutricionales, adscrito a la Dirección de Farmacia, instancia de la Autoridad Nacional de Regulación Sanitaria. Por tanto, se entiende que, los suplementos nutricionales corresponden a una categoría intermedia con su propia regulación.
                                Cabe destacar que, de acuerdo con la [Resolución Administrativa N° 0562-2021](https://www.minsa.gob.ni/index.php/repository/Descargas-MINSA/Dirección-General-de-Regulación-Sanitaria/Dirección-de-Farmacia/Suplementos-Nutricionales/Resolución-de-Suplementos-Nutricionales/), el caso que la concentración de al menos uno de los componentes sea superior a los establecidos en la regulación, el producto será considerado "producto farmacéutico" y deberá ser registrado en el Departamento de Registro Sanitario de la Dirección de Farmacia conforme los requisitos establecidos en la Resolución Nº 333- 2013 (COMIECO-LXVI)."""
    },
    
    "Panamá": {
        "instrumento_legal": """1. [Resuelto AUPSA – DINAN – 008 – 2006](https://sit.apa.gob.pa/aupsa/requisitos/ReqbrRES008.pdf), Por medio del cual se emiten los Requisitos Sanitarios para la importación de complementos alimentarios de vitaminas y minerales y alimentos preenvasados para regímenes especiales.
2. [Decreto Ejecutivo N° 125 de 2021](https://apa.gob.pa/wp-content/uploads/PDF/reglamentacioAPA.pdf), que crea la Autoridad Panameña de Alimentos APA y deroga AUPSA
3. [Resolución N° 550 DE 2019](https://storage.builderall.com/franquias/2/6698075/editor-html/10659868.pdf), que reglamenta la inscripción de suplementos vitamínicos, dietéticos y alimenticios con propiedades terapéuticas.""",
        
        "definicion_legal": """**Productos clasificados como alimentos**: el Resuelto AUPSA – DINAN – 008 – 2006 no proporciona una definición para los complementos alimentarios de vitaminas y minerales. Sin embargo, El Decreto Ejecutivo N° 125 de 2021 al establecer las reglas para el registro sanitario de alimentos, introdujo la siguiente definición:

**Suplemento Alimenticio**: toda sustancia o mezcla de sustancias destinadas a complementar los nutrientes de alimentos que no contengan propiedades terapéuticas, e incluyan a los alimentos catalogados como "suplementos dietéticos", "suplementos nutricionales", "suplementos de vitaminas y/o minerales", o cualquier otro tipo de "suplemento alimentario".

**Productos clasificados como medicamentos**: La Resolución N° 550 DE 2019 proporciona la siguiente definición:

**Suplementos Dietéticos y/o Nutricionales con Propiedad Terapéutica**: Son Productos cuyas concentraciones y recomendaciones en su formulación sobrepasan los requerimientos nutricionales establecidos por la Organización Mundial de la Salud y se indican para una condición clínica específica. También se considerarán aquellos productos que contengan, extractos de plantas u otros productos botánicos, carbohidratos, aminoácidos, proteínas, ácido grasos y enzimas que se les atribuya o especifique alguna propiedad terapéutica.""",
        "categoria_regulatoria": "Alimento/Medicamento (Consulta de clasificación)",
        "proceso_autorizacion": """Hay una línea muy delgada entre las declaraciones de propiedades saludables y las propiedades terapéuticas debido a la falta de reglas claras, y por otra parte, no hay límites máximos de vitaminas y minerales, así como de otros compuestos que determinen a partir de que cantidad un suplemento puede ser clasificado como alimento o como medicamento.
                                Con base en lo anterior, previo a iniciar el trámite para obtener el registro sanitario, es preciso aplicar por el trámite denominado "Consulta de clasificación" en el cual la Autoridad Panameña de Alimentos (APA) determinará si el registro del producto corresponde a dicha entidad, o si por el contrario, corresponde a la Dirección Nacional de Farmacia y Drogas."""
    },
    
    "Perú": {
        "instrumento_legal": """1. [Decreto Supremo N° DS016-2011-MINSA](https://www.digemid.minsa.gob.pe/UpLoad/UpLoaded/PDF/DS016-2011-MINSA.pdf). Reglamento para el registro, control y vigilancia sanitaria de productos farmacéuticos, dispositivos médicos y productos sanitarios.
2. [Resolución Directoral N° 025-2022-DIGEMID-DG-MINSA](https://busquedas.elperuano.pe/normaslegales/aprueban-el-listado-de-vitaminas-minerales-y-otros-nutrien-resolucion-directoral-no-025-2022-digemid-dg-minsa-2056405-1/). Listado de Vitaminas, Minerales y Otros Nutrientes Permitidos en la Fabricación de Productos Dietéticos""",
        
        "definicion_legal": """**Producto dietético**: Es aquel producto cuyo propósito es complementar la dieta normal que consiste en fuentes concentradas de nutrientes o de otras sustancias que tengan un efecto nutricional o fisiológico, en forma simple o combinada y dosificada. Solo se emplean por vía oral *(Según el anexo nro. 1 del Glosario de Términos y Definiciones del Decreto Supremo 016-2011-MINSA)*.""",
        "categoria_regulatoria": "Medicamento",
        "proceso_autorizacion": """Los productos dietéticos se encuentran descritos en la regulación de productos farmacéuticos en el Capítulo IV (Artículos 92 - 100)."""
    
    },

    "El Salvador": {
        "instrumento_legal": """1. Artículos 29 Y 31 del [Decreto N° 1008 Ley de Medicamentos](https://alertas.directoriolegislativo.org/wp-content/uploads/2021/04/ley_de_medicamentos.pdf)
2. Artículo 21 del [Decreto N° 245 Reglamento de la Ley de Medicamentos](http://asp.salud.gob.sv/regulacion/pdf/reglamento/reglamento_ley_medicamentos.pdf)
3. Reglamento Técnico Salvadoreño [(RTS) 67.06.02:22](https://osartec.gob.sv/download/6946/) Alimentos para dietas especiales, suplementos nutricionales y probióticos.

**Nota importante**: El Poder Ejecutivo publicó la versión del Diario Oficial en la cual se [promulgó el Reglamento Técnico Salvadoreño (RTS) 67.06.02:22](https://alertas-v2.directoriolegislativo.org/fzjyd3jrgcq6o5zj9vftjls7_13-12-2023.pdf#page=36) sobre Alimentos para regímenes especiales, suplementos nutricionales y probióticos: Clasificación, características, requisitos de registro sanitario y etiquetado. Esta normativa establece las especificaciones técnicas y requisitos de registro sanitario y etiquetado de estos productos. Luego de su periodo en consulta pública, se hicieron ciertas modificaciones, especialmente en el apartado de suplementos. Entrará en vigencia el 13 de diciembre de 2024.

Con respecto a su [versión en consulta](https://alertas.directoriolegislativo.org/wp-content/uploads/2022/09/RTS-APRE-SUPLE-PROBIO_-VF-30092022.pdf), iniciada en septiembre de 2022, se destacan los siguientes cambios:
- Se incorpora la definición: **Declaraciones de propiedades** como cualquier representación que afirme, sugiera o implique que un alimento tiene cualidades especiales por su origen, propiedades nutritivas, naturaleza, elaboración, composición u otra cualidad cualquiera.
- Dentro de las especificaciones de los suplementos nutricionales, se incorpora que **deben ser de venta libre o sin receta médica**.
- Con respecto al etiquetado de los suplementos: se incorpora que se establezca su intención de uso, como incrementar o complementar la ingesta dietética y promover funciones fisiológicas de personas sanas.
- Se podrá realizar **publicidad de suplementos nutricionales y probióticos** en su empaque, siempre que sea visible y no implique una afectación a la integridad de éste.
- Se excluyen del cumplimiento de los requisitos de etiquetado los alimentos para regímenes especiales que sean **fabricados en el país para su comercialización exclusiva en el exterior**.
- Se amplió la entrada en vigencia de 6 (borrador) a 12 meses (documento oficial) después de la fecha de su publicación en el Diario Oficial.

Actualmente la categoría está regulada en el ámbito de los medicamentos por la Dirección Nacional de Medicamentos, en virtud de la Ley de Medicamentos. Con esta propuesta, se pretende que bajo la misma autoridad, pueda haber una regulación con reglas específica para la categoría.""",
        
        "definicion_legal": """**Suplemento nutricional**: sustancia o mezcla de sustancias destinadas a ser ingeridas por la vía oral para complementar los nutrientes presentes normalmente en los alimentos, éstas pueden ser vitaminas, minerales, aminoácidos, carbohidratos, proteínas, grasas o mezclas de estas sustancias con extractos de origen vegetal, animal o enzimas, excepto hormonas y la combinación de hormonas con vitaminas. El término es sinónimo de suplemento nutritivo, suplemento dietético y suplemento vitamínico. *(Numeral 4.15. del Reglamento Técnico Salvadoreño (RTS) 67.06.02:22)*

**Suplementos para deportistas**: aquellos productos formulados para satisfacer requerimientos de individuos sanos, en especial de aquellos que realicen ejercicios físicos pesados y prolongados. Estos suplementos estarán compuestos por un ingrediente, sustancia o mezcla de éstas. Se les podrá adicionar uno o más nutrientes, como hidratos de carbono, proteínas, vitaminas, minerales y otros componentes presentes naturalmente en los alimentos, tales como cafeína o aquellos expresamente autorizados en el presente instrumento. En ellos no se podrá incorporar, solos ni en asociación, hormonas o compuestos con efecto anabolizante. Tampoco se les podrá incorporar sustancias con acción estimulante sobre el sistema nervioso, salvo aquellas que estén expresamente autorizadas y dentro de los límites permitidos para este tipo de productos en este Reglamento. Estos productos no se constituyen ni alimentos, ni medicamentos. Deben ser comercializados y presentados en forma de tabletas, cápsulas, polvo, soluciones, geles, gomitas, entre otros. *(Numeral 4.16. del Reglamento Técnico Salvadoreño (RTS) 67.06.02:22)*

**Definición previa en el Reglamento de la Ley de Medicamentos**: Suplemento nutricional: Sustancia o mezcla de sustancias destinadas a ser ingeridas por la vía oral para complementar los nutrientes presentes normalmente en los alimentos, éstas pueden ser vitaminas, minerales, aminoácidos, carbohidratos, proteínas, grasas o mezclas de estas sustancias con extractos de origen vegetal, animal o enzimas, excepto hormonas y su combinación con vitaminas. El término es sinónimo de complemento alimenticio, suplemento nutritivo, suplemento dietético y suplemento vitamínico *(Numeral 43 del Artículo 3 del [Decreto N° 245 Reglamento de la Ley de Medicamentos](http://asp.salud.gob.sv/regulacion/pdf/reglamento/reglamento_ley_medicamentos.pdf))*.""",
        "categoria_regulatoria": "Categoría Intermedia/Medicamento",
        "proceso_autorizacion": """Corresponde a la DNM el registro sanitario de los suplementos nutricionales (Numeral 8. del Reglamento Técnico Salvadoreño [(RTS) 67.06.02:22](https://osartec.gob.sv/download/6946/))

Antes de Diciembre 2023, cuando se publicó el RTS para Suplementos, algunos suplementos nutricionales podían ser registrados bajo la categoria de alimentos, porque no tenían un marco regulatorio específico definido, por lo que, en principio, estos se tenían que ajustar a la regulación de etiquetado de alimentos preenvasados y de aditivos alimentarios.

La clasificación de suplementos nutricionales responde a una consulta de clasificación (evaluación caso-por-caso) en la que la Unidad de Alimentos y Bebidas de Dirección de Salud Ambiental (DISAM) determinará la pertenencia o no del producto al área de sus competencias.

A partir de Diciembre de 2024, la clasificación de los suplementos nutricionales, se realiza de acuerdo a los criterios del Numeral 8. del Reglamento Técnico Salvadoreño [(RTS) 67.06.02:22](https://osartec.gob.sv/download/6946/)

Por otra parte, de acuerdo con el Artículo 21 del [Decreto N° 245 Reglamento de la Ley de Medicamentos](http://asp.salud.gob.sv/regulacion/pdf/reglamento/reglamento_ley_medicamentos.pdf) los suplementos nutricionales se encuentran ubicados bajo la categoría de productos farmaceuticos, los cuales se los define como "sustancias de origen natural, sintético, semisintético o mezcla de ellas, con forma farmacéutica definida, empleada para prevenir, diagnosticar, tratar enfermedades o modificar una función fisiológica en los seres humanos" (Númeral 32 del Decreto N° 245). Estos productos deben ser registrados ante la Dirección Nacional de Medicamentos del Ministerio de Salud.

Cabe destacar que, aunque los suplementos nutricionales estan ubicados bajo la categoría de productos farmacéuticos, estos no deben ostentar propiedades terapeuticas."""
    },

    "Alianza del Pacífico": {
   "instrumento_legal": """Las Partes acuerdan que en caso de que se modifiquen sus definiciones nacionales, así como las declaraciones de propiedades nutricionales y saludables, cuando corresponda, se considerarán entre otras, las mejores prácticas internacionales para dichas modificaciones.""",
   
   "definicion_legal": """**Suplemento alimenticio**: Las Partes definen como suplemento alimenticio a los productos que:
a) Sean elaborados especialmente para incrementar, adicionar o complementar la alimentación normal o diaria con efecto nutricional o fisiológico.
b) Puedan utilizar vitaminas, minerales y otros ingredientes alimentarios y no se podrán utilizar sustancias con acción farmacológica o terapéutica de acuerdo a su dosis.
c) Sean de consumo exclusivo por vía oral y pueden ser presentados en forma farmacéutica.

Las Partes acuerdan que en caso de que se modifiquen sus definiciones nacionales, así como las declaraciones de propiedades nutricionales y saludables, cuando corresponda, se considerarán entre otras, las mejores prácticas internacionales para dichas modificaciones.""",
        "categoria_regulatoria": "Categoría Intermedia",
        "proceso_autorizacion": """Las Partes se comprometen a armonizar los requisitos legales exigidos y los tiempos del trámite de la autorización sanitaria de suplementos alimenticios, así como la vigencia de la misma, a través del Grupo de Trabajo que será establecido en este Anexo.

        Las Partes acuerdan que los suplementos alimenticios son productos que se pueden vender libremente en cualquier establecimiento a través de sus canales de distribución autorizados para estos efectos."""
    }
}

def mostrar_comparacion_regulatoria():
    """Muestra la interfaz de comparación regulatoria"""
    st.header("🏛️ Comparación de Marco Regulatorio")
    st.markdown("### Compara las regulaciones de suplementos entre países de América Latina")
    
    # Controles de selección
    col1, col2 = st.columns([1, 1])
    
    with col1:
        paises_seleccionados = st.multiselect(
            "🌎 Seleccionar países a comparar:",
            PAISES_DISPONIBLES,
            default=["Argentina", "Brasil"],
            max_selections=4,  # Limitar para mejor visualización
            key="paises_comparacion"
        )
    
    with col2:
        categoria_seleccionada = st.selectbox(
            "📋 Categoría a comparar:",
            list(CATEGORIAS_REGULATORIAS.keys()),
            key="categoria_comparacion"
        )
    
    if not paises_seleccionados:
        st.warning("⚠️ Selecciona al menos un país para la comparación")
        return
    
    # Obtener datos regulatorios
    datos_regulatorios = extraer_info_regulatoria_pdf()
    
    # Mostrar comparación
    st.markdown("---")
    
    # Obtener subcategorías de la categoría seleccionada
    subcategorias = CATEGORIAS_REGULATORIAS[categoria_seleccionada]
    
    for subcategoria_nombre, subcategoria_key in subcategorias.items():
        st.subheader(f"📊 {subcategoria_nombre}")
        
        # Crear columnas para cada país seleccionado
        cols = st.columns(len(paises_seleccionados))
        
        for idx, pais in enumerate(paises_seleccionados):
            with cols[idx]:
                st.markdown(f"""
                <div class="country-header">
                    🏴 {pais}
                </div>
                """, unsafe_allow_html=True)
                
                # Obtener información del país
                if pais in datos_regulatorios and subcategoria_key in datos_regulatorios[pais]:
                    info = datos_regulatorios[pais][subcategoria_key]
                    # Usar st.markdown para renderizar los hipervínculos
                    st.markdown(info, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="regulatory-item">
                        ℹ️ Información no disponible
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
    
    # Botón de exportación
    if st.button("📥 Exportar Comparación", key="export_comparacion"):
        # Crear DataFrame para exportar
        export_data = []
        for subcategoria_nombre, subcategoria_key in subcategorias.items():
            row = {"Aspecto": subcategoria_nombre}
            for pais in paises_seleccionados:
                if pais in datos_regulatorios and subcategoria_key in datos_regulatorios[pais]:
                    row[pais] = datos_regulatorios[pais][subcategoria_key]
                else:
                    row[pais] = "No disponible"
            export_data.append(row)
        
        df_export = pd.DataFrame(export_data)
        csv = df_export.to_csv(index=False)
        st.download_button(
            label="📄 Descargar CSV",
            data=csv,
            file_name=f"comparacion_regulatoria_{categoria_seleccionada.replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

def mostrar_analisis_ingrediente(df, df_referencias, ingrediente):
    """Muestra análisis detallado de un ingrediente específico"""
    df_ingrediente = df[df['ingrediente'] == ingrediente].copy()
    
    if df_ingrediente.empty:
        st.warning(f"No se encontraron datos para {ingrediente}")
        return
    
    # Información básica
    tipo_ingrediente = df_ingrediente.iloc[0]['tipo']
    unidad = df_ingrediente.iloc[0]['unidad']
    
    st.subheader(f"📊 Análisis: {ingrediente} ({tipo_ingrediente})")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Gráfico de rangos
        fig_rangos = crear_grafico_comparacion_rangos(df, ingrediente)
        if fig_rangos:
            st.plotly_chart(fig_rangos, use_container_width=True)
    
    with col2:
        # Estadísticas del ingrediente
        establecidos = df_ingrediente['establecido'].sum()
        total_paises = len(df_ingrediente)
        
        st.markdown("### 📈 Estadísticas")
        st.write(f"**Países con regulación:** {establecidos}/{total_paises}")
        st.write(f"**Unidad:** {unidad}")
        
        if establecidos > 0:
            df_establecidos = df_ingrediente[df_ingrediente['establecido'] == True]
            
            # Verificar si hay valores mínimos válidos
            valores_minimos_validos = df_establecidos['minimo'].dropna()
            valores_maximos_validos = df_establecidos['maximo'].dropna()
            
            if len(valores_minimos_validos) > 0 and len(valores_maximos_validos) > 0:
                min_global = valores_minimos_validos.min()
                max_global = valores_maximos_validos.max()
                st.write(f"**Rango global:** {min_global:.3f} - {max_global:.3f} {unidad}")
            
            # Categorías de regulación
            categorias = df_establecidos['categoria_regulacion'].value_counts()
            st.write("**Categorías:**")
            for cat, count in categorias.items():
                st.write(f"• {cat}: {count}")
    
    # Tabla detallada del ingrediente con referencias
    st.markdown("### 📋 Detalle por País")
    
    # Enriquecer con referencias
    df_ingrediente_enriquecido = enriquecer_con_referencias(df_ingrediente, df_referencias)
    
    # Opciones de visualización
    col_ref1, col_ref2 = st.columns(2)
    with col_ref1:
        mostrar_refs_detalle = st.checkbox("📖 Mostrar descripciones de referencias", value=True, key="refs_ingrediente")
    
    with col_ref2:
        mostrar_valor_original = st.checkbox("📄 Mostrar valor original", value=False, key="valor_original_ingrediente")
    
    # Preparar columnas a mostrar
    columnas_base = ['pais', 'minimo', 'maximo', 'establecido', 'categoria_regulacion', 'referencias']
    
    if mostrar_refs_detalle:
        columnas_base.append('descripcion_referencias')
    
    if mostrar_valor_original:
        columnas_base.append('valor_original')
    
    df_display = df_ingrediente_enriquecido[columnas_base].copy()
    
    # Configurar columnas
    column_config = {
        'pais': 'País',
        'minimo': st.column_config.NumberColumn('Mínimo', format="%.3f"),
        'maximo': st.column_config.NumberColumn('Máximo', format="%.3f"),
        'establecido': st.column_config.CheckboxColumn('Establecido'),
        'categoria_regulacion': 'Categoría',
        'referencias': 'Ref #'
    }
    
    if mostrar_refs_detalle:
        column_config['descripcion_referencias'] = st.column_config.TextColumn('Descripción Referencias', width='large')
    
    if mostrar_valor_original:
        column_config['valor_original'] = 'Valor Original'
    
    st.dataframe(
        df_display,
        use_container_width=True,
        column_config=column_config
    )
    
    # Mostrar panel de referencias específicas si hay alguna
    referencias_unicas = df_ingrediente[df_ingrediente['referencias'].notna()]['referencias'].unique()
    referencias_validas = []
    
    for ref in referencias_unicas:
        if pd.notna(ref) and str(ref).strip() not in ['nan', 'None', '']:
            referencias_validas.append(str(ref).strip())
    
    if len(referencias_validas) > 0:
        with st.expander("🔍 Ver Referencias Detalladas"):
            for ref_str in referencias_validas:
                refs = ref_str.split(',')
                for ref in refs:
                    ref = ref.strip()
                    if ref == '' or ref in ['nan', 'None']:
                        continue
                        
                    ref_info = df_referencias[
                        (df_referencias['referencia'] == ref) & 
                        (df_referencias['tipo'] == tipo_ingrediente)
                    ]
                    if not ref_info.empty:
                        st.markdown(f"**[{ref}]** {ref_info.iloc[0]['descripcion']}")
                    else:
                        st.markdown(f"**[{ref}]** ⚠️ Referencia no encontrada en tipo {tipo_ingrediente}")
                        # Debug info
                        st.caption(f"Buscando: ref='{ref}', tipo='{tipo_ingrediente}'")

def main():
    # Título principal
    st.title("Dashboard Regulaciones de Suplementos en América Latina")
    
    # Crear pestañas
    tab1, tab2 = st.tabs(["🧪 Análisis por Ingrediente", "🏛️ Comparación Regulatoria"])
    
    with tab1:
        st.markdown("### Análisis por Ingrediente")
        st.markdown("---")
        
        # Cargar datos
        df, df_referencias = cargar_datos()
        
        # Sidebar para filtros (simplificado)
        st.sidebar.header("🔍 Filtros - Análisis Ingredientes")
        
        # Mostrar métricas básicas en sidebar
        st.sidebar.markdown("### 📊 Resumen General")
        st.sidebar.metric("Total Países", df['pais'].nunique())
        st.sidebar.metric("Total Ingredientes", df['ingrediente'].nunique())
        
        # Filtros adicionales opcionales
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🎯 Filtros Adicionales (Opcional)")
        
        tipos_disponibles = sorted(df['tipo'].unique())
        tipos_seleccionados = st.sidebar.multiselect(
            "Filtrar por Tipo:",
            tipos_disponibles,
            default=tipos_disponibles,
            key="tipos_ingredientes"
        )
        
        # Aplicar filtro de tipo si se selecciona
        if tipos_seleccionados:
            df_filtrado = df[df['tipo'].isin(tipos_seleccionados)]
        else:
            df_filtrado = df
        
        # Selector principal de ingrediente
        ingredientes_disponibles = sorted(df_filtrado['ingrediente'].unique())
        
        if not ingredientes_disponibles:
            st.error("No hay ingredientes disponibles con los filtros seleccionados")
            return
        
        ingrediente_analisis = st.selectbox(
            "🔬 Seleccionar ingrediente para análisis:",
            ingredientes_disponibles,
            key="ingrediente_analisis"
        )
        
        # Mostrar análisis del ingrediente seleccionado
        if ingrediente_analisis:
            mostrar_analisis_ingrediente(df, df_referencias, ingrediente_analisis)
            
            # Botón de descarga específico para el ingrediente
            df_ingrediente_export = df[df['ingrediente'] == ingrediente_analisis]
            csv = df_ingrediente_export.to_csv(index=False)
            st.download_button(
                label=f"📥 Descargar datos de {ingrediente_analisis} (CSV)",
                data=csv,
                file_name=f"suplemento_{ingrediente_analisis.replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with tab2:
        mostrar_comparacion_regulatoria()

if __name__ == "__main__":
    main()