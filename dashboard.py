import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Suplementos América Latina",
    page_icon="💊",
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
</style>
""", unsafe_allow_html=True)

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
    st.title("💊 Dashboard Regulaciones de Suplementos en América Latina")
    st.markdown("### 🧪 Análisis por Ingrediente")
    st.markdown("---")
    
    # Cargar datos
    df, df_referencias = cargar_datos()
    
    # Sidebar para filtros (simplificado)
    st.sidebar.header("🔍 Filtros")
    
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
        default=tipos_disponibles
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

if __name__ == "__main__":
    main()