# Flower paper-reproduction experiment

This folder contains the Flower implementation used to reproduce the paper's
COVID-19 forecasting comparison for Portugal, Guangdong, and Macau:

- **L-LSTM**: an independent local model for each region.
- **C-LSTM**: one centralized model trained on pooled regional training data.
- **F-LSTM**: one shared model trained with Flower FedAvg.

The three regions are equal federated clients. Macau is not a held-out target
domain. The global model is evaluated on each region's own test data without
local personalization.

## Repository contents

- `main.py`
- `server.py`
- `client.py`
- `summarize_results.py`
- `analyze_results.py`
- `requirements.txt`
- `README.md`
- `notes.md`

The result-generation scripts are included in the experiment record. Their
CSV outputs are generated locally and are intentionally excluded from version
control because the repository policy excludes data and files derived from
real data.

## Requirements

- Python 3.10+ recommended
- One Flower server and three client machines/processes
- The input workbook supplied separately at `data/input/c19_data_for_FL.xlsx`
- Network connectivity between clients and the server

The input workbook is not included in this experiment folder. It is required
at the documented path for rerunning the experiment.

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Running one experiment

Start the server:

```bash
python server.py --paper --rounds 200 --lr 0.01 \
  --reset-optimizer --seed 1
```

Start one client for each region, using the same configuration flags:

```bash
python client.py --paper --rounds 200 --lr 0.01 \
  --reset-optimizer --seed 1 \
  --region Portugal --server SERVER_IP:8080
```

Repeat the client command for `Guangdong` and `Macau`. The server writes the
server-side artifacts; the corresponding client-side artifacts contain the
regional FL-LSTM workbooks and training-loss plots. They also contain the
federated plots generated during training.
`summarize_results.py` reads both `server/` and `clients/` when both are
present.

## Protocol

- data period: 2021-11-24 to 2023-01-08;
- training through 2022-10-17;
- test from 2022-10-18;
- seven-day moving average;
- seven-day input window;
- one local epoch per federated round;
- 200 communication rounds;
- full-batch training (`BATCH_SIZE` is not used);
- Adam optimizer;
- FedAvg weighted by client examples.

The default scaler is fitted to the complete regional series for comparability
with the earlier sandbox and paper-oriented runs. The thesis-compliant option
is `--train-only-scaler`, which fits each regional scaler only to its local
training data. These two protocols must be reported separately.

## Options

| Option | Default | Meaning |
|---|---:|---|
| `--paper` | off | Enables the paper dates and preprocessing |
| `--rounds N` | 10, or 200 with `--paper` | Federated rounds |
| `--lr VALUE` | `0.003` | Adam learning rate |
| `--seed N` | `42` | Reproducibility seed |
| `--reset-optimizer` | off | Fresh Adam state for each fit round |
| `--train-only-scaler` | off | Fit scalers only on local training data |
| `--timesteps` | off | Use `(samples, 7, 1)` input layout |

## The 18 runs

Each seed is a separate complete server/client execution. The completed
experiment matrix consists of the following configurations, each evaluated
with seeds 1, 2, and 3:

| Group | Command flags | Purpose |
|---|---|---|
| A | `--paper --rounds 200 --lr 0.01 --reset-optimizer` | fresh optimizer, full-series scaler |
| B | `--paper --rounds 200 --lr 0.003 --reset-optimizer` | lower learning rate, fresh optimizer |
| C | `--paper --rounds 200 --lr 0.003` | lower learning rate, persistent optimizer |
| D | A plus `--train-only-scaler` | fresh optimizer, training-only scaler |
| E | B plus `--train-only-scaler` | lower learning rate, fresh optimizer, training-only scaler |
| F | C plus `--train-only-scaler` | lower learning rate, persistent optimizer, training-only scaler |

There are therefore 6 configurations x 3 seeds = 18 runs.

## Run outputs

The server run directory contains:

- `run_metadata.json`;
- `round_summary.json`;
- `round_metrics.csv`;
- `fit_metrics.csv`;
- `round_status.csv`;
- `performance_Portugal.xlsx`;
- `performance_Guangdong.xlsx`;
- `performance_Macau.xlsx`;
- Figure 4(a), Figure 4(b), and diagnostic PNG files.

The generated `processed_results/` and `analysis_results/` directories contain
summary tables for local review. They are derived from real data and are
therefore excluded from version control together with the raw results, but can be generated locally with the scripts `summarize_results.py` and `analyze_results.py`, respectively.

## Summarizing completed runs

`summarize_results.py` does not train anything. It reads one server output
directory per run and produces compact CSV tables. It includes all model rows
present in the regional workbooks (LSTM, C-LSTM, and FL-LSTM).

Example:

```bash
python summarize_results.py --output-dir processed_results \
  raw_results/A_lr01_reset_full/seed_1 \
  raw_results/A_lr01_reset_full/seed_2 \
  raw_results/A_lr01_reset_full/seed_3
```

Pass all completed `seed_*` directories to reproduce the derived tables.

Alternatively, use a wildcard to summarize all runs in one command:

```bash
python summarize_results.py --output-dir processed_results \
  raw_results/*/seed_*
```  

With the
current six configurations and three seeds, this means 18 run directories.
The output directory
contains:

- `regional_all_rounds.csv`;
- `global_all_rounds.csv`;
- `regional_final_round.csv`;
- `regional_best_round.csv`;
- `regional_final_mean_std.csv`.

The last file provides final-round mean and standard deviation across the
supplied seeds, grouped by learning rate, optimizer policy, scaler policy,
region, and model. These tables support the paper's Table 3 comparison,
round-200 versus best-round reporting, and the analysis of training-loss
oscillations.

For smaller report-ready tables, run:

```bash
python analyze_results.py processed_results \
  --output-dir analysis_results
```

This creates per-seed and per-configuration global comparisons, regional
final/best-round summaries, and a global RMSE trajectory table. It also
produces a separate paper-reference analysis using the paper's reported
round-71 threshold. The outputs are derived files and are excluded
from version control; the Python analysis scripts remain part of the
experiment record.

The primary experiment-specific instability estimates are recorded in
`analysis_results/observed_instability_onsets.csv`. They are approximate
visual observations and are used to interpret the training-loss curves. The
paper-reference outputs are named `*paper_reference*` and are retained only
for a clearly labelled comparison with the source paper.

The two `presentation_table3_*.csv` files are regenerated by
`analyze_results.py`; the observed-instability CSV is manually curated and
must be preserved when regenerating the derived tables.

## Limitations

The available Guangdong workbook has a lower outbreak magnitude than the
paper's Figure 4. Do not multiply or alter the data to force agreement.
Exact reproduction requires the original WHO/China CDC data version used by the paper.
