#!/usr/bin/env python

import os
from flask import Flask, render_template, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd

# Initialize Flask app
app = Flask(__name__)

# Detect if running inside Docker/Cloud Run
if os.getenv("GAE_ENV", "").startswith("standard") or os.getenv("CLOUD_RUN"):
    FIREBASE_KEY_PATH = "/app/firebase-key.json"  # Cloud Run Path
else:
    FIREBASE_KEY_PATH = os.path.join(os.getcwd(), "firebase-key.json")  # Local Path

# Initialize Firebase only if not already initialized
if not firebase_admin._apps:
    if os.path.exists(FIREBASE_KEY_PATH):
        cred = credentials.Certificate(FIREBASE_KEY_PATH)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully!")
    else:
        print(f"❌ Error: Firebase key file not found at {FIREBASE_KEY_PATH}")
        exit(1)

# Firestore client
db = firestore.client()

@app.route('/')
def index():
    """Render the main page with the chart."""
    return render_template('index.html')

@app.route('/chart-data', methods=['GET'])
def get_chart_data():
    """Fetch data from Firestore (no local cache) and return it as JSON."""
    print("✅ Entering /chart-data route")
    try:
        # Fetch raw data from Firestore every time
        collection_ref = db.collection("Indices").document("BTC_Mag7_Index").collection("DailyData")
        docs = collection_ref.stream()

        # Convert Firestore docs to DataFrame
        data = []
        for doc in docs:
            doc_data = doc.to_dict()
            data.append(doc_data)

        df = pd.DataFrame(data)
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

        # Filter out incomplete data if needed
        valid_start_date = df[['BTC-USD','TSLA']].dropna().index.min()
        df = df[df.index >= valid_start_date]

        # Forward-fill missing values for MAG7 stocks
        df.fillna(method='ffill', inplace=True)

        # Normalize prices to start at 100
        normalized_data = df / df.iloc[0] * 100

        # Apply weights
        weights = {
            'BTC-USD': 0.5,
            'MSFT': 0.1,
            'AAPL': 0.1,
            'GOOGL': 0.1,
            'AMZN': 0.1,
            'META': 0.05,
            'NVDA': 0.05
        }
        df['BTC_Mag7_Index'] = (normalized_data * pd.Series(weights)).sum(axis=1)

        # Smooth with a 7-day moving average
        df['Smoothed_Index'] = df['BTC_Mag7_Index'].rolling(window=7).mean()

        # Calculate multiple MAs
        df['MA200'] = df['Smoothed_Index'].rolling(window=200).mean()
        df['MA150'] = df['Smoothed_Index'].rolling(window=150).mean()
        df['MA100'] = df['Smoothed_Index'].rolling(window=100).mean()

        # Calculate EMAs
        df['EMA200'] = df['Smoothed_Index'].ewm(span=200, adjust=False).mean()
        df['EMA150'] = df['Smoothed_Index'].ewm(span=150, adjust=False).mean()
        df['EMA100'] = df['Smoothed_Index'].ewm(span=100, adjust=False).mean()

        # Drop rows with NaN in critical columns
        df.dropna(subset=['Smoothed_Index'], inplace=True)

        # Build JSON response
        response = {
            'dates': df.index.strftime('%Y-%m-%d').tolist(),
            'index_values': [None if pd.isna(x) else x for x in df['Smoothed_Index']],
            'ma200': [None if pd.isna(x) else x for x in df['MA200']],
            'ma150': [None if pd.isna(x) else x for x in df['MA150']],
            'ma100': [None if pd.isna(x) else x for x in df['MA100']],
            'ema200': [None if pd.isna(x) else x for x in df['EMA200']],
            'ema150': [None if pd.isna(x) else x for x in df['EMA150']],
            'ema100': [None if pd.isna(x) else x for x in df['EMA100']],
        }

        # Add known BTC tops/bottoms
        cycle_tops = ['2017-12-17', '2021-11-10']
        cycle_bottoms = ['2018-12-15', '2022-06-18']

        response['tops'] = [
            {'date': top, 'value': df.loc[top, 'BTC_Mag7_Index']}
            for top in cycle_tops if top in df.index
        ]
        response['bottoms'] = [
            {'date': bottom, 'value': df.loc[bottom, 'BTC_Mag7_Index']}
            for bottom in cycle_bottoms if bottom in df.index
        ]

        print("✅ Returning JSON response:", response)
        return jsonify(response)

    except Exception as e:
        print("❌ Error in /chart-data:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run on port 8080 for Cloud Run
    app.run(debug=True, host='0.0.0.0', port=8080)
