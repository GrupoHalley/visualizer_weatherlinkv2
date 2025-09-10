# 🌤️ Davis Weather Stations Visualizer

Interactive web application to visualize real-time meteorological and air quality data from Davis WeatherLink stations.

## 📋 Features

- **Real-time visualization** of multiple weather stations
- **Interactive charts** for temperature, humidity, PM2.5 and PM1
- **Flexible time selection**: last N hours or specific date range
- **Station comparison** on the same scales and timeframes
- **Intuitive interface** built with Streamlit

## ☁️ Monitored Variables

- **🌡️ Temperature (°C)**: Ambient temperature
- **💧 Humidity (%)**: Relative air humidity
- **🌫️ PM2.5 (μg/m³)**: Fine particles - air quality
- **💨 PM1 (μg/m³)**: Ultrafine particles - air quality

## 🛠️ Local Installation

### Prerequisites

- Python 3.8+
- WeatherLink API account with valid credentials

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/visualizer_weatherlinkv2.git
   cd visualizer_weatherlinkv2
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   WEATHERLINK_API_KEY=your_api_key_here
   WEATHERLINK_API_SECRET=your_api_secret_here
   ```

4. **Run the application**
   ```bash
   streamlit run visualizador_es.py
   ```

5. **Open in browser**
   
   The application will be available at `http://localhost:8501`

## 🔧 Configuration

### Environment Variables

- `WEATHERLINK_API_KEY`: Your WeatherLink API key
- `WEATHERLINK_API_SECRET`: Your WeatherLink API secret

### Stations

Stations are automatically loaded from your WeatherLink API account. Make sure your stations are configured and sending data.

## 📦 Main Dependencies

- **Streamlit**: Web application framework
- **weatherlinkv2**: Custom library for WeatherLink API
- **Plotly**: Interactive charts
- **Pandas**: Data manipulation
- **python-dotenv**: Environment variables management

## 📝 Usage

1. **Select stations**: Use the multi-select dropdown in the sidebar
2. **Configure time**: Choose between "Last hours" or "Date range"
3. **Update data**: Press the "🔄 Update data" button
4. **Visualize**: View interactive charts with data from all selected stations

## 🤝 Contributions

Contributions are welcome. Please:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

----

⭐ If you find this project useful, please give it a star on GitHub!
