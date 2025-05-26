# AI-Based Fraud Detection System for Banks

📍 **Live Demo:**  
👉 [Click here to try the app](https://banking-fraud-detection-system-6t8aztranactionhxcqctmjzdeuhjj.streamlit.app/)

An interactive web application that detects fraudulent financial transactions using machine learning, Designed for banking staff to review, upload, and manage transactions with customer verification via email.

---

## 💡 Overview

This system empowers banks to:
- Detect fraud using a pre-trained ML model
- View statistics through a dashboard
- Allow customers to confirm suspicious activity via email
- Upload CSV files for batch transaction analysis
- Store data securely in a cloud-hosted database

---

## 🔍 Features

- 🧠 ML-based fraud prediction using a trained `.pkl` model  
- 📊 KPI dashboard: Fraudulent, Legitimate, and Total counts  
- 📂 Upload CSV files — automatically classify transactions using the ML model and insert them into the database. 
- 🔐 Secure login with OTP via email  
- 📧 YES/NO confirmation emails for customers  
- 🎯 Filter and search transactions manually  
- ☁️ Hosted using **Streamlit Cloud** for the app and **Railway** for the MySQL database.

---

## ⚙️ Technologies Used

- `Python`, `Streamlit` — Web interface  
- `scikit-learn`, `joblib` — ML model  
- `MySQL` (via Railway) — Database  
- `Yagmail`, `SMTP` — Email/OTP services  
- `Altair`, `Plotly`, `Matplotlib` — Data visualization
- `Streamlit Cloud` and `Railway` — App and database deployment

---

## 🚀 Deployment

The application is deployed using:

- **Streamlit Cloud** for hosting the web interface  
- **Railway** for hosting the MySQL database

### 🛠️ Database Connection Example

To connect your app to the Railway-hosted MySQL database, use:

```python
pymysql.connect(
    host="your_railway_host",
    user="your_railway_user",
    password="your_password",
    database="your_database",
    port=your_railway_port
)
