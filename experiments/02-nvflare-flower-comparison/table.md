## Experiment 02 — Local FL-LSTM Replication: Flower vs. NVFlare

### Protocol & Configuration
- **Task & Dataset:** Federated LSTM (`nn.LSTM` with `hidden_size=64`, `num_layers=2`, `dropout=0.0`, `window=7`, moving average window `7` with double smoothing for `Portugal`, `2021-11-24` to `2023-01-08`, test split from `2022-10-18`) across `Portugal`, `Macau`, and `Guangdong`.
- **Training & Scaling:** `200` rounds, `1` local epoch per round, `lr=0.003`, `Adam` optimizer (persistent across rounds), `MinMaxScaler` fit on training split only.
- **Metrics & Best Round:** Metrics are computed on the test split; the best round is chosen by lowest test RMSE and is descriptive only (no early stopping or checkpoint selection based on test performance).
- **Seeds:** Seeds `1` and `42` agree to about 6 significant digits on clean runs, so additional seeds were not run for this replication check.
- **Primary vs. Reference Runs:** Primary comparison is between **Local Flower** (`flower_main.py`) and **Local NVFlare** (`nvflare_main.py`) on the same machine (`seed=1`); **Remote Flower** (3-machine run) and `seed=42` observations are retained as reference context.

### Environment & Versions
- **Hardware / OS:** CPU: `AMD Ryzen 5 5600U with Radeon Graphics`, RAM: `16GB`, WSL2 (`6.6.114.1-microsoft-standard-WSL2` & `Ubuntu 22.04.5 LTS`).
- **Software Versions:** Python `3.10.12`, torch `2.14.1`, flwr `1.7.0`, nvflare `2.9.1`.

### Seed 1 Numerical Parity (200 Rounds)
Both local runs reach their lowest test RMSE at round `164` and agree to ~6 significant digits (`< 0.00016%` relative difference):

| Metric | Local Flower (`seed=1`) | Local NVFlare (`seed=1`) | Diff (NVFlare − Flower) | Rel. Diff |
| :--- | :---: | :---: | :---: | :---: |
| **Best Round** *(test RMSE, descriptive only)* | `164` | `164` | `0` | — |
| **Best Test RMSE** | `428.838893` | `428.839184` | `+0.000291` | `+0.000068%` |
| **Best Test MAE** | `330.831371` | `330.831804` | `+0.000434` | `+0.000131%` |
| **Best Test SMAPE** | `37.619233` | `37.619235` | `+0.000002` | `+0.000004%` |
| **Final Round** | `200` | `200` | `0` | — |
| **Final Test RMSE** | `432.622748` | `432.623121` | `+0.000373` | `+0.000086%` |
| **Final Test MAE** | `335.756671` | `335.757181` | `+0.000510` | `+0.000152%` |
| **Final Test SMAPE** | `37.676074` | `37.676090` | `+0.000017` | `+0.000044%` |

### Execution Time (`seed=1`, 200 Rounds)

| Metric | Local Flower | Local NVFlare | Difference / Ratio |
| :--- | :---: | :---: | :---: |
| **Real (Wall Time)** | `2m27.812s` (`147.812s`) | `14m33.682s` (`873.682s`) | `+725.870s` (`5.91x`) |
| **User CPU Time** | `0m45.834s` (`45.834s`) | `2m12.691s` (`132.691s`) | `+86.857s` (`2.90x`) |
| **System CPU Time** | `0m12.400s` (`12.400s`) | `0m43.585s` (`43.585s`) | `+31.185s` (`3.51x`) |

- **Per-round breakdown:** Across `200` rounds, wall-clock time averages about `0.7 s` per round for Flower (`147.812 s` total) and about `4.4 s` per round for NVFlare (`873.682 s` total); startup cost vs. per-round cost was not measured separately.
- **Hypothesis (unprofiled):** I have not profiled where the `725.870 s` gap goes. Polling at `task_check_period = 0.5` s accounts for at most about `100 s` across `200` rounds, so it is not the main cause; the remainder is hypothetically driven by external subprocess execution (`ScriptRunner`), per-round `train` and `validate` task transactions, serialization, and server model persistence.

### Stability & Seed Context (`seed=42` & Remote Flower Reference)
- **`seed=42` local stability:** Under `seed=42`, local NVFlare completed all `200` rounds cleanly (`best_rmse = final_rmse = 426.361741` at round `200`), whereas local Flower hit client instability starting around round `108` (producing single-round test RMSE dips such as `80.398442` at round `143` and ending at `567.082102`) caused by one of the 3 Ray workers failing.
- **Remote Flower reference:** Remote 3-machine Flower runs completed `200` rounds cleanly on both seeds (`428.838859` best / `432.622723` final test RMSE on `seed=1`; `426.361282` best & final test RMSE on `seed=42`), matching NVFlare to ~6 significant digits; this is consistent with the local `seed=42` round-108 issue being a worker/environment artifact rather than a protocol or seed issue, though the root cause was not isolated. No remote NVFlare runs were attempted, as the local NVFlare run was stable and reproducible.

### Code Size Comparison (`black` + `cloc`)

Both python scripts were formatted with `black` and then counted with `cloc` (v1.90) to compare code size and structure.

| File | Code Lines | Blank Lines | Comment Lines | Total Lines |
| :--- | :---: | :---: | :---: | :---: |
| `flower_main.py` (Flower) | `354` | `67` | `1` | `422` |
| `nvflare_main.py` (NVFlare) | `483` | `79` | `1` | `563` |
| **Difference (NVFlare − Flower)** | **`+129` (`+36.4%`)** | **`+12`** | **`0`** | **`+141`** |

- NVFlare has `+129` more code lines (`+36.4%`) than the trimmed Flower script, largely because `nvflare_main.py` embeds the `AuditedFedAvg` controller loop, `WeightedAggregationHelper` / validation broadcast, `PTFileModelPersistor` / `FedJob` / `ScriptRunner` configuration, and the `flare` client loop in one file.
- **What this excludes:** These single-file local counts exclude the separate Flower `server.py` and `client.py` scripts used for multi-machine runs, as well as NVFlare's project file, provisioning, and admin commands; local single-file counts therefore understate the full deployment difference.

### Network & Connection Comparison

| Criterion | Flower (`1.7.0`) | NVFlare (`2.9.1` POC) |
| :--- | :--- | :--- |
| **Server / Bound Listeners** | `1` (`*:8080`) | `1` on `8002` (`0.0.0.0:8002` & `[::]:8002`, `grpc://localhost:8002`); `8003` announced as admin address but not seen listening in `ss -tnlp` without admin console |
| **Listeners on Client Sites** | None | Loopback (`127.0.0.1`) only (for local parent–child/runner IPC) |
| **Outbound Connections per Site (1 Job)** | `1` (client process → `:8080`) | `2` (client parent + `worker_process` → `:8002`) |
| **Client Connections at the Server** | `3` (one per regional client) | `6` per active job |
| **Processes per Site** | `1` (client process) | `3` (`client_train` parent, `worker_process`, and training script `main.py --client`) |
| **Training Script's Network Use** | Direct connection to the server | Loopback (`127.0.0.1`) only, via its `worker_process` (`flare` client API) |
| **Connection Direction** | Clients connect out to server | Clients/workers connect out to server (`127.0.0.1` for local child–parent IPC; `nvflare job submit` for job submission) |
| **Outbound-Only Feasible** | Yes (observed locally; subject to TRE egress/routing rules) | Yes (observed locally; `127.0.0.1` IPC stays local; subject to TRE egress/routing rules) |
| **Local Provisioning / Setup** | None (`server.py` + `client.py`) | `nvflare poc prepare -c ...` generates Root CA, `project.yml`, and startup kits (`prod_00`), followed by `nvflare poc start` and `nvflare job submit -j <job_dir>` |

### What the Server Sees

| Criterion | Flower (`1.7.0`) | NVFlare (`2.9.1`) |
| :--- | :--- | :--- |
| **Primary run aggregation** | Plain FedAvg; individual client parameter updates are sent to the server | Plain `PTFedAvg` / `AuditedFedAvg`; individual client parameter updates are sent to the server |
| **Can the server inspect each client update?** | Yes, in this run; no masking or secure aggregation is enabled | Yes, in this run; no masking or secure aggregation is enabled |
| **Does the server see the aggregate only?** | No | No |
| **Secure aggregation in this run** | Disabled | Disabled |
| **Differential privacy in this run** | Disabled | Disabled |
| **Framework support not tested here** | Secure aggregation and DP extensions/plugins may be available; version-specific setup and drop-out semantics need a focused test | NVFlare privacy filters and homomorphic-encryption secure aggregation are available components, but were not enabled or tested |
| **TRE acceptance implication** | Plain mode requires trust in the server boundary unless a masking/DP mode is added | Plain mode is also an accepted-sensitive-data boundary; secure aggregation and DP still require separate validation |

### Installation & Operational Footprint

| Component | Flower | NVFlare |
| :--- | :--- | :--- |
| **Python packages** | `flwr==1.7.0`, NumPy, pandas, PyTorch, scikit-learn, OpenPyXL | `nvflare==2.9.1`, NumPy, pandas, PyTorch, scikit-learn, OpenPyXL |
| **Extra runtime components** | Ray is used by the local Flower simulation | NVFlare client parent, worker process, external training script, POC/simulator workspace |
| **Project/deployment files** | Two scripts for distributed mode: `server.py` and `client.py` | FedJob/Python job plus provisioned POC or production startup kits for a real deployment |
| **Local setup** | Start server; start a client for each region | Start NVFlare simulator/workspace; submit or execute a job |
| **Real distributed setup** | A server certificate/listener and client server address must be configured | Server, admin, root certificate and site startup kits must be provisioned |
| **Main integration burden** | Custom strategy, client loop, metrics and server address | Controller, persistor, runner, job, processes, metrics and provisioning |

### Framework-Selection Status

| Criterion | Flower | NVFlare |
| :--- | :--- | :--- |
| **Numerical reproduction** | Strong in local seed 1 and in 3-machine reference runs | Strong in local seed 1 and local seed 42 |
| **TRE network evidence** | Simple client-outbound model; only local listener/connectivity evidence | Client workers can remain outbound/local-loopback; real TRE/Poc routing not tested |
| **Plain-weight visibility** | Individual updates visible to server | Individual updates visible to server |
| **Secure aggregation evidence** | Not enabled; support needs verification for the target version | Not enabled; implementation and participant-failure behavior need verification |
| **DP evidence** | Not enabled; DP mode not tested | Not enabled; filter configuration and epsilon accounting not tested |
| **Code/operation cost** | Lower in the single-file local experiment; distributed scripts remain separate | Higher in the single-file local experiment and heavier in provisioning |
| **Decision** | Still viable if a lightweight outbound-only integration is priority | Still viable if integrated provisioning/privacy components justify the footprint |
