import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from joblib import dump
import os

# ------------------ CONFIGURACIÓN ------------------
train_po_path = "data/Records/train_po/ECOPALtrain_po.csv"
scaler_output_path = "models/scaler/std_scaler_ECOPAL.bin"

# ------------------ CARGAR DATOS ------------------
df = pd.read_csv(train_po_path)

# Eliminar columnas no ambientales
cols_to_drop = ['spid', 'x', 'y']
env_vars = [col for col in df.columns if col not in cols_to_drop]

X = df[env_vars].copy()

# ------------------ AJUSTAR Y GUARDAR SCALER ------------------
scaler = StandardScaler()
scaler.fit(X)

# Crear carpeta si no existe
os.makedirs(os.path.dirname(scaler_output_path), exist_ok=True)

dump(scaler, scaler_output_path)
print(f"\n✅ Scaler guardado correctamente en: {scaler_output_path}")
