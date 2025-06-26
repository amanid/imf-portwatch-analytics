
# 🌐 IMF PortWatch Analytics Dashboard

A production-grade analytics dashboard to explore global maritime trade patterns using real-time open data from the **IMF PortWatch** initiative. This app offers a seamless view into port-level activity and trends across cargo types, geographies, and time, with forecasting and anomaly detection capabilities built-in.

---

## 🚀 Features

- 📊 **Interactive Dashboard** built with [Dash](https://dash.plotly.com/)
- 🧮 **Dynamic KPIs** with anomaly detection and weekly deltas
- 📍 **Multi-port filtering** and global port mapping
- 🔁 **2-Year Time Series + Forecasts** using Prophet and ARIMA
- 📈 **Top ports**, **country pies**, and **traffic heatmaps**
- 📤 **CSV/XLSX Export** + Auto-email delivery (optional)
- 🔌 Fully driven by **live open data** via ArcGIS API

---

## 📂 Project Structure

```bash
imf-portwatch-analytics/
├── app.py                     # Main Dash app
├── requirements.txt           # Dependencies
├── README.md                  # You're here
├── src/
│   ├── data_loader.py         # Fetching + caching data from ArcGIS API
│   ├── preprocess.py          # Data cleaning and feature engineering
│   ├── analytics.py           # KPI calculations, anomaly detection, forecasts
│   └── visualizations.py      # Charting logic using Plotly
└── assets/                    # Optional CSS or images
```

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/amanid/imf-portwatch-analytics.git
cd imf-portwatch-analytics

# Set up a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install required packages
pip install -r requirements.txt

# Run the app
python app.py
```

---

## 🌍 Data Source

Data is pulled from the official IMF PortWatch ArcGIS dataset:  
[IMF PortWatch Open Data CSV](https://opendata.arcgis.com/api/v3/datasets/75619cb86e5f4beeb7dab9629d861acf_0/downloads/data?format=csv&spatialRefId=4326&where=1=1)

---

## 🧠 Forecasting Models

The dashboard supports switching between:

- **Prophet** (Facebook’s time series model)
- **ARIMA** (Statsmodels-based)

You can select the model type from the dropdown in the Forecast tab.

---

## 📬 Email Automation (Optional)

To enable scheduled exports via email:
1. Add your email configuration in a `.env` file
2. Schedule jobs using `apscheduler` or `cron`
3. Trigger `send_email_with_attachment()` from a custom script

---

## 📸 Screenshots

![Dashboard Screenshot](assets/dashboard_screenshot.png)

---

## 🤝 Contributing

Contributions are welcome! Feel free to fork, open issues, or submit pull requests to improve the project.

---

## 📄 License

MIT License

---

## 👨‍💻 Author

**Amani Dieudonné Konan**  
GitHub: [@amanid](https://github.com/amanid)  
LinkedIn: [linkedin.com/in/amanikonan](https://linkedin.com/in/amanikonan)

