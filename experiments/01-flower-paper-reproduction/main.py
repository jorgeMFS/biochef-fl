import sys
import random
import atexit
import json
from collections import OrderedDict
from typing import List, Tuple
from datetime import datetime
import os
from math import sqrt

import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend for plotting
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from openpyxl import load_workbook, Workbook

import flwr as fl
from flwr.common import Metrics

DEVICE = torch.device("cpu")  # Try "cuda" to train on GPU
print(f"Training on {DEVICE} using PyTorch {torch.__version__} and Flower {fl.__version__}")
# disable_progress_bar()

PAPER_MODE = "--paper" in sys.argv
sequence_layout = "timesteps" if "--timesteps" in sys.argv else "features"
reset_optimizer = "--reset-optimizer" in sys.argv
train_only_scaler = "--train-only-scaler" in sys.argv
learning_rate = 0.003
if "--lr" in sys.argv:
    lr_position = sys.argv.index("--lr") + 1
    if lr_position >= len(sys.argv):
        raise ValueError("--lr requires a positive number")
    learning_rate = float(sys.argv[lr_position])
    if learning_rate <= 0:
        raise ValueError("--lr must be a positive number")
rounds_override = None
if "--rounds" in sys.argv:
    rounds_position = sys.argv.index("--rounds") + 1
    if rounds_position >= len(sys.argv):
        raise ValueError("--rounds requires a positive integer")
    rounds_override = int(sys.argv[rounds_position])
    if rounds_override < 1:
        raise ValueError("--rounds must be a positive integer")
seed = 42
if "--seed" in sys.argv:
    seed_position = sys.argv.index("--seed") + 1
    if seed_position >= len(sys.argv):
        raise ValueError("--seed requires an integer")
    seed = int(sys.argv[seed_position])

random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(seed)

NUM_CLIENTS = 3
BATCH_SIZE = 32

time_str = datetime.now().strftime('%m/%d_%H%M%S_%f')
output_dir = f'data/output/{time_str}'
os.makedirs(output_dir)

input_cols = ['NewCases']
output_col = ['NewCases']

# Define the Hyper Parameters
input_size = 1 if PAPER_MODE and sequence_layout == "timesteps" else (
    7 if PAPER_MODE else len(input_cols)
)
hidden_size = 64
num_layers = 2
output_size = 1
num_epochs = 200
federated_local_epochs = 1 if PAPER_MODE else num_epochs
early_stopping_patience = 10
dropout = 0.0  # Dropout probability
time_lag = 1
window = 7 if PAPER_MODE else 3
REGIONS = ['Portugal', 'Macau', 'Guangdong']
# Flower parameters
NUM_ROUNDS = rounds_override or (200 if PAPER_MODE else 10)

DAY_MODE = '1D'
ROUND = 5  # Do 5 individual experiment, each time add {ROUND_SIZE} data as dataset
ROUND_SIZE = 14
MOV_AVG_WIN = 7 if PAPER_MODE else 3
PAPER_START_DATE = "2021-11-24"
PAPER_TEST_START_DATE = "2022-10-18"
PAPER_END_DATE = "2023-01-08"

OMICRON_START_COLS = 673  # Omicron first reported on 2021-11-24. https://www.who.int/news/item/26-11-2021-classification-of-omicron-(b.1.1.529)-sars-cov-2-variant-of-concern

MODEL_LSTM = 'LSTM'
MODEL_FL_LSTM = 'FL-LSTM'

current_round = 0  # Current experiment ID


def cleanup_output_directory():
    """Remove intermediate artifacts while preserving analysis outputs."""
    removed = []
    for filename in os.listdir(output_dir):
        if not (
            filename.startswith("predit_data-")
            or filename.startswith("opt_")
        ):
            continue
        path = os.path.join(output_dir, filename)
        if os.path.isfile(path):
            os.remove(path)
            removed.append(filename)
    if removed:
        print(f"Removed {len(removed)} intermediate output files")


atexit.register(cleanup_output_directory)


def save_run_metadata():
    """Persist the configuration needed to reproduce this experiment."""
    metadata = {
        "seed": seed,
        "learning_rate": learning_rate,
        "reset_optimizer": reset_optimizer,
        "train_only_scaler": train_only_scaler,
        "paper_mode": PAPER_MODE,
        "sequence_layout": sequence_layout,
        "window": window,
        "moving_average_window": MOV_AVG_WIN,
        "federated_local_epochs": federated_local_epochs,
        "rounds": NUM_ROUNDS,
        "regions": REGIONS,
        "paper_start_date": PAPER_START_DATE,
        "paper_test_start_date": PAPER_TEST_START_DATE,
        "paper_end_date": PAPER_END_DATE,
        "input_file": "data/input/c19_data_for_FL.xlsx",
    }
    with open(f"{output_dir}/run_metadata.json", "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)


def save_round_summary():
    """Save final and best global evaluation metrics after training."""
    path = f"{output_dir}/round_metrics.csv"
    if not os.path.exists(path):
        return
    metrics = pd.read_csv(path)
    if metrics.empty or "rmse" not in metrics:
        return
    best = metrics.loc[metrics["rmse"].idxmin()]
    final = metrics.iloc[-1]
    summary = {
        "best_round": int(best["round"]),
        "best_rmse": float(best["rmse"]),
        "best_mae": float(best["mae"]),
        "best_smape": float(best["smape"]),
        "final_round": int(final["round"]),
        "final_rmse": float(final["rmse"]),
        "final_mae": float(final["mae"]),
        "final_smape": float(final["smape"]),
    }
    with open(f"{output_dir}/round_summary.json", "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)


def _make_sequences(values, window_size):
    """Create one-step-ahead sequences in the selected LSTM layout."""
    sequences = np.asarray(
        [values[start:start + window_size] for start in range(len(values) - window_size)],
        dtype=np.float32,
    )
    if sequence_layout == "timesteps":
        return sequences.reshape(-1, window_size, 1)
    return sequences.reshape(-1, 1, window_size)


def _recursive_forecast(model, history, scaler, horizon):
    """Forecast one or more steps from a raw seven-day history."""
    values = list(np.asarray(history, dtype=np.float32).reshape(-1))
    predictions = []
    model.eval()
    with torch.no_grad():
        for _ in range(horizon):
            window_values = np.asarray(values[-window:], dtype=np.float32)
            scaled_window = scaler.transform(window_values.reshape(-1, 1))
            if sequence_layout == "timesteps":
                model_input = scaled_window.reshape(1, window, 1)
            else:
                model_input = scaled_window.reshape(1, 1, window)
            tensor_input = torch.tensor(model_input, dtype=torch.float32)
            scaled_prediction = model(tensor_input).numpy().reshape(-1, 1)
            prediction = float(scaler.inverse_transform(scaled_prediction)[0, 0])
            predictions.append(prediction)
            values.append(prediction)
    return predictions


def _multi_horizon_predictions(model, x_test, y_test, scaler, test_dates):
    """Create rolling-origin recursive forecasts for horizons one through seven."""
    raw_windows = scaler.inverse_transform(
        x_test.detach().numpy().reshape(-1, 1)
    ).reshape(x_test.shape)
    actual = scaler.inverse_transform(
        y_test.detach().numpy().reshape(-1, 1)
    ).flatten()
    results = {}
    for horizon in range(1, 8):
        count = len(raw_windows) - horizon + 1
        if count <= 0:
            break
        predictions = [
            _recursive_forecast(
                model,
                raw_windows[index].reshape(-1),
                scaler,
                horizon,
            )[-1]
            for index in range(count)
        ]
        results[str(horizon)] = {
            "dates": [
                pd.Timestamp(date).isoformat()
                for date in test_dates[horizon - 1:horizon - 1 + count]
            ],
            "actual": actual[horizon - 1:horizon - 1 + count].tolist(),
            "predictions": predictions,
        }
    return results


# Define LSTM model
class LSTM(nn.Module):
    def __init__(self, input_size=1, hidden_size=64, num_layers=2, output_size=1, dropout=0.0):
        super(LSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_size, output_size)
        self.dropout = nn.Dropout(dropout)  # Define dropout layer

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.dropout(out)  # Apply dropout
        out = self.fc(out[:, -1, :])
        return out


# trainloader = trainloaders[0]
# valloader = valloaders[0]
# Initialize model, loss function, and optimizer
# model = LSTM(input_size, hidden_size, num_layers, output_size, dropout=dropout)
# criterion = nn.MSELoss()
# optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

def smape(y_true, y_pred):
    """
    Compute SMAPE（Symmetric Mean Absolute Percentage Error）
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    denominator = np.abs(y_true) + np.abs(y_pred)
    terms = np.divide(
        np.abs(y_pred - y_true),
        denominator,
        out=np.zeros_like(denominator),
        where=denominator != 0,
    )
    return float(np.mean(terms) * 100.0)


def _load_paper_series(region):
    data_df = pd.read_excel(
        'data/input/c19_data_for_FL.xlsx',
        sheet_name=region,
        index_col='Date',
    )
    data_df.index = pd.to_datetime(data_df.index)
    data_df = data_df[['NewCases']]
    data_df = data_df.rolling(window=MOV_AVG_WIN).mean()
    if region == "Portugal":
        data_df = data_df.rolling(window=MOV_AVG_WIN).mean()
    return data_df.loc[PAPER_START_DATE:PAPER_END_DATE].dropna()


def set_parameters(model, parameters: List[np.ndarray]):
    params_dict = zip(model.state_dict().keys(), parameters)
    state_dict = OrderedDict({k: torch.Tensor(v) for k, v in params_dict})
    model.load_state_dict(state_dict, strict=True)


def get_parameters(model) -> List[np.ndarray]:
    return [val.cpu().numpy() for _, val in model.state_dict().items()]


def train_model(model, x_train, y_train, epochs, patience=None):
    """Train a model and optionally stop after patience stagnant epochs."""
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    train_losses = []
    best_loss = float("inf")
    best_state = None
    stagnant_epochs = 0

    model.train()
    for epoch in range(epochs):
        outputs = model(x_train)
        optimizer.zero_grad()
        loss = criterion(outputs, y_train.unsqueeze(1))
        loss.backward()
        optimizer.step()

        loss_value = float(loss.item())
        train_losses.append(loss_value)
        if loss_value < best_loss:
            best_loss = loss_value
            best_state = OrderedDict(
                (key, value.detach().clone())
                for key, value in model.state_dict().items()
            )
            stagnant_epochs = 0
        else:
            stagnant_epochs += 1

        if (epoch + 1) % 100 == 0:
            print(f"Epoch [{epoch + 1}/{epochs}], Loss: {loss_value:.4f}")
        if patience is not None and stagnant_epochs >= patience:
            print(f"Early stopping at epoch {epoch + 1}")
            break

    if best_state is not None:
        model.load_state_dict(best_state)
    return criterion, train_losses


_CACHE = {}
def load_datasets_cached(region):
    if region not in _CACHE:
        _CACHE[region] = load_datasets(region)
    return _CACHE[region]

def load_datasets(region):
    # Load data from Excel
    if PAPER_MODE:
        data_df = _load_paper_series(region)
    else:
        data_df = pd.read_excel('data/input/c19_data_for_FL.xlsx', sheet_name=region, index_col='Date')
        data_df = data_df[OMICRON_START_COLS:]  # Ignore data prior to the first reported Omicron case

        # Compute moving average
        for key in data_df.keys():
            data_df[key] = data_df[key].rolling(window=MOV_AVG_WIN).mean()
        data_df = data_df[MOV_AVG_WIN - 1:]  # Delete the data who has no enouth previous data to complete moving average

    print(f'data_df={data_df}')

    if not PAPER_MODE:
        data_df = data_df[0:current_round * ROUND_SIZE]

    data_df = data_df.resample(DAY_MODE).mean()  # Resample data on weekly basis, taking mean
    values = data_df["NewCases"].to_numpy(dtype=np.float32)

    if PAPER_MODE:
        if len(values) <= window:
            raise ValueError(f"Not enough data for a {window}-day input window in {region}")
        raw_x = _make_sequences(values, window)
        raw_y = values[window:]
        sequence_index = data_df.index[window:]
        test_start = pd.Timestamp(PAPER_TEST_START_DATE)
        split_at = int(np.flatnonzero(sequence_index >= test_start)[0])
        if split_at <= 0 or split_at >= len(raw_y):
            raise ValueError(f"Paper train/test split is invalid for {region}")
    else:
        data = data_df[input_cols].values
        target = data_df[output_col].values
        data = data[0:-time_lag]
        target = target[time_lag:]
        data_df = data_df[time_lag:]
        raw_x = data.reshape(-1, 1, len(input_cols))
        raw_y = target.reshape(-1)
        sequence_index = data_df.index
        test_size = max(1, int(len(raw_y) * 0.2))

        split_at = len(raw_y) - test_size
    x_scaler = MinMaxScaler()
    y_scaler = MinMaxScaler()
    scaler_x_values = raw_x[:split_at]
    scaler_y_values = raw_y[:split_at]
    if train_only_scaler:
        x_scaler.fit(scaler_x_values.reshape(-1, 1))
        y_scaler.fit(scaler_y_values.reshape(-1, 1))
    else:
        x_scaler.fit(values.reshape(-1, 1))
        y_scaler.fit(values.reshape(-1, 1))
    X = x_scaler.transform(raw_x.reshape(-1, 1)).reshape(raw_x.shape)
    y = y_scaler.transform(raw_y.reshape(-1, 1)).flatten()

    X_train, X_test = X[:split_at], X[split_at:]
    y_train, y_test = y[:split_at], y[split_at:]
    X_train = torch.tensor(X_train, dtype=torch.float32)
    y_train = torch.tensor(y_train, dtype=torch.float32)
    X_test = torch.tensor(X_test, dtype=torch.float32)
    y_test = torch.tensor(y_test, dtype=torch.float32)

    return sequence_index, X_train, X_test, y_train, y_test, y_scaler


def load_centralized_datasets():
    """Build one paper-protocol dataset from all regional time series."""
    regional = {}

    for region in REGIONS:
        data_df = _load_paper_series(region).resample(DAY_MODE).mean()
        values = data_df["NewCases"].to_numpy(dtype=np.float32)
        raw_x = _make_sequences(values, window)
        raw_y = values[window:]
        sequence_index = data_df.index[window:]
        split_at = int(np.flatnonzero(
            sequence_index >= pd.Timestamp(PAPER_TEST_START_DATE)
        )[0])
        if split_at <= 0 or split_at >= len(raw_y):
            raise ValueError(f"Paper train/test split is invalid for {region}")

        x_scaler = MinMaxScaler()
        y_scaler = MinMaxScaler()
        if train_only_scaler:
            x_scaler.fit(raw_x[:split_at].reshape(-1, 1))
            y_scaler.fit(raw_y[:split_at].reshape(-1, 1))
        else:
            x_scaler.fit(values.reshape(-1, 1))
            y_scaler.fit(values.reshape(-1, 1))

        regional[region] = (
            data_df.index[window:],
            raw_x[:split_at],
            raw_x[split_at:],
            raw_y[:split_at],
            raw_y[split_at:],
            x_scaler,
            y_scaler,
        )
    scaled = {}
    for region, (
        index,
        x_train,
        x_test,
        y_train,
        y_test,
        x_scaler,
        y_scaler,
    ) in regional.items():
        scaled[region] = (
            index,
            torch.tensor(
                x_scaler.transform(x_train.reshape(-1, 1)).reshape(x_train.shape),
                dtype=torch.float32,
            ),
            torch.tensor(
                x_scaler.transform(x_test.reshape(-1, 1)).reshape(x_test.shape),
                dtype=torch.float32,
            ),
            torch.tensor(y_scaler.transform(y_train.reshape(-1, 1)).flatten(), dtype=torch.float32),
            torch.tensor(y_scaler.transform(y_test.reshape(-1, 1)).flatten(), dtype=torch.float32),
            y_scaler,
        )

    x_train = torch.cat([values[1] for values in scaled.values()])
    y_train = torch.cat([values[3] for values in scaled.values()])
    return scaled, x_train, y_train


def save_performance(label, rmse, mae, smape_value, model, round_number, normalization_scale):
    normalization_scale = max(float(normalization_scale), np.finfo(float).eps)
    nrmse = rmse / normalization_scale
    nmae = mae / normalization_scale
    # Load existing Excel file or create a new one if it doesn't exist
    file_path = f'{output_dir}/performance_{label}.xlsx'
    try:
        wb = load_workbook(file_path)
        ws = wb.active
    except FileNotFoundError:
        wb = Workbook()
        ws = wb.active
        ws.append([
            'Label', 'RMSE', 'MAE', 'SMAPE', 'nRMSE', 'nMAE',
            'Model', 'Round', 'NormalizationScale',
        ])
    ws.append([
        label, rmse, mae, smape_value, nrmse, nmae,
        model, round_number, normalization_scale,
    ])
    wb.save(file_path)


def lstm(region, index, x_train, x_test, y_train, y_test, scaler):
    model = LSTM(input_size, hidden_size, num_layers, output_size, dropout=dropout)
    criterion, train_losses = train_model(
        model,
        x_train,
        y_train,
        num_epochs,
        early_stopping_patience if PAPER_MODE else None,
    )

    model.eval()
    with torch.no_grad():
        y_pred_train = model(x_train)
        y_pred_test = model(x_test)

    # Denormalize predictions
    scaler = scaler
    y_train = scaler.inverse_transform(y_train.detach().numpy().reshape(-1, 1)).flatten()
    y_test = scaler.inverse_transform(y_test.unsqueeze(1).numpy().reshape(-1, 1)).flatten()
    y_pred_train = scaler.inverse_transform(y_pred_train.detach().numpy().reshape(-1, 1)).flatten()
    y_pred_test = scaler.inverse_transform(y_pred_test.detach().numpy().reshape(-1, 1)).flatten()

    df_pred = pd.concat(
        [pd.DataFrame(y_pred_train, index=index[:len(x_train)]), pd.DataFrame(y_pred_test, index=index[len(x_train):])])
    df_pred.to_excel(f'{output_dir}/predit_data-{region}-{MODEL_LSTM}-round_{current_round}.xlsx')

    loss = criterion(torch.tensor(y_pred_test), torch.tensor(y_test))
    rmse = sqrt(mean_squared_error(y_test, y_pred_test))
    mae = mean_absolute_error(y_test, y_pred_test)
    s_mape = smape(y_test, y_pred_test)
    print(f'Test Loss: RMSE={rmse:.2f}, MAE={mae:.2f}, SMAPE={s_mape:.2f}')

    save_performance(
        region,
        rmse,
        mae,
        s_mape,
        MODEL_LSTM,
        current_round,
        np.max(np.abs(np.concatenate((y_train, y_test)))),
    )

    # Plot results
    fig, axs = plt.subplots(2, 1, figsize=(8, 8))

    index_array = index.to_numpy()
    axs[0].plot(index_array, np.concatenate((y_train, y_test), axis=0), label='Reported cases', c='black')
    # plt.plot(data_df.index, torch.cat((y_train, y_test), dim=0).numpy(), label='Data')
    axs[0].plot(index_array[:len(y_pred_train)], y_pred_train, label='LSTM predicted (Train)')
    axs[0].plot(index_array[len(y_pred_train):], y_pred_test, label='LSTM predicted (Test)')
    axs[0].set_title('LSTM Prediction')
    axs[0].set_xlabel('Time')
    axs[0].set_ylabel('Number of reported cases')
    axs[0].legend()

    axs[1].plot(train_losses, label='Loss')
    axs[1].set_title('Training loss')
    axs[1].set_xlabel('Epoch')
    axs[1].set_ylabel('MSE')
    axs[1].legend()

    # Adjust layout
    plt.tight_layout()
    plt.savefig(f'{output_dir}/{region}-lstm-round_{current_round}.png')
    plt.cla()
    plt.close()


def centralized_lstm():
    """Train the pooled centralized baseline used by the paper."""
    regional, x_train, y_train = load_centralized_datasets()
    model = LSTM(input_size, hidden_size, num_layers, output_size, dropout=dropout)
    criterion, _ = train_model(
        model,
        x_train,
        y_train,
        num_epochs,
        early_stopping_patience,
    )

    model.eval()
    with torch.no_grad():
        for region, (
            index,
            x_region_train,
            x_region_test,
            y_region_train,
            y_region_test,
            scaler,
        ) in regional.items():
            y_pred_train = model(x_region_train)
            y_pred_test = model(x_region_test)
            y_train_raw = scaler.inverse_transform(y_region_train.numpy().reshape(-1, 1)).flatten()
            y_test_raw = scaler.inverse_transform(y_region_test.numpy().reshape(-1, 1)).flatten()
            y_pred_train_raw = scaler.inverse_transform(y_pred_train.numpy()).flatten()
            y_pred_test_raw = scaler.inverse_transform(y_pred_test.numpy()).flatten()

            rmse = sqrt(mean_squared_error(y_test_raw, y_pred_test_raw))
            mae = mean_absolute_error(y_test_raw, y_pred_test_raw)
            s_mape = smape(y_test_raw, y_pred_test_raw)
            save_performance(
                region,
                rmse,
                mae,
                s_mape,
                "C-LSTM",
                current_round,
                np.max(np.abs(np.concatenate((y_train_raw, y_test_raw)))),
            )

            predictions = pd.concat([
                pd.DataFrame(y_pred_train_raw, index=index[:len(y_pred_train_raw)]),
                pd.DataFrame(y_pred_test_raw, index=index[len(y_pred_train_raw):]),
            ])
            predictions.to_excel(
                f'{output_dir}/predit_data-{region}-C-LSTM-round_{current_round}.xlsx'
            )

            fig, ax = plt.subplots(figsize=(8, 5))
            index_array = index.to_numpy()
            ax.plot(
                index_array,
                np.concatenate((y_train_raw, y_test_raw)),
                label='Reported cases',
                c='black',
            )
            ax.plot(
                index_array[:len(y_pred_train_raw)],
                y_pred_train_raw,
                label='C-LSTM predicted (Train)',
            )
            ax.plot(
                index_array[len(y_pred_train_raw):],
                y_pred_test_raw,
                label='C-LSTM predicted (Test)',
            )
            ax.set_title('Centralized C-LSTM Prediction')
            ax.set_xlabel('Time')
            ax.set_ylabel('Number of reported cases')
            ax.legend()
            plt.tight_layout()
            plt.savefig(f'{output_dir}/{region}-c_lstm-round_{current_round}.png')
            plt.close(fig)


def _read_prediction_file(path, dates):
    """Read predictions saved by a local or centralized model."""
    data = pd.read_excel(path, index_col=0)
    if data.shape[1] != 1:
        raise ValueError(f"Expected one prediction column in {path}")
    data.index = pd.to_datetime(data.index)
    return data.iloc[:, 0].reindex(pd.to_datetime(dates)).to_numpy(dtype=float)


def _rounded_y_limit(values):
    """Return a positive, rounded y-axis limit that contains all plotted values."""
    maximum = max(float(np.max(np.abs(values))), 0.0)
    if maximum == 0:
        return 1
    step = (
        10000 if maximum >= 10000
        else 1000 if maximum >= 1000
        else 100 if maximum >= 100
        else 10 if maximum >= 10
        else 1
    )
    return step * np.ceil(maximum / step)


def _paper_y_limit(region, extra_values=()):
    """Return a paper-style regional limit that contains every plotted value."""
    series = _load_paper_series(region).resample(DAY_MODE).mean()["NewCases"]
    values = [series.to_numpy()]
    values.extend(np.asarray(extra, dtype=float) for extra in extra_values)
    return _rounded_y_limit(np.concatenate(values))


def save_figure_4a(horizons_by_region, server_round):
    """Create the paper-style one-to-seven-day federated forecast figure."""
    missing = [region for region in REGIONS if region not in horizons_by_region]
    if missing:
        print(
            "Could not create Figure 4(a); missing horizon artifacts: "
            + ", ".join(missing)
        )
        return

    colors = plt.cm.Blues(np.linspace(0.9, 0.45, 7))
    regional_limits = {}
    fig, axes = plt.subplots(len(REGIONS), 1, figsize=(12, 12), sharex=False)
    for ax, region in zip(np.atleast_1d(axes), REGIONS):
        region_horizons = horizons_by_region[region]
        plotted_values = []
        for horizon in range(1, 8):
            payload = region_horizons.get(str(horizon))
            if payload is None:
                continue
            plotted_values.append(np.asarray(payload["predictions"], dtype=float))
            ax.plot(
                pd.to_datetime(payload["dates"]).to_numpy(),
                payload["predictions"],
                color=colors[horizon - 1],
                label=str(horizon),
            )
        first = region_horizons.get("1")
        if first is not None:
            plotted_values.append(np.asarray(first["actual"], dtype=float))
            ax.plot(
                pd.to_datetime(first["dates"]).to_numpy(),
                first["actual"],
                color="red",
                linestyle="--",
                linewidth=2,
                label="Real",
            )
        ax.set_title(region)
        regional_limits[region] = _paper_y_limit(region, plotted_values)
        ax.set_ylim(0, regional_limits[region])
        ax.set_ylabel("New cases")
        ax.grid(True, alpha=0.25)
        ax.legend(title="Days ahead")

    axes[-1].set_xlabel("Date")
    fig.suptitle("Federated LSTM forecasts from one to seven days ahead")
    fig.tight_layout()
    path = f"{output_dir}/figure4a-federated-round_{server_round}.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved Figure 4(a) to {os.path.abspath(path)}")
    return regional_limits


def save_figure_4b(predictions_by_region, server_round, paper_limits=None):
    """Create the paper-style test-period comparison for all regions."""
    missing = []
    comparison = {}
    dates_by_region = {}

    for region in REGIONS:
        payload = predictions_by_region.get(region)
        if payload is None:
            missing.append(f"{region}: federated test predictions")
            continue

        dates = pd.to_datetime(payload["dates"]).to_numpy()
        local_files = [
            name for name in os.listdir(output_dir)
            if name.startswith(f"predit_data-{region}-{MODEL_LSTM}-round_")
            and name.endswith(".xlsx")
        ]
        centralized_files = [
            name for name in os.listdir(output_dir)
            if name.startswith(f"predit_data-{region}-C-LSTM-round_")
            and name.endswith(".xlsx")
        ]
        if not local_files:
            missing.append(f"{region}: local LSTM prediction file")
            continue
        if not centralized_files:
            missing.append(f"{region}: centralized C-LSTM prediction file")
            continue

        local = _read_prediction_file(
            os.path.join(output_dir, sorted(local_files)[-1]), dates
        )
        centralized = _read_prediction_file(
            os.path.join(output_dir, sorted(centralized_files)[-1]), dates
        )
        federated = np.asarray(payload["predictions"], dtype=float)
        actual = np.asarray(payload["actual"], dtype=float)
        if not (len(dates) == len(actual) == len(local) == len(centralized) == len(federated)):
            raise ValueError(f"Prediction lengths do not match for {region}")

        comparison[region] = {
            "actual": actual,
            "local": local,
            "centralized": centralized,
            "federated": federated,
        }
        dates_by_region[region] = dates

    if missing:
        print(
            "Could not create Figure 4(b); missing artifacts: "
            + ", ".join(missing)
        )
        return
    paper_limits = paper_limits or {}

    fig, axes = plt.subplots(len(REGIONS), 1, figsize=(12, 12), sharex=False)
    for ax, region in zip(np.atleast_1d(axes), REGIONS):
        values = comparison[region]
        dates = dates_by_region[region]
        ax.plot(dates, values["actual"], color="red", linestyle="--", label="Reported cases")
        ax.plot(dates, values["local"], color="tab:green", label="L-LSTM")
        ax.plot(dates, values["centralized"], color="tab:purple", label="C-LSTM")
        ax.plot(dates, values["federated"], color="tab:blue", label="F-LSTM")
        ax.set_title(region)
        ax.set_ylim(
            0,
            _rounded_y_limit(
                np.concatenate(list(values.values()))
            ),
        )
        ax.set_ylabel("New cases")
        ax.grid(True, alpha=0.25)
        ax.legend()

    axes[-1].set_xlabel("Date")
    fig.suptitle("Test-period predictions: adapted regional scales")
    fig.tight_layout()
    combined_path = f"{output_dir}/figure4b-comparison-round_{server_round}.png"
    fig.savefig(combined_path, dpi=150)
    plt.close(fig)
    print(f"Saved Figure 4(b) comparison to {os.path.abspath(combined_path)}")

    for region in REGIONS:
        fig, ax = plt.subplots(figsize=(10, 5))
        values = comparison[region]
        dates = dates_by_region[region]
        ax.plot(dates, values["actual"], color="red", linestyle="--", label="Reported cases")
        ax.plot(dates, values["local"], color="tab:green", label="L-LSTM")
        ax.plot(dates, values["centralized"], color="tab:purple", label="C-LSTM")
        ax.plot(dates, values["federated"], color="tab:blue", label="F-LSTM")
        ax.set_title(f"{region}: test-period predictions (adapted scale)")
        ax.set_xlabel("Date")
        ax.set_ylabel("New cases")
        ax.set_ylim(0, _rounded_y_limit(np.concatenate(list(values.values()))))
        ax.grid(True, alpha=0.25)
        ax.legend()
        fig.tight_layout()
        path = f"{output_dir}/{region}-figure4b-round_{server_round}.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)

    fig, axes = plt.subplots(len(REGIONS), 1, figsize=(12, 12), sharex=False)
    for ax, region in zip(np.atleast_1d(axes), REGIONS):
        values = comparison[region]
        dates = dates_by_region[region]
        ax.plot(dates, values["actual"], color="red", linestyle="--", label="Reported cases")
        ax.plot(dates, values["local"], color="tab:green", label="L-LSTM")
        ax.plot(dates, values["centralized"], color="tab:purple", label="C-LSTM")
        ax.plot(dates, values["federated"], color="tab:blue", label="F-LSTM")
        ax.set_title(region)
        ax.set_ylim(
            0,
            paper_limits.get(
                region,
                _paper_y_limit(
                    region,
                    [np.concatenate(list(values.values()))],
                ),
            ),
        )
        ax.set_ylabel("New cases")
        ax.grid(True, alpha=0.25)
        ax.legend()

    axes[-1].set_xlabel("Date")
    fig.suptitle("Test-period predictions: same regional scales as Figure 4(a)")
    fig.tight_layout()
    paper_combined_path = (
        f"{output_dir}/figure4b-comparison-paper-scale-round_{server_round}.png"
    )
    fig.savefig(paper_combined_path, dpi=150)
    plt.close(fig)
    print(
        "Saved paper-scale Figure 4(b) comparison to "
        f"{os.path.abspath(paper_combined_path)}"
    )

    for region in REGIONS:
        fig, ax = plt.subplots(figsize=(10, 5))
        values = comparison[region]
        dates = dates_by_region[region]
        ax.plot(dates, values["actual"], color="red", linestyle="--", label="Reported cases")
        ax.plot(dates, values["local"], color="tab:green", label="L-LSTM")
        ax.plot(dates, values["centralized"], color="tab:purple", label="C-LSTM")
        ax.plot(dates, values["federated"], color="tab:blue", label="F-LSTM")
        ax.set_title(f"{region}: test-period predictions (Figure 4(a) scale)")
        ax.set_xlabel("Date")
        ax.set_ylabel("New cases")
        ax.set_ylim(
            0,
            paper_limits.get(
                region,
                _paper_y_limit(
                    region,
                    [np.concatenate(list(values.values()))],
                ),
            ),
        )
        ax.grid(True, alpha=0.25)
        ax.legend()
        fig.tight_layout()
        path = f"{output_dir}/{region}-figure4b-paper-scale-round_{server_round}.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)


class FlowerClient(fl.client.NumPyClient):
    def __init__(self, region):
        self.region = region
        self.index, self.x_train, self.x_test, self.y_train, self.y_test, self.scaler = load_datasets_cached(region)

        # Initialize model, loss function, and optimizer
        self.model = LSTM(input_size, hidden_size, num_layers, output_size, dropout=dropout)
        self.criterion = nn.MSELoss()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)

        self.train_losses = []

        self.round = 0

    def _save_training_loss_plot(self):
        """Save this client's local loss history after the final round."""
        if not self.train_losses:
            print(f"Skipping training-loss plot for {self.region}: no loss history")
            return

        fig, ax = plt.subplots(figsize=(8, 5))
        rounds = np.arange(1, len(self.train_losses) + 1)
        ax.plot(rounds, self.train_losses, color='tab:blue', linewidth=1.5)
        ax.set_title(f'{self.region} federated training loss')
        ax.set_xlabel('Communication round')
        ax.set_ylabel('Local training MSE')
        ax.grid(True, alpha=0.25)
        fig.tight_layout()
        plot_path = (
            f'{output_dir}/{self.region}-training-loss.png'
        )
        fig.savefig(plot_path, dpi=150)
        plt.close(fig)
        print(f"Saved federated training-loss plot to {os.path.abspath(plot_path)}")

    def get_parameters(self, config):
        print(f'FlowerClient: get_parameters')
        return get_parameters(self.model)

    def fit(self, parameters, config):
        print(f'FlowerClient: fit')
        set_parameters(self.model, parameters)

        # Rebuild the optimizer for THIS model instance, then restore its state
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        opt_path = f"{output_dir}/opt_{self.region}.pt"
        if not reset_optimizer and os.path.exists(opt_path):
            self.optimizer.load_state_dict(torch.load(opt_path))

        state = self.optimizer.state_dict()["state"]
        steps = int(next(iter(state.values()))["step"]) if state else 0
        print(f"{self.region}: Adam step counter at start of fit = {steps}")

        # Set the model to training mode
        self.model.train()
        # Training loop
        for epoch in range(federated_local_epochs):
            outputs = self.model(self.x_train)
            self.optimizer.zero_grad()
            # add unsqueeze(1) to match the expected target shape
            loss = self.criterion(outputs, self.y_train.unsqueeze(1))
            loss.backward()
            self.optimizer.step()
            # print(f'FL-LSTM before append: len(self.train_losses)={len(self.train_losses)}')
            self.train_losses.append(loss.item())
            # print(f'FL-LSTM after append: len(self.train_losses)={len(self.train_losses)}')
            if (epoch + 1) % 100 == 0:
                print(f'Epoch [{epoch + 1}/{num_epochs}], Loss: {loss.item():.4f}')

        torch.save(self.optimizer.state_dict(), opt_path)
        return get_parameters(self.model), len(self.x_train), {
            "region": self.region,
            "train_loss": float(loss.item()),
            "local_epochs": federated_local_epochs,
        }

    def evaluate(self, parameters, config):
        print(f'FlowerClient: evaluate')
        server_round = int(config.get("server_round", 0))
        save_artifacts = (
            server_round == 1
            or server_round % 10 == 0
            or server_round == NUM_ROUNDS 
        )
        print(f'evaluate (region={self.region}): config={config}')
        print("FL-LSTM evaluate: fit loss is recorded by the server")

        set_parameters(self.model, parameters)

        # loss, accuracy = test(model, testloader)
        # print(f"Final test set performance:\n\tloss {loss}\n\taccuracy {accuracy}")

        # loss, accuracy = test(self.model, self.valloader)

        # Evaluation
        self.model.eval()
        with torch.no_grad():
            y_pred_train = self.model(self.x_train)
            y_pred_test = self.model(self.x_test)

        # Denormalize predictions
        scaler = self.scaler
        y_train = scaler.inverse_transform(self.y_train.detach().numpy().reshape(-1, 1)).flatten()
        y_test = scaler.inverse_transform(self.y_test.unsqueeze(1).numpy().reshape(-1, 1)).flatten()
        y_pred_train = scaler.inverse_transform(y_pred_train.detach().numpy().reshape(-1, 1)).flatten()
        y_pred_test = scaler.inverse_transform(y_pred_test.detach().numpy().reshape(-1, 1)).flatten()

        if save_artifacts:
            df_pred = pd.concat([pd.DataFrame(y_pred_train, index=self.index[:len(self.x_train)]),
                                 pd.DataFrame(y_pred_test, index=self.index[len(self.x_train):])])
            df_pred.to_excel(f'{output_dir}/predit_data-{self.region}-{MODEL_FL_LSTM}-round_{server_round}.xlsx')
            self._save_training_loss_plot()

        loss = self.criterion(torch.tensor(y_pred_test), torch.tensor(y_test))
        s_mape = smape(y_test, y_pred_test)
        rmse = sqrt(mean_squared_error(y_test, y_pred_test))
        mae = mean_absolute_error(y_test, y_pred_test)
        print(f'Test Loss: RMSE={rmse:.2f}, MAE={mae:.2f}, SMAPE={s_mape:.2f}')

        save_performance(
            self.region,
            rmse,
            mae,
            s_mape,
            MODEL_FL_LSTM,
            server_round,
            np.max(np.abs(np.concatenate((y_train, y_test)))),
        )

        # Plot results
        self.round += 1

        if save_artifacts:
            fig, ax = plt.subplots(figsize=(8, 5))

            index_array = self.index.to_numpy()

            ax.plot(index_array, np.concatenate((y_train, y_test), axis=0), label='Reported cases', c='black')
            # plt.plot(data_df.index, torch.cat((y_train, y_test), dim=0).numpy(), label='Data')
            ax.plot(index_array[:len(y_pred_train)], y_pred_train, label='FL-LSTM prediction (Train)')
            ax.plot(index_array[len(y_pred_train):], y_pred_test, label='FL-LSTM prediction (Test)')
            ax.set_title('FL-LSTM Prediction')
            ax.set_xlabel('Time')
            ax.set_ylabel('Number of reported cases')
            ax.legend()

            # Adjust layout
            plt.tight_layout()
            plt.savefig(f'{output_dir}/{self.region}-fl_lstm-round_{server_round}.png')
            plt.close(fig)  

        normalization_scale = max(
            float(np.max(np.abs(np.concatenate((y_train, y_test))))),
            np.finfo(float).eps,
        )
        metrics = {
            "rmse": rmse,
            "mae": mae,
            "smape": s_mape,
            "nrmse": rmse / normalization_scale,
            "nmae": mae / normalization_scale,
        }
        if server_round == NUM_ROUNDS:
            metrics["prediction_payload"] = json.dumps({
                "region": self.region,
                "dates": [date.isoformat() for date in self.index[len(self.x_train):]],
                "actual": y_test.tolist(),
                "predictions": y_pred_test.tolist(),
            })
            metrics["horizon_payload"] = json.dumps({
                "region": self.region,
                "horizons": _multi_horizon_predictions(
                    self.model,
                    torch.cat((self.x_train, self.x_test)),
                    torch.cat((self.y_train, self.y_test)),
                    self.scaler,
                    self.index,
                ),
            })
        return float(loss), len(self.x_test), metrics


def client_fn(cid: str) -> FlowerClient:
    """Create a Flower client representing a single organization."""
    print(f'client_fn: cid={cid}')
    random.seed(seed + int(cid))
    np.random.seed(seed + int(cid))
    torch.manual_seed(seed + int(cid))
    region = REGIONS[int(cid)]

    # Create a  single Flower client representing a single organization
    return FlowerClient(region).to_client()


def weighted_average(metrics: List[Tuple[int, Metrics]]) -> Metrics:
    examples = [num_examples for num_examples, _ in metrics]
    total_examples = sum(examples)

    if total_examples == 0:
        raise ValueError("Cannot aggregate metrics without client examples")

    def weighted_metric(name):
        return sum(num_examples * metric[name] for num_examples, metric in metrics) / total_examples

    return {
        "rmse": weighted_metric("rmse"),
        "mae": weighted_metric("mae"),
        "smape": weighted_metric("smape"),
        "nrmse": weighted_metric("nrmse"),
        "nmae": weighted_metric("nmae"),
    }


class AuditedFedAvg(fl.server.strategy.FedAvg):
    """FedAvg strategy that records client participation for every round."""

    def _record_round_status(self, phase, server_round, successful, failed):
        status_path = f'{output_dir}/round_status.csv'
        status = pd.DataFrame([{
            "phase": phase,
            "round": server_round,
            "successful_clients": successful,
            "failed_clients": failed,
            "expected_clients": NUM_CLIENTS,
        }])
        status.to_csv(
            status_path,
            mode="a",
            header=not os.path.exists(status_path),
            index=False,
        )

    def aggregate_fit(self, server_round, results, failures):
        self._record_round_status("fit", server_round, len(results), len(failures))
        fit_metrics = pd.DataFrame([
            {
                "round": server_round,
                "region": fit_result.metrics.get("region", "unknown"),
                "train_loss": fit_result.metrics.get("train_loss"),
                "local_epochs": fit_result.metrics.get("local_epochs"),
            }
            for _, fit_result in results
        ])
        if not fit_metrics.empty:
            fit_metrics.to_csv(
                f'{output_dir}/fit_metrics.csv',
                mode="a",
                header=not os.path.exists(f'{output_dir}/fit_metrics.csv'),
                index=False,
            )
        return super().aggregate_fit(server_round, results, failures)

    def aggregate_evaluate(self, server_round, results, failures):
        self._record_round_status("evaluate", server_round, len(results), len(failures))
        if server_round == NUM_ROUNDS:
            predictions_by_region = {}
            horizons_by_region = {}
            for _, evaluate_result in results:
                payload = evaluate_result.metrics.get("prediction_payload")
                if payload is not None:
                    decoded = json.loads(payload)
                    predictions_by_region[decoded["region"]] = decoded
                horizon_payload = evaluate_result.metrics.get("horizon_payload")
                if horizon_payload is not None:
                    decoded = json.loads(horizon_payload)
                    horizons_by_region[decoded["region"]] = decoded["horizons"]
            paper_limits = save_figure_4a(horizons_by_region, server_round)
            save_figure_4b(predictions_by_region, server_round, paper_limits)
        loss, metrics = super().aggregate_evaluate(server_round, results, failures)
        if metrics:
            metrics_path = f'{output_dir}/round_metrics.csv'
            aggregate = pd.DataFrame([{
                "round": server_round,
                "loss": loss,
                **metrics,
            }])
            aggregate.to_csv(
                metrics_path,
                mode="a",
                header=not os.path.exists(metrics_path),
                index=False,
            )
        return loss, metrics


if __name__ == '__main__':
    save_run_metadata()
    # Obtain the parameters from command line input
    if len(sys.argv) > 1 and sys.argv[1].lstrip("-").isdigit():
        current_round = int(sys.argv[1])
        print("current_round: ", current_round)

    # Create FedAvg strategy
    strategy = AuditedFedAvg(
        fraction_fit=1.0,  # Sample 100% of available clients for training
        fraction_evaluate=0.5,  # Sample 50% of available clients for evaluation
        min_fit_clients=3,  # Never sample less than 3 clients for training
        min_evaluate_clients=3,  # Never sample less than 3 clients for evaluation
        min_available_clients=3,  # Wait until all 3 clients are available
        on_evaluate_config_fn=lambda server_round: {"server_round": server_round},
        evaluate_metrics_aggregation_fn=weighted_average,  # <-- pass the metric aggregation function
    )

    # Specify the resources each of your clients need. By default, each
    # client will be allocated 1x CPU and 0x GPUs
    client_resources = {"num_cpus": 1, "num_gpus": 0.0}
    if DEVICE.type == "cuda":
        # here we are asigning an entire GPU for each client.
        client_resources = {"num_cpus": 1, "num_gpus": 1.0}
        # Refer to our documentation for more details about Flower Simulations
        # and how to setup these `client_resources`.

    experiment_rounds = 1 if PAPER_MODE else ROUND
    for i in range(1, experiment_rounds + 1):
        current_round = current_round + 1

        # Try LSTM for each region, without using federated learning
        for region in REGIONS:
            index, x_train, x_test, y_train, y_test, scaler = load_datasets(region)
            lstm(region, index, x_train, x_test, y_train, y_test, scaler)
        if PAPER_MODE:
            centralized_lstm()

        # Start simulation
        fl.simulation.start_simulation(
            client_fn=client_fn,
            num_clients=NUM_CLIENTS,
            config=fl.server.ServerConfig(num_rounds=NUM_ROUNDS),
            strategy=strategy,
            client_resources=client_resources,
        )

    print('Process completed.')

    excel_files = [f'{output_dir}/performance_{region}.xlsx' for region in REGIONS]
    merged_data = pd.concat([pd.read_excel(file) for file in excel_files], ignore_index=True)
    merged_data.to_excel(f'{output_dir}/performance.xlsx', index=False)
    save_round_summary()
