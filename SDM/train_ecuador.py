# train_ecuador.py

import pandas as pd
import geopandas as gpd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import torch

from training_helpers import train_multi_species
from losses import full_weighted_loss

# 1. Cargar datos de presencia y pseudo-ausencias
df = pd.read_csv("data/data_combinada_final.csv")
gdf = gpd.read_file("data/grid_clima.geojson")

# 2. Seleccionar variables ambientales
excluded = ['species', 'x', 'y']
features = [col for col in df.columns if col not in excluded and col in gdf.columns]

# 3. Matrices X (variables) e Y (presencia por especie)
df['coord'] = list(zip(df['x'], df['y']))
x_df = df[features].groupby(df['coord']).mean()
y_df = pd.get_dummies(df['species']).groupby(df['coord']).sum().clip(0, 1)

x = x_df.to_numpy()
y = y_df.to_numpy()

# 4. Pseudo-ausencias (background) desde la grilla
x_bg = gdf[features].dropna().to_numpy()

# 5. Normalizar
scaler = StandardScaler()
x = scaler.fit_transform(x)
x_bg = scaler.transform(x_bg)

# 6. Separar test
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

# 7. Configuración del modelo
config = {
    "random_seed_split": 42,
    "region": "ECU",
    "co_occurrence": True,
    "valavi_covariates": False,
    "num_species": y.shape[1],
    "num_covariates": x.shape[1],
    "device": "cuda" if torch.cuda.is_available() else "cpu",
    "num_layers": 4,
    "width_MLP": 512,
    "dropout": 0.01,
    "epochs": 30,
    "batch_size": 256,
    "learning_rate": 0.0001,
    "learning_rate_decay": 0.95,
    "weight_decay": 0.0001,
    "cross_validation": None,
    "val_size": 0.2,
    "num_cv_blocks": (5, 5),
    "lambda_1": 1,
    "lambda_2": 0.8,
    "species_weights_method": "inversely_proportional",
    "loss_fn": full_weighted_loss
}

# 8. Entrenar
model, auc_roc, auc_prg, corr, _ = train_multi_species(
    x_train=x_train,
    y_train=y_train,
    bg_train=x_bg,
    x_val=None,
    y_val=None,
    bg_val=None,
    x_test=x_test,
    y_test=y_test,
    config=config
)

print("\n=== RESULTADOS FINALES ===")
print(f"AUC ROC: {auc_roc:.4f}")
print(f"AUC PRG: {auc_prg:.4f}")
print(f"Correlación media: {corr:.4f}")
