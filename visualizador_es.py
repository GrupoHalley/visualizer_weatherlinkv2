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

# Configuración de sensores
SENSOR_CONFIG = {
    "AirLink": {
        "sensor_type": 323,
        "data_structure_type": 17,
        "variables": ['temperature_c', 'humidity_pct', 'pm25_ugm3', 'pm1_ugm3'],
        "labels": {
            'temperature_c': 'Temperatura (°C)',
            'humidity_pct': 'Humedad (%)',
            'pm25_ugm3': 'PM2.5 (μg/m³)',
            'pm1_ugm3': 'PM1 (μg/m³)'
        }
    },
    "Vantage Vue": {
        "sensor_type": 37,
        "data_structure_type": 24,
        "variables": ['temperature_c', 'humidity_pct', 'rainfall_mm', 'wind_speed_kmh'],
        "labels": {
            'temperature_c': 'Temperatura (°C)',
            'humidity_pct': 'Humedad (%)',
            'rainfall_mm': 'Lluvia (mm)',
            'wind_speed_kmh': 'Velocidad del Viento (km/h)'
        }
    },
    "Vantage Pro2": {
        "sensor_type": 23,
        "data_structure_type": 4,
        "variables": ['temperature_out_c', 'humidity_out_pct', 'rainfall_mm', 'wind_speed_kmh'],
        "labels": {
            'temperature_out_c': 'Temperatura (°C)',
            'humidity_out_pct': 'Humedad (%)',
            'rainfall_mm': 'Lluvia (mm)',
            'wind_speed_kmh': 'Velocidad del Viento (km/h)'
        }
    }
}

# Configuración especial para estaciones específicas
STATION_SENSOR_OVERRIDE = {
    "219678": {"AirLink": {"sensor_type": 326, "data_structure_type": 17}},
    "84759": {"required_sensor": "Vantage Pro2"}  # Solo funciona con Vantage Pro2
}

# Sidebar para configuración
with st.sidebar:
    stations = st.multiselect("Seleccionar estaciones", options=station_options)
    
    # Selector de tipo de sensor
    sensor_type = st.radio(
        "Tipo de sensor",
        options=["AirLink", "Vantage Vue", "Vantage Pro2"],
        index=0,
        help="Selecciona el tipo de sensor a consultar"
    )
    
    # Seleccionar modo de consulta de tiempo
    query_mode = st.radio("Modo de consulta", ["Últimas horas", "Rango de fechas"], index=0)
    if query_mode == "Últimas horas":
        hours_back = st.number_input("Horas anteriores", min_value=1, value=24)
        # En modo "Últimas horas" siempre cargamos los datos
        load_data = True
    else:
        start_date = st.date_input("Fecha inicio", datetime.date.today() - datetime.timedelta(days=1))
        end_date = st.date_input("Fecha fin", datetime.date.today())
        # Botón para aplicar el rango de fechas
        load_data = st.button("📅 Aplicar fechas", use_container_width=True)

# Auto-refresh y botones de descarga
col_update, col_csv, col_excel = st.columns([3, 1.2, 1.2])

with col_update:
    if st.button("🔄 Actualizar datos"):
        # Limpiar el área de contenido
        st.empty()

# Preparar datos y descargas si hay estaciones seleccionadas y se debe cargar
if stations and load_data:
    # Procesar datos para obtener df
    dfs = []
    missing = []
    
    for station in stations:
        station_id = station_id_map.get(station)
        station_id_str = str(station_id)
        
        # Obtener configuración del sensor
        sensor_config = SENSOR_CONFIG[sensor_type].copy()
        
        # Verificar override para estaciones específicas
        if station_id_str in STATION_SENSOR_OVERRIDE:
            override = STATION_SENSOR_OVERRIDE[station_id_str]
            
            # Si la estación requiere un sensor específico
            if "required_sensor" in override:
                if sensor_type != override["required_sensor"]:
                    st.warning(f"⚠️ La estación {station} (ID: {station_id}) solo funciona con {override['required_sensor']}")
                    missing.append(station)
                    continue
            
            # Si hay override de parámetros para este sensor
            if sensor_type in override:
                sensor_config["sensor_type"] = override[sensor_type]["sensor_type"]
                sensor_config["data_structure_type"] = override[sensor_type]["data_structure_type"]
        
        # Obtener histórico según modo de consulta
        if query_mode == "Últimas horas":
            hist_json = api.get_historic_data(station_id=station_id_str, hours_back=int(hours_back))
        elif query_mode == "Rango de fechas":
            start_ts = int(datetime.datetime.combine(start_date, datetime.time()).timestamp())
            end_ts = int(datetime.datetime.combine(end_date, datetime.time()).timestamp())
            hist_json = api.get_historic_data(station_id=station_id_str, start_timestamp=start_ts, end_timestamp=end_ts)
        
        # Corregir timestamp con tz_offset
        if 'sensors' in hist_json:
            for sensor in hist_json['sensors']:
                if 'data' in sensor:
                    for record in sensor['data']:
                        if 'ts' in record and 'tz_offset' in record:
                            record['ts'] += record['tz_offset']

        # Parsear datos con la configuración del sensor
        df_i = parse_weather_data(
            hist_json, 
            sensor_type=sensor_config["sensor_type"], 
            data_structure_type=sensor_config["data_structure_type"]
        )
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
        
        # Preparar datos para descarga con las variables del sensor seleccionado
        selected_vars = SENSOR_CONFIG[sensor_type]["variables"]
        available_vars = [var for var in selected_vars if var in df.columns]
        download_columns = ['station_name'] + available_vars
        
        download_df = df[download_columns].copy()
        download_df.reset_index(inplace=True)
        
        # Renombrar columnas para formato Python-friendly
        rename_dict = {'ts': 'timestamp', 'station_name': 'station'}
        download_df = download_df.rename(columns=rename_dict)
        
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

if stations and load_data:
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
        )
        return fig
    
    # Obtener variables y etiquetas del sensor seleccionado
    variables = SENSOR_CONFIG[sensor_type]["variables"]
    labels = SENSOR_CONFIG[sensor_type]["labels"]
    
    # Crear gráficas dinámicamente según las variables disponibles
    col1, col2 = st.columns([1, 1], gap="medium")
    
    # Primera fila: primeras 2 variables
    with col1:
        var1 = variables[0]
        if var1 in df.columns:
            fig1 = px.line(df, x=df.index, y=var1, color='station_name', 
                          title=labels[var1],
                          labels={'index': 'Tiempo', var1: labels[var1], 'station_name': 'Estación'})
            fig1 = create_responsive_chart(fig1)
            st.plotly_chart(fig1, use_container_width=True, key=f"chart_{var1}", config={'responsive': True})
    
    with col2:
        var2 = variables[1]
        if var2 in df.columns:
            fig2 = px.line(df, x=df.index, y=var2, color='station_name', 
                          title=labels[var2],
                          labels={'index': 'Tiempo', var2: labels[var2], 'station_name': 'Estación'})
            fig2 = create_responsive_chart(fig2)
            st.plotly_chart(fig2, use_container_width=True, key=f"chart_{var2}", config={'responsive': True})
    
    # Segunda fila: últimas 2 variables
    col3, col4 = st.columns([1, 1], gap="medium")
    
    with col3:
        if len(variables) > 2:
            var3 = variables[2]
            if var3 in df.columns:
                fig3 = px.line(df, x=df.index, y=var3, color='station_name', 
                              title=labels[var3],
                              labels={'index': 'Tiempo', var3: labels[var3], 'station_name': 'Estación'})
                fig3 = create_responsive_chart(fig3)
                st.plotly_chart(fig3, use_container_width=True, key=f"chart_{var3}", config={'responsive': True})
    
    with col4:
        if len(variables) > 3:
            var4 = variables[3]
            if var4 in df.columns:
                fig4 = px.line(df, x=df.index, y=var4, color='station_name', 
                              title=labels[var4],
                              labels={'index': 'Tiempo', var4: labels[var4], 'station_name': 'Estación'})
                fig4 = create_responsive_chart(fig4)
                st.plotly_chart(fig4, use_container_width=True, key=f"chart_{var4}", config={'responsive': True})

else:
    # Mensaje de bienvenida o instrucciones según el contexto
    if not stations:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; border-radius: 10px; margin: 1rem 0;">
            <h3>🚀 ¡Bienvenido al Visualizador de Estaciones Meteorológicas!</h3>
            <p style="font-size: 1.1rem;">
                ⚙️ Selecciona al menos una estación en la barra lateral para comenzar a visualizar los datos en tiempo real.
            </p>
        </div>
        """, unsafe_allow_html=True)
    elif query_mode == "Rango de fechas" and not load_data:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; border-radius: 10px; margin: 1rem 0;">
            <p style="font-size: 1.1rem;">
                📅 Selecciona las fechas de inicio y fin, luego presiona el botón <b>'Aplicar fechas'</b> en la barra lateral para cargar los datos.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("🔄 Los datos se actualizan automáticamente al cambiar las horas anteriores. Selecciona las estaciones en la barra lateral.")

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