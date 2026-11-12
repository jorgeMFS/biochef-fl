import sys
import flwr as fl
import main as m

def arg(name):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None

if __name__ == "__main__":
    region, server = arg("--region"), arg("--server")
    if region not in m.REGIONS or not server:
        raise SystemExit("usage: python client.py --paper --region Portugal --server host:8080")
    idx = m.REGIONS.index(region)          # same per-client seeding as client_fn
    m.random.seed(m.seed + idx); m.np.random.seed(m.seed + idx); m.torch.manual_seed(m.seed + idx)
    fl.client.start_numpy_client(server_address=server, client=m.FlowerClient(region))
