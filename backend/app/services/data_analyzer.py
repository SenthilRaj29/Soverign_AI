import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List

class PythonDataAnalyzer:
    def __init__(self, temp_dir: str = "./sandbox"):
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)

    def analyze_sensor_csv(
        self,
        file_path: str,
        temp_threshold: float = 85.0,
        vibration_threshold: float = 4.5
    ) -> Dict[str, Any]:
        df = pd.read_csv(file_path)
        
        # Calculate summary metrics
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        summary_stats = df[numeric_cols].describe().to_dict()

        # Identify threshold violations if temperature or vibration present
        anomalies = []
        threshold_violations_count = 0

        for idx, row in df.iterrows():
            row_anomaly = {}
            if "temperature" in row and row["temperature"] > temp_threshold:
                row_anomaly["temperature"] = float(row["temperature"])
            if "vibration" in row and row["vibration"] > vibration_threshold:
                row_anomaly["vibration"] = float(row["vibration"])
            
            if row_anomaly:
                threshold_violations_count += 1
                anomalies.append({
                    "row_index": int(idx),
                    "timestamp": str(row.get("timestamp", idx)),
                    "violations": row_anomaly
                })

        # Calculate rolling averages if timestamp & temp/vibration present
        rolling_metrics = {}
        if "temperature" in df.columns:
            df["temp_rolling_avg"] = df["temperature"].rolling(window=5, min_periods=1).mean()
            rolling_metrics["temp_rolling_max"] = float(df["temp_rolling_avg"].max())
            rolling_metrics["temp_mean"] = float(round(df["temperature"].mean(), 2))
            rolling_metrics["temp_max"] = float(df["temperature"].max())

        if "vibration" in df.columns:
            df["vibration_rolling_avg"] = df["vibration"].rolling(window=5, min_periods=1).mean()
            rolling_metrics["vibration_rolling_max"] = float(df["vibration_rolling_avg"].max())
            rolling_metrics["vibration_mean"] = float(round(df["vibration"].mean(), 2))
            rolling_metrics["vibration_max"] = float(df["vibration"].max())

        return {
            "total_records": len(df),
            "numeric_columns": numeric_cols,
            "metrics": rolling_metrics,
            "threshold_violations_detected": threshold_violations_count > 0,
            "total_violations": threshold_violations_count,
            "anomalies_sample": anomalies[:5], # top 5 samples
            "summary_stats": summary_stats
        }
