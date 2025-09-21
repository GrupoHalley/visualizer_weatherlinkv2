import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from weatherlinkv2 import WeatherLinkAPI, parse_weather_data
import io

API_KEY = st.secrets["WEATHERLINK_API_KEY"]
API_SECRET = st.secrets["WEATHERLINK_API_SECRET"]

# Inicializar api
api = WeatherLinkAPI(api_key=API_KEY, api_secret=API_SECRET, demo_mode=False)

# Cargar IDs y nombres de estaciones
stations_request = [{'station_name': s['station_name'], 'station_id': s['station_id']} for s in api.get_stations()]
stations_df = pd.DataFrame(stations_request, columns=['station_name', 'station_id'])
station_options = stations_df["station_name"].tolist()
station_options.sort()
station_id_map = dict(zip(stations_df["station_name"], stations_df["station_id"]))

st.set_page_config(page_title="Estaciones Meteorológicas", layout="wide", initial_sidebar_state="expanded")
st.title("🌤️ Monitoreo en Tiempo Real - Estaciones Davis")

# Sidebar para configuración
with st.sidebar:
    stations = st.multiselect("Seleccionar estaciones", options=station_options)
    # Seleccionar modo de consulta de tiempo
    query_mode = st.radio("Modo de consulta", ["Últimas horas", "Rango de fechas"], index=0)
    if query_mode == "Últimas horas":
        hours_back = st.number_input("Horas anteriores", min_value=1, value=24)
    else:
        start_date = st.date_input("Fecha inicio", datetime.date.today() - datetime.timedelta(days=1))
        end_date = st.date_input("Fecha fin", datetime.date.today())

# Auto-refresh y botones de descarga
col_update, col_csv, col_excel = st.columns([3, 1.2, 1.2])

with col_update:
    if st.button("🔄 Actualizar datos"):
        # Limpiar el área de contenido
        st.empty()

# Preparar datos y descargas si hay estaciones seleccionadas
if stations:
    # Procesar datos para obtener df
    dfs = []
    missing = []  # estaciones sin datos
    for station in stations:
        station_id = station_id_map.get(station)
        # Obtener histórico según modo de consulta
        if query_mode == "Últimas horas":
            hist_json = api.get_historic_data(station_id=str(station_id), hours_back=int(hours_back))
        elif query_mode == "Rango de fechas":
            # Convertir fechas a timestamp Unix
            start_ts = int(datetime.datetime.combine(start_date, datetime.time()).timestamp())
            end_ts = int(datetime.datetime.combine(end_date, datetime.time()).timestamp())
            hist_json = api.get_historic_data(station_id=str(station_id), start_timestamp=start_ts, end_timestamp=end_ts)
        df_i = parse_weather_data(hist_json, sensor_type=323, data_structure_type=17)
        if df_i.empty:
            missing.append(station)
            continue
        df_i["station_name"] = station
        dfs.append(df_i)
    if missing:
        st.warning(f"No hay datos disponibles para las siguientes estaciones: {', '.join(missing)}")
        if len(missing) == len(stations):
            st.stop()
    if dfs:
        df = pd.concat(dfs)
        
        # Preparar datos para descarga (solo las 4 variables principales)
        download_df = df[['station_name', 'temperature_c', 'humidity_pct', 'pm25_ugm3', 'pm1_ugm3']].copy()
        download_df.reset_index(inplace=True)
        download_df = download_df.rename(columns={
            'ts': 'timestamp',
            'station_name': 'station',
            'temperature_c': 'temperature_c',
            'humidity_pct': 'humidity_pct',
            'pm25_ugm3': 'pm25_ugm3',
            'pm1_ugm3': 'pm1_ugm3'
        })
        
        with col_csv:
            # Preparar CSV
            csv_buffer = io.StringIO()
            download_df.to_csv(csv_buffer, index=False, encoding='utf-8')
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label="📄 Descargar CSV",
                data=csv_data,
                file_name=f"weather_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col_excel:
            # Preparar Excel
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                download_df.to_excel(writer, index=False, sheet_name='weather_data')
            excel_data = excel_buffer.getvalue()
            
            st.download_button(
                label="📊 Descargar Excel",
                data=excel_data,
                file_name=f"weather_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.warning("Selecciona al menos una estación para visualizar los datos")
        st.stop()

if stations:  # Solo procesar si hay estaciones seleccionadas
    def create_responsive_chart(fig):
        fig.update_layout(
            autosize=True,
            margin=dict(l=20, r=20, t=40, b=20),
            font=dict(size=12),
            title_font_size=14,
            legend=dict(
                orientation="v",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode='x unified'
        )
        return fig
    
    # Layout responsive para las gráficas
    col1, col2 = st.columns([1, 1], gap="medium")
    
    with col1:
        fig_temp = px.line(df, x=df.index, y='temperature_c', color='station_name', 
                          title='Temperatura (°C)',
                          labels={'index': 'Tiempo', 'temperature_c': 'Temperatura (°C)', 'station_name': 'Estación'})
        fig_temp = create_responsive_chart(fig_temp)
        st.plotly_chart(fig_temp, use_container_width=True, key="temp_chart", config={'responsive': True})
    
    with col2:
        fig_humidity = px.line(df, x=df.index, y='humidity_pct', color='station_name', 
                              title='Humedad (%)',
                              labels={'index': 'Tiempo', 'humidity_pct': 'Humedad (%)', 'station_name': 'Estación'})
        fig_humidity = create_responsive_chart(fig_humidity)
        st.plotly_chart(fig_humidity, use_container_width=True, key="humidity_chart", config={'responsive': True})
    
    col3, col4 = st.columns([1, 1], gap="medium")
    
    with col3:
        fig_pm25 = px.line(df, x=df.index, y='pm25_ugm3', color='station_name', 
                          title='PM2.5 (μg/m³)',
                          labels={'index': 'Tiempo', 'pm25_ugm3': 'PM2.5 (μg/m³)', 'station_name': 'Estación'})
        fig_pm25 = create_responsive_chart(fig_pm25)
        st.plotly_chart(fig_pm25, use_container_width=True, key="pm25_chart", config={'responsive': True})
    
    with col4:
        fig_pm1 = px.line(df, x=df.index, y='pm1_ugm3', color='station_name', 
                         title='PM1 (μg/m³)',
                         labels={'index': 'Tiempo', 'pm1_ugm3': 'PM1 (μg/m³)', 'station_name': 'Estación'})
        fig_pm1 = create_responsive_chart(fig_pm1)
        st.plotly_chart(fig_pm1, use_container_width=True, key="pm1_chart", config={'responsive': True})

else:
    # Mensaje de bienvenida
    st.markdown("""
    <div style="text-align: center; padding: 2rem; border-radius: 10px; margin: 1rem 0;">
        <h3>🚀 ¡Bienvenido al Visualizador de Estaciones Meteorológicas!</h3>
        <p style="font-size: 1.1rem;">
            ⚙️ Selecciona al menos una estación en la barra lateral para comenzar a visualizar los datos en tiempo real.
        </p>
    </div>
    """, unsafe_allow_html=True)

# CSS para diseño responsive
st.markdown("""
<style>
    /* Hacer que las columnas se adapten cuando hay menos de 1100px */
    @media (max-width: 1100px) {
        .stColumn {
            width: 100% !important;
            margin-bottom: 1rem;
        }

        /* Títulos más pequeños */
        h1 {
            font-size: 1.5rem !important;
        }
        
        h3 {
            font-size: 1.2rem !important;
        }
        
        /* Alertas y warnings más compactas */
        .stAlert > div {
            font-size: 0.85rem !important;
            padding: 0.5rem !important;
        }
    }

</style>
""", unsafe_allow_html=True)