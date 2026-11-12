#!/usr/bin/env python3
"""Create compact, report-ready tables from summarize_results.py output."""

import argparse
from pathlib import Path

import pandas as pd


def configuration_name(row: pd.Series) -> str:
    lr = "lr01" if row["learning_rate"] == 0.01 else "lr003"
    optimizer = "reset" if bool(row["reset_optimizer"]) else "persistent"
    scaler = "trainonly" if bool(row["train_only_scaler"]) else "full"
    return f"{lr}_{optimizer}_{scaler}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("analysis_results"))
    args = parser.parse_args()

    summary_dir = args.summary_dir
    args.output_dir.mkdir(parents=True, exist_ok=True)
    global_all = pd.read_csv(summary_dir / "global_all_rounds.csv")
    regional_all = pd.read_csv(summary_dir / "regional_all_rounds.csv")

    for frame in (global_all, regional_all):
        frame["configuration"] = frame.apply(configuration_name, axis=1)

    global_rows = []
    for run, group in global_all.groupby("run", sort=True):
        best = group.loc[group["rmse"].idxmin()]
        final = group.loc[group["round"].idxmax()]
        global_rows.append(
            {
                "run": run,
                "seed": int(best["seed"]),
                "configuration": best["configuration"],
                "learning_rate": best["learning_rate"],
                "reset_optimizer": bool(best["reset_optimizer"]),
                "train_only_scaler": bool(best["train_only_scaler"]),
                "best_round": int(best["round"]),
                "best_rmse": best["rmse"],
                "final_round": int(final["round"]),
                "final_rmse": final["rmse"],
                "final_minus_best_rmse": final["rmse"] - best["rmse"],
            }
        )
    global_by_run = pd.DataFrame(global_rows)
    global_by_run.to_csv(args.output_dir / "global_best_and_final_by_seed.csv", index=False)

    global_by_config = (
        global_by_run.groupby("configuration", as_index=False)
        .agg(
            seeds=("seed", "count"),
            best_round_mean=("best_round", "mean"),
            best_round_std=("best_round", "std"),
            best_rmse_mean=("best_rmse", "mean"),
            best_rmse_std=("best_rmse", "std"),
            final_rmse_mean=("final_rmse", "mean"),
            final_rmse_std=("final_rmse", "std"),
        )
    )
    global_by_config.to_csv(args.output_dir / "global_best_and_final_by_configuration.csv", index=False)

    round_mean = (
        global_all.groupby(["configuration", "round"], as_index=False)
        .agg(rmse_mean=("rmse", "mean"), rmse_std=("rmse", "std"))
    )
    round_mean.to_csv(args.output_dir / "global_rmse_by_round.csv", index=False)

    regional_final = (
        regional_all.sort_values(["run", "Region", "Model", "Round"])
        .groupby(["run", "Region", "Model"], as_index=False)
        .tail(1)
    )
    regional_best = regional_all.loc[
        regional_all.groupby(["run", "Region", "Model"])["RMSE"].idxmin()
    ].copy()
    for frame in (regional_final, regional_best):
        frame["configuration"] = frame.apply(configuration_name, axis=1)

    def aggregate(frame: pd.DataFrame, prefix: str) -> pd.DataFrame:
        result = (
            frame.groupby(["configuration", "Region", "Model"], as_index=False)
            .agg(
                seeds=("seed", "count"),
                RMSE_mean=("RMSE", "mean"),
                RMSE_std=("RMSE", "std"),
                MAE_mean=("MAE", "mean"),
                MAE_std=("MAE", "std"),
                SMAPE_mean=("SMAPE", "mean"),
                SMAPE_std=("SMAPE", "std"),
                round_mean=("Round", "mean"),
            )
        )
        result.to_csv(args.output_dir / f"regional_{prefix}_mean_std.csv", index=False)
        return result

    aggregate(regional_final, "final")
    aggregate(regional_best, "best")
    regional_best.to_csv(args.output_dir / "regional_best_by_seed.csv", index=False)
    for frame, filename in (
        (regional_final, "presentation_table3_config_c_final.csv"),
        (regional_best, "presentation_table3_config_c_best_observed.csv"),
    ):
        frame.loc[
            frame["configuration"].eq("lr003_persistent_full")
        ].to_csv(args.output_dir / filename, index=False)

    # Optional fixed-round reference values for comparison with the paper.
    # These are not used to select the primary result.
    checkpoints = global_all[global_all["round"].isin([32, 71, 200])]
    checkpoint_summary = (
        checkpoints.groupby(["configuration", "round"], as_index=False)
        .agg(rmse_mean=("rmse", "mean"), rmse_std=("rmse", "std"))
    )
    checkpoint_summary.to_csv(
        args.output_dir / "global_paper_reference_checkpoints.csv", index=False
    )

    # Secondary paper-reference analysis: choose the round minimizing each
    # client's training loss through the paper's reported threshold (round 71).
    preinstability = []
    for run in sorted(global_all["run"].unique()):
        fit_path = Path(run) / "server" / "fit_metrics.csv"
        if not fit_path.exists():
            continue
        fit = pd.read_csv(fit_path)
        fit = fit[fit["round"] <= 71]
        for region, group in fit.groupby("region"):
            selected = group.loc[group["train_loss"].idxmin()]
            preinstability.append(
                {
                    "run": run,
                    "seed": int(global_all.loc[global_all["run"].eq(run), "seed"].iloc[0]),
                    "configuration": configuration_name(
                        global_all.loc[global_all["run"].eq(run)].iloc[0]
                    ),
                    "Region": region,
                    "selected_round": int(selected["round"]),
                    "minimum_train_loss": selected["train_loss"],
                }
            )
    preinstability_df = pd.DataFrame(preinstability)
    preinstability_df.to_csv(
        args.output_dir / "training_loss_best_paper_reference_by_region.csv",
        index=False,
    )

    regional_pre = regional_all.merge(
        preinstability_df[["run", "Region", "selected_round"]],
        left_on=["run", "Region", "Round"],
        right_on=["run", "Region", "selected_round"],
        how="inner",
    )
    regional_pre = regional_pre[regional_pre["Model"].eq("FL-LSTM")].copy()
    regional_pre.to_csv(
        args.output_dir / "regional_best_paper_reference_by_seed.csv",
        index=False,
    )
    if not regional_pre.empty:
        (
            regional_pre.groupby(["configuration", "Region", "Model"], as_index=False)
            .agg(
                seeds=("seed", "count"),
                selected_round_mean=("selected_round", "mean"),
                RMSE_mean=("RMSE", "mean"),
                RMSE_std=("RMSE", "std"),
                MAE_mean=("MAE", "mean"),
                MAE_std=("MAE", "std"),
                SMAPE_mean=("SMAPE", "mean"),
                SMAPE_std=("SMAPE", "std"),
            )
            .to_csv(
                args.output_dir / "regional_best_paper_reference_mean_std.csv",
                index=False,
            )
        )

    print(f"Wrote analysis tables to {args.output_dir}")


if __name__ == "__main__":
    main()
