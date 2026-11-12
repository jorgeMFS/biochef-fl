#!/usr/bin/env python3
"""Build compact tables from completed Flower server output directories.

Each input directory must contain the files produced by one server run:
run_metadata.json, round_metrics.csv, and performance_<region>.xlsx files.
Raw output directories are never modified.
"""

import argparse
import json
from pathlib import Path

import pandas as pd


REGIONS = {"Portugal", "Guangdong", "Macau"}


def read_run(run_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    server_dir = run_dir / "server" if (run_dir / "server").is_dir() else run_dir
    clients_dir = run_dir / "clients" if (run_dir / "clients").is_dir() else None
    metadata_path = server_dir / "run_metadata.json"
    metrics_path = server_dir / "round_metrics.csv"
    if not metadata_path.exists() or not metrics_path.exists():
        raise FileNotFoundError(
            f"{server_dir} must contain run_metadata.json and round_metrics.csv"
        )

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    global_metrics = pd.read_csv(metrics_path)
    required_global = {"round", "rmse", "mae", "smape"}
    missing = required_global - set(global_metrics.columns)
    if missing:
        raise ValueError(f"{metrics_path} is missing columns: {sorted(missing)}")

    global_metrics["run"] = str(run_dir)
    global_metrics["seed"] = metadata.get("seed")
    global_metrics["learning_rate"] = metadata.get("learning_rate")
    global_metrics["reset_optimizer"] = metadata.get("reset_optimizer")
    global_metrics["train_only_scaler"] = metadata.get("train_only_scaler")
    global_metrics["metric_scope"] = "global"

    regional_frames = []
    workbook_sources = [(server_dir, "server")]
    if clients_dir is not None:
        workbook_sources.append((clients_dir, "clients"))
    for source_dir, source_role in workbook_sources:
        for workbook in sorted(source_dir.glob("performance_*.xlsx")):
            if workbook.name == "performance.xlsx":
                continue
            region = workbook.stem.removeprefix("performance_")
            if region not in REGIONS:
                continue
            regional = pd.read_excel(workbook)
            if "Model" not in regional.columns:
                raise ValueError(f"{workbook} is missing the Model column")
            if "Round" not in regional.columns and "CurrentRound" in regional.columns:
                regional = regional.rename(columns={"CurrentRound": "Round"})
            if "Round" not in regional.columns:
                raise ValueError(f"{workbook} is missing Round/CurrentRound")
            regional["run"] = str(run_dir)
            regional["seed"] = metadata.get("seed")
            regional["learning_rate"] = metadata.get("learning_rate")
            regional["reset_optimizer"] = metadata.get("reset_optimizer")
            regional["train_only_scaler"] = metadata.get("train_only_scaler")
            regional["Region"] = region
            regional["source_role"] = source_role
            regional["metric_scope"] = "regional"
            regional_frames.append(regional)

    if not regional_frames:
        raise ValueError(f"No regional performance workbooks found in {run_dir}")
    return pd.concat(regional_frames, ignore_index=True), global_metrics


def write_summary(run_dirs: list[Path], output_dir: Path) -> None:
    regional_runs = []
    global_runs = []
    for run_dir in run_dirs:
        regional, global_metrics = read_run(run_dir)
        regional_runs.append(regional)
        global_runs.append(global_metrics)

    regional_all = pd.concat(regional_runs, ignore_index=True)
    global_all = pd.concat(global_runs, ignore_index=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    regional_all.to_csv(output_dir / "regional_all_rounds.csv", index=False)
    global_all.to_csv(output_dir / "global_all_rounds.csv", index=False)

    final_round = (
        regional_all.sort_values(["run", "Region", "Model", "Round"])
        .groupby(["run", "Region", "Model"], as_index=False)
        .tail(1)
    )
    final_round.to_csv(output_dir / "regional_final_round.csv", index=False)

    if "RMSE" in regional_all:
        best_round = (
            regional_all.loc[
                regional_all.groupby(["run", "Region", "Model"])["RMSE"].idxmin()
            ]
            .copy()
        )
        best_round.to_csv(output_dir / "regional_best_round.csv", index=False)

    summary_columns = [
        "RMSE", "MAE", "SMAPE", "nRMSE", "nMAE",
    ]
    available = [column for column in summary_columns if column in final_round]
    grouping = [
        "learning_rate", "reset_optimizer", "train_only_scaler",
        "Region", "Model",
    ]
    summary = (
        final_round.groupby(grouping, dropna=False)[available]
        .agg(["mean", "std"])
        .reset_index()
    )
    summary.columns = [
        "_".join(str(part) for part in column if str(part) != "").rstrip("_")
        if isinstance(column, tuple) else str(column)
        for column in summary.columns
    ]
    summary.to_csv(output_dir / "regional_final_mean_std.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize completed Flower server output directories."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("processed_results"),
        help="Directory for generated CSV tables (default: processed_results)",
    )
    parser.add_argument(
        "run_dirs",
        nargs="+",
        type=Path,
        help="One server output directory per completed run",
    )
    args = parser.parse_args()
    write_summary(args.run_dirs, args.output_dir)
    print(f"Wrote summary tables to {args.output_dir}")


if __name__ == "__main__":
    main()
