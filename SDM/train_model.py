import argparse
import os
import pandas as pd

import numpy as np
import verde as vd

from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from iterstrat.ml_stratifiers import MultilabelStratifiedKFold
from joblib import load

from training_helpers import seed_everything, train_multi_species
from data_helpers import get_data_one_region, get_species_list
from losses import full_weighted_loss
import torch


def main():
    
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--region", type=str, help="region of interest", 
                            choices=["AWT", "CAN", "NSW", "NZ", "SA", "SWI","ECOPAL"], default="SWI")

    args = arg_parser.parse_args()
    
    seed_split = 42    
    device = "cpu"
    
    # Region of interest
    region = args.region
    co_occurrence = False
    valavi = True

    # Hyperparameters
    val_size = 0.2
    num_layers = 4
    width_MLP = 512
    dropout = 0.01
    epochs = 30
    batch_size = 256
    learning_rate = 0.0001
    learning_rate_decay = 0.95
    weight_decay = 0.0001
    cross_validation = "stratified"
    num_bg_val = 0
    num_cv_blocks = (5, 5)
    species_weights_method = "inversely_proportional"
    
    lambda_1 = 1
    lambda_2 = 0.95
    
    seed_everything(seed_split)
    
    # Get data
    x_train, y_train, coordinates_train, x_test, y_test, coordinates_test, bg, coordinates_bg = get_data_one_region(
                                                                region, co_occurrence=co_occurrence, valavi=valavi)
    num_species = len(get_species_list(region, remove=False))
    num_covariates = x_train.shape[1]
    
    # Scale data
    scaler_path = f"models/scaler/std_scaler_{region}.bin"
    sc = load(scaler_path)
    x_train = sc.transform(x_train)


    # Verificar si hay NaN en datos de entrada
    print("NaNs en x_train:", np.isnan(x_train).sum())
    print("NaNs en y_train:", np.isnan(y_train).sum())  
    print("NaNs en bg:", np.isnan(bg).sum())
    print("Shape de x_train:", x_train.shape)
    print("Shape de y_train:", y_train.shape)
    print("Shape de bg:", bg.shape)

    x_test = sc.transform(x_test)

    # Crear máscara conjunta donde ambas matrices no tienen NaN
    mask_x = ~np.isnan(x_test).any(axis=1)
    mask_y = ~np.isnan(y_test).any(axis=1)

    # Tomar solo índices donde ambas coinciden
    combined_mask = mask_x & mask_y

    x_test = x_test[combined_mask]
    y_test = y_test[combined_mask]

    bg = sc.transform(bg)
    bg = np.nan_to_num(bg, nan=0.0)

    # 1. Eliminar NaNs en bg (pseudoausencias)
    print(f"Antes de limpiar, bg tenía NaNs: {np.isnan(bg).sum()}")
    bg = bg[~np.isnan(bg).any(axis=1)]
    print(f"Después de limpiar, bg tiene forma: {bg.shape}")

    # 2. Verificar presencias en y_test
    print("Presencias por especie en y_test:", y_test.sum(axis=0))
    # 3. Verificar columnas originales del scaler vs actuales
    try:
        print("Columnas con las que se entrenó el scaler:")
        print(sc.feature_names_in_)
    except AttributeError:
        print("⚠️ El scaler fue entrenado sin nombres de columnas (posiblemente con un array).")

    print("Shape de x_train:", x_train.shape)
    print("Shape de y_train:", y_train.shape)
    print("Shape de bg:", bg.shape)

    # Cross-validation
    x_trains = []
    y_trains = []
    x_vals = []
    y_vals = []
    bg_trains = []
    bg_vals = []
    if cross_validation is not None:
        if cross_validation == "plain":
            kfold = KFold(n_splits=int(1/val_size), shuffle=True).split(x_train)
        elif cross_validation == "blocked":
            kfold = vd.BlockKFold(shape=num_cv_blocks, n_splits=int(1/val_size), shuffle=True, balance=True).split(coordinates_train)
        elif cross_validation == "stratified":
            kfold = MultilabelStratifiedKFold(n_splits=int(1/val_size), shuffle=True).split(x_train, y_train)
        else:
            raise ValueError("Invalid cross-validation method")
        for ind_train, ind_val in kfold:
            # Add background points to validation set
            num_presences_val = y_train[ind_val].sum()
            np.random.shuffle(bg)
            bg_train = bg[num_bg_val:]
            bg_val = bg[:num_bg_val]
            x_trains.append(x_train[ind_train])
            y_trains.append(y_train[ind_train])
            x_vals.append(x_train[ind_val])
            y_vals.append(y_train[ind_val])
            bg_trains.append(bg_train)
            bg_vals.append(bg_val)
    else: # No cross-validation
        x_trains.append(x_train)
        y_trains.append(y_train)
        x_vals.append(None)
        y_vals.append(None)
        bg_trains.append(bg)
        bg_vals.append(None)
    
    for i in range(len(x_trains)):
        
        x_train = x_trains[i]
        y_train = y_trains[i]
        x_val = x_vals[i]
        y_val = y_vals[i]
        bg_train = bg_trains[i]
        bg_val = bg_vals[i]
        
        # Ruta donde guardar los resultados
        results_path = "model_results.csv"

        # The configuration can be saved in a file      
        config = {
            "random_seed_split": seed_split,
            "region": region,
            "co_occurrence": co_occurrence,
            "valavi_covariates": valavi,
            "num_species": num_species,
            "num_covariates": num_covariates,
            "device": device,
            "num_layers": num_layers,
            "width_MLP": width_MLP,
            "dropout": dropout,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "learning_rate_decay": learning_rate_decay,
            "weight_decay": weight_decay,
            "cross_validation": cross_validation,
            "val_size": val_size,
            "num_cv_blocks": num_cv_blocks,
            "lambda_1": lambda_1,
            "lambda_2": lambda_2,
            "species_weights_method": species_weights_method,
            "loss_fn": full_weighted_loss
        }

        train_params = {
            "x_train": x_train,
            "y_train": y_train,
            "bg_train": bg_train,
            "x_val": x_val,
            "y_val": y_val,
            "bg_val": bg_val,
            "x_test": x_test,
            "y_test": y_test,
            "config": config,
        }

        model, mean_test_auc_roc, mean_test_auc_prg, mean_test_cor, mean_val_auc_roc = train_multi_species(**train_params)
        
        print("\nFinal results on test set:")
        print("auc_roc: {}".format(mean_test_auc_roc))
        print("auc_prg: {}".format(mean_test_auc_prg))
        print("correlation: {}\n\n".format(mean_test_cor))


        # Registro de resultados
        results_row = {
            "region": region,
            "lambda_1": lambda_1,
            "lambda_2": lambda_2,
            "fold": i,
            "val_auc": mean_val_auc_roc,
            "test_auc_roc": mean_test_auc_roc,
            "test_auc_prg": mean_test_auc_prg,
            "test_correlation": mean_test_cor
        }

        # Crear o agregar al archivo CSV
        if not os.path.isfile(results_path):
            pd.DataFrame([results_row]).to_csv(results_path, index=False)
        else:
            pd.DataFrame([results_row]).to_csv(results_path, mode='a', header=False, index=False)

        # Guardar modelo entrenado
        torch.save(model.state_dict(), f"models/model_{region}.pt")
        print(f"Modelo guardado en: models/model_{region}.pt")


if __name__ == '__main__':
    main()


