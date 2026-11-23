# Flower vs. NVFlare local replication

This experiment compares Flower 1.7.0 and NVFlare 2.9.1 on the same federated
LSTM forecasting protocol. It does not contain model weights or result files
derived from the input workbook.

## Repository contents

- `flower_main.py`: local Flower/FedAvg implementation.
- `nvflare_main.py`: local NVFlare/FedJob implementation.
- `requirements.txt`: Python dependencies.
- `table.md`: numerical and framework comparison.
- `README.md`: setup and reproduction instructions.
- `notes.md`: experiment record.

The input workbook is required separately at:

```text
data/input/c19_data_for_FL.xlsx
```

## Requirements

- Python 3.10 or later is recommended.
- CPU is sufficient.
- OpenPyXL must be able to read the regional Excel sheets.
- The experiment is local: no inbound connection is required on the client
  machines.

Install:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r experiments/02-nvflare-flower-comparison/requirements.txt
```

## Protocol

All runs use:

- regions: Portugal, Macau, and Guangdong;
- model: PyTorch LSTM, hidden size 64, 2 layers, dropout 0;
- input window: 7 observations;
- moving average: 7 observations, with Portugal double-smoothed;
- period: 2021-11-24 to 2023-01-08;
- training: through 2022-10-17;
- test: from 2022-10-18;
- one local epoch per round;
- Adam learning rate 0.003;
- persistent optimizer state;
- FedAvg aggregation weighted by client examples;
- 200 federated rounds;
- seed 1 for the primary local comparison;
- separate MinMax scalers fitted only on each region's training split.

The primary result is the weighted test evaluation at round 200 and the
lowest test RMSE observed during the run. The best round is descriptive:
it is not used for early stopping or model selection.

## Running Flower

```bash
python experiments/02-nvflare-flower-comparison/flower_main.py \
  --rounds 200 \
  --lr 0.003 \
  --seed 1
```

To write artifacts to a chosen directory:

```bash
python experiments/02-nvflare-flower-comparison/flower_main.py \
  --run-dir results/flower_seed_1 \
  --rounds 200 \
  --lr 0.003 \
  --seed 1
```

## Running NVFlare

```bash
python experiments/02-nvflare-flower-comparison/nvflare_main.py \
  --rounds 200 \
  --lr 0.003 \
  --seed 1
 ```

This run uses NVFlare's local simulator and three external regional training
processes. To export the generated job without starting it:

```bash
python experiments/02-nvflare-flower-comparison/nvflare_main.py \
  --rounds 200 \
  --lr 0.003 \
  --seed 1 \
  --export-dir /tmp/nvflare-job
```

The NVFlare POC setup is separate from the local simulator and requires project
provisioning before a real multi-machine deployment. It was not used for the
primary numerical comparison.

## Outputs

Each implementation writes:

- `run_metadata.json`;
- `round_metrics.csv`;
- `fit_metrics.csv`;
- `round_summary.json`.

For NVFlare, regional files are also written under one subdirectory per region.

## Limitations

- The primary run is local; it does not verify routing or firewall behavior
  across TRE boundaries.
- The NVFlare POC network observations were made locally and do not establish
  a remote TRE deployment.
- The local run was not configured with secure aggregation or differential
  privacy. The framework capabilities are not performance guarantees
  for this run.
