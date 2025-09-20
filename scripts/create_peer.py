import os, glob, re, random, yaml

CONFIG_DIR = "config"
BASE_PATH = os.path.join(CONFIG_DIR, "base_config.yaml")
FILE_RE = re.compile(r"peer_(\d+)\.yaml$")

def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

def main():
    # Archivos existentes peer_*.yaml
    files = []
    for p in glob.glob(os.path.join(CONFIG_DIR, "peer_*.yaml")):
        m = FILE_RE.search(os.path.basename(p))
        if m: files.append((int(m.group(1)), p))
    if not files:
        raise SystemExit("No hay peers existentes (esperado al menos peer_01.yaml).")

    files.sort(key=lambda x: x[0])
    last_n, last_path = files[-1]
    last_cfg = load(last_path)
    base_cfg = load(BASE_PATH)

    # Siguiente número y padding (según nombres existentes)
    pad_width = len(FILE_RE.search(os.path.basename(files[-1][1])).group(1))
    next_n = last_n + 1
    peer_id = f"peer_{str(next_n).zfill(pad_width)}"

    # Puertos secuenciales
    rest_port = int(last_cfg["rest_port"]) + 1
    grpc_port = int(last_cfg["grpc_port"]) + 1

    # Selección aleatoria de headline y substitute entre existentes
    existing = [load(p) for _, p in files]
    head = random.choice(existing)
    subs_candidates = [e for e in existing if e is not head] or [head]
    subs = random.choice(subs_candidates)

    # Construcción del nuevo config (tomando IP de base; resto explícito)
    new_cfg = dict(base_cfg)
    new_cfg.update({
        "peer_id": peer_id,
        "ip": base_cfg.get("ip", "127.0.0.1"),
        "rest_port": rest_port,
        "grpc_port": grpc_port,
        "files_directory": f"./files/peer{next_n}",
        "headline_peer": {
            "id": head.get("peer_id", ""),
            "address": f"{head.get('ip', '127.0.0.1')}:{head.get('rest_port', '')}"
        },
        "substitute_peer": {
            "id": subs.get("peer_id", ""),
            "address": f"{subs.get('ip', '127.0.0.1')}:{subs.get('rest_port', '')}"
        }
    })

    out_path = os.path.join(CONFIG_DIR, f"peer_{str(next_n).zfill(pad_width)}.yaml")
    if os.path.exists(out_path):
        raise SystemExit(f"Ya existe: {out_path}")
    save(out_path, new_cfg)
    print(f"Creado {out_path}")

if __name__ == "__main__":
    main()