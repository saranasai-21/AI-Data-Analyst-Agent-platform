# ⚡ EKPC Load Forecasting using Bidirectional LSTM

An advanced deep learning-based electricity load forecasting system developed using **TensorFlow, Bidirectional LSTM, and Streamlit**.
This project predicts next-hour electricity demand using historical load patterns and time-series forecasting techniques.

# 📌 Project Overview

Electricity demand forecasting is critical for:

- Power system planning
- Load balancing
- Energy optimization
- Grid stability
- Smart energy management

This project uses a **Bidirectional Long Short-Term Memory (BiLSTM)** neural network to accurately forecast electricity load based on historical consumption data.
The system also includes a professional **Streamlit dashboard** for real-time forecasting and visualization.

# Deep Learning Architecture

The forecasting model uses:

- Bidirectional LSTM Layers
- Dense Neural Layers
- Dropout Regularization
- Adam Optimizer
- EarlyStopping

# 📊 Feature Engineering

The model was trained using:

- Historical Load Values (EKPC_MW)
- Rolling Mean (24 Hours)
- Cyclical Hour Encoding (Hour_sin, Hour_cos)

# 📈 Model Performance

| Metric | Value |
|---|---|
| MAE | 29.31 |
| MSE | 1505.41 |
| RMSE | 38.80 |
| R² Score | 0.9905 |
| Accuracy (Within 10%) | 98%+ |

# Interpretation

- The model achieves very high forecasting accuracy.
- R² Score of 0.9905 indicates excellent learning capability.
- Low MAE and RMSE values show minimal prediction error.
- Accuracy within 10% demonstrates reliable real-world forecasting performance.

# Technologies Used

- Python
- TensorFlow / Keras
- NumPy
- Pandas
- Scikit-learn
- Streamlit
- Joblib

# 🚀 Streamlit Application

The Streamlit dashboard allows users to:

- Enter recent electricity load values
- Predict the next-hour electricity demand
- View model performance metrics
- Perform real-time forecasting interactively

## Run the Project
```text
Install Requirements
- pip install -r requirements.txt
Run Streamlit App
- streamlit run app.py
```
# 📂 Project Structure

```text
EKPC Load Forecasting using BiLSTM
│
├── app.py
├── train.py
├── ekpc_usage.csv
├── load_forecasting_model.keras
├── scaler.save
├── metrics.save
├── requirements.txt
└── README.md
```

Developed as a deep learning and time-series forecasting project using BiLSTM architecture for electricity demand prediction.

# 🌐 Live Demo

Streamlit App: https://ai-load-forecasting-using-lstm.streamlit.app

# Screenshot

<img width="1374" height="830" alt="Screenshot 2026-05-22 023404" src="https://github.com/user-attachments/assets/8e22f1d0-1c98-455a-91fc-484d30d4706b" />
