#!/usr/bin/env python3

import argparse
from collections import OrderedDict
from datetime import datetime
import json
import os
from pathlib import Path
import random
import sys
from typing import List, Tuple

import flwr as fl
from flwr.common import Metrics
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import MinMaxScaler
import torch
import torch.nn as nn

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

DEVICE = torch.device("cpu")

REGIONS = ["Portugal", "Macau", "Guangdong"]
PAPER_START_DATE = "2021-11-24"
PAPER_TEST_START_DATE = "2022-10-18"
PAPER_END_DATE = "2023-01-08"
MOV_AVG_WIN = 7
WINDOW = 7
NUM_LAYERS = 2
HIDDEN_SIZE = 64
OUTPUT_SIZE = 1
DROPOUT = 0.0
NUM_CLIENTS = 3


class LSTM(nn.Module):
    def __init__(
        self,
        input_size=WINDOW,
        hidden_size=HIDDEN_SIZE,
        num_layers=NUM_LAYERS,
        output_size=OUTPUT_SIZE,
        dropout=DROPOUT,
        seed=None,
    ):
        super().__init__()
        if seed is not None:
            torch.manual_seed(seed)
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size, device=x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size, device=x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.dropout(out)
        return self.fc(out[:, -1, :])


def _make_sequences(values, window_size):
    sequences = np.asarray(
        [
            values[start : start + window_size]
            for start in range(len(values) - window_size)
        ],
        dtype=np.float32,
    )
    return sequences.reshape(-1, 1, window_size), values[window_size:]


def _load_paper_series(region, data_path):
    data_df = pd.read_excel(data_path, sheet_name=region, index_col="Date")
    data_df.index = pd.to_datetime(data_df.index)
    data_df = data_df[["NewCases"]].rolling(window=MOV_AVG_WIN).mean()
    if region == "Portugal":
        data_df = data_df.rolling(window=MOV_AVG_WIN).mean()
    return data_df.loc[PAPER_START_DATE:PAPER_END_DATE].dropna()


def load_datasets(region, data_path, train_only_scaler):
    data_df = _load_paper_series(region, data_path).resample("1D").mean()
    values = data_df["NewCases"].to_numpy(dtype=np.float32)
    if len(values) <= WINDOW:
        raise ValueError(f"Not enough data for a {WINDOW}-day window in {region}")

    raw_x, raw_y = _make_sequences(values, WINDOW)
    sequence_index = data_df.index[WINDOW:]

    split_at = int(
        np.flatnonzero(sequence_index >= pd.Timestamp(PAPER_TEST_START_DATE))[0]
    )
    if split_at <= 0 or split_at >= len(raw_y):
        raise ValueError(f"Invalid train/test split for {region}")

    x_scaler = MinMaxScaler()
    y_scaler = MinMaxScaler()
    if train_only_scaler:
        x_scaler.fit(raw_x[:split_at].reshape(-1, 1))
        y_scaler.fit(raw_y[:split_at].reshape(-1, 1))
    else:
        x_scaler.fit(values.reshape(-1, 1))
        y_scaler.fit(values.reshape(-1, 1))

    x_scaled = x_scaler.transform(raw_x.reshape(-1, 1)).reshape(raw_x.shape)
    y_scaled = y_scaler.transform(raw_y.reshape(-1, 1)).flatten()

    x_train = torch.tensor(x_scaled[:split_at], dtype=torch.float32)
    y_train = torch.tensor(y_scaled[:split_at], dtype=torch.float32)
    x_test = torch.tensor(x_scaled[split_at:], dtype=torch.float32)
    y_test = torch.tensor(y_scaled[split_at:], dtype=torch.float32)

    return sequence_index, x_train, x_test, y_train, y_test, y_scaler


def smape(y_true, y_pred):
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


def evaluate_model(model, x_train, y_train, x_test, y_test, y_scaler):
    model.eval()
    with torch.no_grad():
        pred_test = model(x_test).cpu().numpy()

    train_raw = y_scaler.inverse_transform(
        y_train.cpu().numpy().reshape(-1, 1)
    ).flatten()
    test_raw = y_scaler.inverse_transform(y_test.cpu().numpy().reshape(-1, 1)).flatten()
    pred_test_raw = y_scaler.inverse_transform(pred_test).flatten()

    rmse = float(np.sqrt(mean_squared_error(test_raw, pred_test_raw)))
    mae = float(mean_absolute_error(test_raw, pred_test_raw))
    smape_value = smape(test_raw, pred_test_raw)
    normalization_scale = max(
        float(np.max(np.abs(np.concatenate((train_raw, test_raw))))),
        np.finfo(float).eps,
    )

    return {
        "rmse": rmse,
        "mae": mae,
        "smape": smape_value,
        "nrmse": rmse / normalization_scale,
        "nmae": mae / normalization_scale,
        "normalization_scale": normalization_scale,
    }


def append_csv(path, row):
    frame = pd.DataFrame([row])
    frame.to_csv(path, mode="a", header=not os.path.exists(path), index=False)


def save_round_summary(output_dir):
    path = os.path.join(output_dir, "round_metrics.csv")
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
    with open(
        os.path.join(output_dir, "round_summary.json"), "w", encoding="utf-8"
    ) as handle:
        json.dump(summary, handle, indent=2)


def save_run_metadata(run_dir, args, data_path):
    metadata = {
        "seed": args.seed,
        "learning_rate": args.lr,
        "reset_optimizer": args.reset_optimizer,
        "train_only_scaler": args.train_only_scaler,
        "window": WINDOW,
        "moving_average_window": MOV_AVG_WIN,
        "federated_local_epochs": 1,
        "rounds": args.rounds,
        "regions": REGIONS,
        "paper_start_date": PAPER_START_DATE,
        "paper_test_start_date": PAPER_TEST_START_DATE,
        "paper_end_date": PAPER_END_DATE,
        "data_path": str(data_path),
    }
    with open(
        os.path.join(run_dir, "run_metadata.json"), "w", encoding="utf-8"
    ) as handle:
        json.dump(metadata, handle, indent=2)


def set_parameters(model, parameters: List[np.ndarray]):
    params_dict = zip(model.state_dict().keys(), parameters)
    state_dict = OrderedDict({k: torch.Tensor(v) for k, v in params_dict})
    model.load_state_dict(state_dict, strict=True)


def get_parameters(model) -> List[np.ndarray]:
    return [val.cpu().numpy() for _, val in model.state_dict().items()]


class FlowerClient(fl.client.NumPyClient):
    def __init__(
        self, region, data_path, learning_rate, reset_optimizer, train_only_scaler, seed
    ):
        self.region = region
        self.learning_rate = learning_rate
        self.reset_optimizer = reset_optimizer
        _, self.x_train, self.x_test, self.y_train, self.y_test, self.y_scaler = (
            load_datasets(region, data_path, train_only_scaler)
        )
        self.model = LSTM(seed=seed)
        self.criterion = nn.MSELoss()
        self.optimizer = torch.optim.Adam(
            self.model.parameters(), lr=self.learning_rate
        )

    def get_parameters(self, config):
        return get_parameters(self.model)

    def fit(self, parameters, config):
        set_parameters(self.model, parameters)
        if self.reset_optimizer:
            self.optimizer = torch.optim.Adam(
                self.model.parameters(), lr=self.learning_rate
            )

        self.model.train()
        outputs = self.model(self.x_train)
        self.optimizer.zero_grad()
        loss = self.criterion(outputs, self.y_train.unsqueeze(1))
        loss.backward()
        self.optimizer.step()

        return (
            get_parameters(self.model),
            len(self.x_train),
            {
                "region": self.region,
                "train_loss": float(loss.item()),
                "local_epochs": 1,
            },
        )

    def evaluate(self, parameters, config):
        set_parameters(self.model, parameters)
        metrics = evaluate_model(
            self.model,
            self.x_train,
            self.y_train,
            self.x_test,
            self.y_test,
            self.y_scaler,
        )
        eval_metrics = {k: v for k, v in metrics.items() if k != "normalization_scale"}
        return float(metrics["rmse"]), len(self.x_test), eval_metrics


def weighted_average(metrics: List[Tuple[int, Metrics]]) -> Metrics:
    examples = [num_examples for num_examples, _ in metrics]
    total_examples = sum(examples)
    if total_examples == 0:
        raise ValueError("Cannot aggregate metrics without client examples")

    names = ("rmse", "mae", "smape", "nrmse", "nmae")
    return {
        name: sum(
            num_examples * float(metric[name]) for num_examples, metric in metrics
        )
        / total_examples
        for name in names
        if all(name in metric for _, metric in metrics)
    }


class AuditedFedAvg(fl.server.strategy.FedAvg):
    """FedAvg strategy with round metric logging matching NVFlare outputs."""

    def __init__(self, *args, output_dir: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_dir = output_dir

    def aggregate_fit(self, server_round, results, failures):
        rows = [
            {
                "round": server_round,
                "region": fit_res.metrics.get("region", "unknown"),
                "train_loss": fit_res.metrics.get("train_loss"),
                "local_epochs": fit_res.metrics.get("local_epochs"),
            }
            for _, fit_res in results
        ]
        for row in rows:
            append_csv(os.path.join(self.output_dir, "fit_metrics.csv"), row)
        return super().aggregate_fit(server_round, results, failures)

    def aggregate_evaluate(self, server_round, results, failures):
        loss, metrics = super().aggregate_evaluate(server_round, results, failures)
        if metrics:
            append_csv(
                os.path.join(self.output_dir, "round_metrics.csv"),
                {"round": server_round, **metrics},
            )
        return loss, metrics


def _default_data_path():
    repo_candidate = THIS_DIR.parent / "data/input/c19_data_for_FL.xlsx"
    if repo_candidate.exists():
        return str(repo_candidate)
    return str(THIS_DIR / "data/input/c19_data_for_FL.xlsx")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", default=_default_data_path())
    parser.add_argument("--run-dir")
    parser.add_argument("--lr", type=float, default=0.003)
    parser.add_argument("--rounds", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--reset-optimizer", action="store_true")
    parser.add_argument("--full-series-scaler", action="store_true")
    args = parser.parse_args()
    args.train_only_scaler = not args.full_series_scaler

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    optimizer_policy = "reset" if args.reset_optimizer else "persistent"
    scaler_policy = "full" if args.full_series_scaler else "trainonly"
    lr_tag = f"lr{args.lr:g}".replace(".", "")
    configuration = f"{lr_tag}_{optimizer_policy}_{scaler_policy}"

    if args.run_dir:
        run_dir = Path(args.run_dir)
    else:
        run_stamp = datetime.now().strftime("%m/%d_%H%M%S_%f")
        run_dir = THIS_DIR / "results" / configuration / f"seed_{args.seed}" / run_stamp

    run_dir.mkdir(parents=True, exist_ok=True)
    save_run_metadata(str(run_dir), args, args.data_path)

    def client_fn(cid: str):
        region_index = int(cid)
        region_seed = args.seed + region_index
        random.seed(region_seed)
        np.random.seed(region_seed)
        torch.manual_seed(region_seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(region_seed)
        return FlowerClient(
            region=REGIONS[region_index],
            data_path=args.data_path,
            learning_rate=args.lr,
            reset_optimizer=args.reset_optimizer,
            train_only_scaler=args.train_only_scaler,
            seed=args.seed,
        ).to_client()

    strategy = AuditedFedAvg(
        output_dir=str(run_dir),
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_fit_clients=3,
        min_evaluate_clients=3,
        min_available_clients=3,
        on_evaluate_config_fn=lambda server_round: {"server_round": server_round},
        evaluate_metrics_aggregation_fn=weighted_average,
    )

    client_resources = {"num_cpus": 1, "num_gpus": 0.0}
    if DEVICE.type == "cuda":
        client_resources = {"num_cpus": 1, "num_gpus": 1.0}

    fl.simulation.start_simulation(
        client_fn=client_fn,
        num_clients=NUM_CLIENTS,
        config=fl.server.ServerConfig(num_rounds=args.rounds),
        strategy=strategy,
        client_resources=client_resources,
    )

    save_round_summary(str(run_dir))
    print("Process completed.")


if __name__ == "__main__":
    main()
