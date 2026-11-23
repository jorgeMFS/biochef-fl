#!/usr/bin/env python3

import argparse
from datetime import datetime
import json
import os
import random
import sys
from collections import OrderedDict
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import MinMaxScaler

import nvflare.client as flare
from nvflare import FedJob
from nvflare.apis.fl_constant import FLMetaKey
from nvflare.app_common.abstract.fl_model import FLModel
from nvflare.app_common.aggregators.weighted_aggregation_helper import (
    WeightedAggregationHelper,
)
from nvflare.app_common.app_constant import AppConstants
from nvflare.app_common.app_event_type import AppEventType
from nvflare.app_opt.pt.file_model_persistor import PTFileModelPersistor
from nvflare.client.config import ExchangeFormat, TransferType
from nvflare.fuel.utils.constants import FrameworkType
from nvflare.fuel.utils.log_utils import center_message
from nvflare.job_config.script_runner import ScriptRunner

from nvflare.app_opt.pt.fedavg import PTFedAvg

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


class AuditedFedAvg(PTFedAvg):
    """FedAvg controller with post-aggregation global evaluation and summary export."""

    def __init__(self, *args, output_dir: str, **kwargs):
        kwargs.pop("model", None)
        super().__init__(*args, model=None, persistor_id="persistor", **kwargs)
        self.output_dir = output_dir
        self.task_check_period = 0.5

    def run(self) -> None:
        import nvflare.fuel.utils.fobs as fobs
        from nvflare.app_opt.pt.decomposers import TensorDecomposer

        fobs.register(TensorDecomposer)
        self.info(center_message("Start FedAvg with post-aggregation evaluation."))
        self.fl_ctx.set_prop(
            AppConstants.NUM_ROUNDS,
            self.num_rounds,
            private=True,
            sticky=False,
        )

        if self.model is not None:
            if isinstance(self.model, torch.nn.Module):
                model = FLModel(params=self.model.state_dict())
            elif isinstance(self.model, dict):
                model = FLModel(params=self.model)
            else:
                model = (
                    self.model
                    if isinstance(self.model, FLModel)
                    else FLModel(params=self.model)
                )
        else:
            model = self.load_model()

        model.start_round = self.start_round
        model.total_rounds = self.num_rounds
        os.makedirs(self.output_dir, exist_ok=True)
        global_metrics_path = os.path.join(self.output_dir, "round_metrics.csv")

        for self.current_round in range(
            self.start_round, self.start_round + self.num_rounds
        ):
            display_round = self.current_round + 1
            self.info(
                center_message(f"Round {self.current_round} started.", boarder_str="-")
            )
            model.current_round = self.current_round
            self.fl_ctx.set_prop(
                AppConstants.CURRENT_ROUND,
                self.current_round,
                private=True,
                sticky=False,
            )
            self.event(AppEventType.ROUND_STARTED)

            clients = self.sample_clients(self.num_clients)
            self._aggr_helper = WeightedAggregationHelper(
                exclude_vars=self.exclude_vars
            )
            self._aggr_metrics_helper = WeightedAggregationHelper()
            self._all_metrics = True
            self._received_count = 0
            self._expected_count = len(clients)
            self._params_type = None
            self._site_metric_weights = {}
            self._aggregation_failed = False

            self.send_model(
                task_name=self.task_name,
                targets=clients,
                data=model,
                callback=self._aggregate_one_result,
            )

            while self.get_num_standing_tasks():
                if self.abort_signal.triggered:
                    self.info("Abort signal triggered. Finishing FedAvg.")
                    return
                import time

                time.sleep(self.task_check_period)

            aggregate_results = self._get_aggregated_result()
            model = self.update_model(model, aggregate_results)

            model.current_round = self.current_round
            evaluation_results = self.broadcast_model(
                task_name="validate",
                targets=clients,
                data=model,
                min_responses=len(clients),
                blocking=True,
            )

            weighted_metrics = self._aggregate_evaluation_metrics(evaluation_results)
            if weighted_metrics:
                append_csv(
                    global_metrics_path,
                    {"round": display_round, **weighted_metrics},
                )

            self.save_model(model)
            self._maybe_cleanup_memory()

        save_round_summary(self.output_dir)
        self.info(center_message("Finished FedAvg."))

    def _aggregate_evaluation_metrics(self, results):
        if not results:
            return {}
        names = ("rmse", "mae", "smape", "nrmse", "nmae")
        weighted = {name: 0.0 for name in names}
        total_weight = 0.0
        for result in results:
            metrics = result.metrics or {}
            weight = float(
                (result.meta or {}).get(FLMetaKey.NUM_STEPS_CURRENT_ROUND, 1.0)
            )
            total_weight += weight
            for name in names:
                if name in metrics:
                    weighted[name] += weight * float(metrics[name])
        if total_weight <= 0:
            return {}
        return {name: weighted[name] / total_weight for name in names}


def run_client(args):
    region_index = REGIONS.index(args.region)
    region_seed = args.seed + region_index
    random.seed(region_seed)
    np.random.seed(region_seed)
    torch.manual_seed(region_seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(region_seed)

    os.makedirs(args.output_dir, exist_ok=True)

    _, x_train, x_test, y_train, y_test, y_scaler = load_datasets(
        args.region,
        args.data_path,
        args.train_only_scaler,
    )

    model = LSTM(seed=args.seed)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    flare.init()
    while flare.is_running():
        input_model = flare.receive()
        if input_model is None:
            break

        round_number = int(input_model.current_round or 0) + 1
        if input_model.params:
            model.load_state_dict(input_model.params)
        if args.reset_optimizer:
            optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

        if flare.is_train():
            model.train()
            outputs = model(x_train)
            optimizer.zero_grad()
            loss = criterion(outputs, y_train.unsqueeze(1))
            loss.backward()
            optimizer.step()

            train_loss = float(loss.item())
            append_csv(
                os.path.join(args.output_dir, "fit_metrics.csv"),
                {
                    "round": round_number,
                    "region": args.region,
                    "train_loss": train_loss,
                    "local_epochs": 1,
                },
            )

            model_params = OrderedDict(
                (name, value.detach().cpu())
                for name, value in model.state_dict().items()
            )
            flare.send(
                FLModel(
                    params=model_params,
                    metrics={"train_loss": train_loss},
                    current_round=round_number,
                    total_rounds=args.rounds,
                    meta={FLMetaKey.NUM_STEPS_CURRENT_ROUND: len(x_train)},
                )
            )
        else:
            metrics = evaluate_model(model, x_train, y_train, x_test, y_test, y_scaler)
            append_csv(
                os.path.join(args.output_dir, "round_metrics.csv"),
                {"round": round_number, "region": args.region, **metrics},
            )
            flare.send(
                FLModel(
                    metrics=metrics,
                    current_round=round_number,
                    total_rounds=args.rounds,
                    meta={FLMetaKey.NUM_STEPS_CURRENT_ROUND: len(x_test)},
                )
            )


def _default_data_path():
    repo_candidate = THIS_DIR.parent / "data/input/c19_data_for_FL.xlsx"
    if repo_candidate.exists():
        return str(repo_candidate)
    return str(THIS_DIR / "data/input/c19_data_for_FL.xlsx")


def main():
    from nvflare_main import AuditedFedAvg, LSTM

    parser = argparse.ArgumentParser()
    parser.add_argument("--client", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--region", choices=REGIONS)
    parser.add_argument("--data-path", default=_default_data_path())
    parser.add_argument("--output-dir")
    parser.add_argument("--run-dir")
    parser.add_argument("--lr", type=float, default=0.003)
    parser.add_argument("--rounds", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--reset-optimizer", action="store_true")
    parser.add_argument("--full-series-scaler", action="store_true")
    parser.add_argument("--export-dir")
    parser.add_argument(
        "--workspace",
        default=str(THIS_DIR / "simulator_workspaces"),
    )
    args = parser.parse_args()
    args.train_only_scaler = not args.full_series_scaler

    if args.client:
        if not args.region or not args.output_dir:
            raise ValueError("--client requires both --region and --output-dir")
        run_client(args)
        return

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

    job = FedJob(
        name=f"lstm_fedavg_{configuration}_seed_{args.seed}",
        min_clients=3,
    )
    controller = AuditedFedAvg(
        num_clients=3,
        num_rounds=args.rounds,
        save_filename="FL_global_model.pt",
        output_dir=str(run_dir),
    )
    persistor = PTFileModelPersistor(
        model={"path": "nvflare_main.LSTM", "args": {"seed": args.seed}},
        allow_numpy_conversion=False,
    )
    job.to_server(persistor, id="persistor")
    job.to_server(controller, id="controller")

    this_script = str(Path(__file__).resolve())
    for region in REGIONS:
        region_output_dir = run_dir / region
        common_args = (
            f" --client"
            f" --region {region}"
            f" --data-path {args.data_path}"
            f" --output-dir {region_output_dir}"
            f" --run-dir {run_dir}"
            f" --lr {args.lr}"
            f" --seed {args.seed}"
            f" --rounds {args.rounds}"
        )
        if args.reset_optimizer:
            common_args += " --reset-optimizer"
        if args.full_series_scaler:
            common_args += " --full-series-scaler"

        runner = ScriptRunner(
            script=this_script,
            script_args=common_args,
            launch_external_process=True,
            framework=FrameworkType.PYTORCH,
            server_expected_format=ExchangeFormat.PYTORCH,
            params_transfer_type=TransferType.FULL,
            launch_once=True,
        )
        job.to(runner, region)

    if args.export_dir:
        job.export_job(args.export_dir)
        print(f"Exported NVFlare job to {args.export_dir}")
        return

    print(
        f"Starting NVFlare local run ({run_dir}) with {len(REGIONS)} clients and {args.rounds} rounds..."
    )
    status = job.simulator_run(
        workspace=args.workspace,
        n_clients=None,
        clients=REGIONS,
        threads=3,
    )
    print(f"NVFlare local run status: {status}")


if __name__ == "__main__":
    main()
