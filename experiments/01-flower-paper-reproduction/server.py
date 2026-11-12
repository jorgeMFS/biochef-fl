import flwr as fl
import main as m

if __name__ == "__main__":
    if not m.PAPER_MODE:
        raise SystemExit("Run the paper comparison with the --paper option")

    m.save_run_metadata()
    m.current_round = 1
    for region in m.REGIONS:
        index, x_train, x_test, y_train, y_test, scaler = m.load_datasets(region)
        m.lstm(region, index, x_train, x_test, y_train, y_test, scaler)
    m.centralized_lstm()

    strategy = m.AuditedFedAvg(
        fraction_fit=1.0,
        fraction_evaluate=1.0,   # with 3 clients, same as your 0.5 plus min 3
        min_fit_clients=3,
        min_evaluate_clients=3,
        min_available_clients=3,  # waits until all three clients connect
        on_evaluate_config_fn=lambda r: {"server_round": r},
        evaluate_metrics_aggregation_fn=m.weighted_average,
    )
    fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=fl.server.ServerConfig(num_rounds=m.NUM_ROUNDS),
        strategy=strategy,
    )
    m.save_round_summary()
