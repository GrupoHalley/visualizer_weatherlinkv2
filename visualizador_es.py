# streamlit_app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from weatherlinkv2 import WeatherLinkAPI, parse_weather_data
import time

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

st.set_page_config(page_title="Estaciones Meteorológicas", layout="wide")

# Configurar auto-refresh
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

# Auto-refresh
if st.button("🔄 Actualizar datos"):
    # Limpiar el área de contenido
    st.empty()
    
if stations:  # Solo procesar si hay estaciones seleccionadas
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
    else:
        st.warning("Selecciona al menos una estación para visualizar los datos")
        st.stop()

    # Visualizaciones
    col1, col2 = st.columns(2)
    
    with col1:
        fig_temp = px.line(df, x=df.index, y='temperature_c', color='station_name', 
                          title='Temperatura (°C)',
                          labels={'index': 'Tiempo', 'temperature_c': 'Temperatura (°C)', 'station_name': 'Estación'})
        st.plotly_chart(fig_temp, use_container_width=True, key="temp_chart")
    
    with col2:
        fig_humidity = px.line(df, x=df.index, y='humidity_pct', color='station_name', 
                              title='Humedad (%)',
                              labels={'index': 'Tiempo', 'humidity_pct': 'Humedad (%)', 'station_name': 'Estación'})
        st.plotly_chart(fig_humidity, use_container_width=True, key="humidity_chart")
    
    # Segunda fila para calidad del aire
    col3, col4 = st.columns(2)
    
    with col3:
        fig_pm25 = px.line(df, x=df.index, y='pm25_ugm3', color='station_name', 
                          title='PM2.5 (μg/m³)',
                          labels={'index': 'Tiempo', 'pm25_ugm3': 'PM2.5 (μg/m³)', 'station_name': 'Estación'})
        st.plotly_chart(fig_pm25, use_container_width=True, key="pm25_chart")
    
    with col4:
        fig_pm1 = px.line(df, x=df.index, y='pm1_ugm3', color='station_name', 
                         title='PM1 (μg/m³)',
                         labels={'index': 'Tiempo', 'pm1_ugm3': 'PM1 (μg/m³)', 'station_name': 'Estación'})
        st.plotly_chart(fig_pm1, use_container_width=True, key="pm1_chart")

else:
    st.info("👆 Selecciona al menos una estación en la barra lateral para comenzar a visualizar los datos.")