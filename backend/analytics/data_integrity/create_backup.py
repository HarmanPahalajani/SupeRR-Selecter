import os
import shutil
import hashlib
import json

def run_backup():
    backup_dir = "backup/production_pre_scope_fix"
    os.makedirs(backup_dir, exist_ok=True)

    files_to_backup = [
        "data/processed/fact_player_metrics.parquet",
        "data/processed/dim_player.parquet",
        "data/processed/dim_match.parquet",
        "data/processed/dim_competition.parquet",
        "data/processed/fact_delivery_canonical.parquet",
        "data/processed/fact_delivery_scored.parquet",
        "data/processed/fact_delivery_states.parquet",
        "data/processed/fact_delivery_super_overs.parquet",
        "data/app/analytics.duckdb",
        "data/app/user_store.db",
    ]

    manifest = {}
    for rel_path in files_to_backup:
        if os.path.exists(rel_path):
            dest = os.path.join(backup_dir, os.path.basename(rel_path))
            shutil.copy2(rel_path, dest)
            hasher = hashlib.sha256()
            with open(rel_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            sha = hasher.hexdigest()
            size = os.path.getsize(rel_path)
            manifest[rel_path] = {
                "sha256": sha,
                "size_bytes": size,
                "dest": dest
            }
            print(f"Backed up {rel_path} -> {dest} ({size:,} bytes, sha256={sha[:12]}...)")
        else:
            print(f"Warning: {rel_path} does not exist")

    manifest_path = os.path.join(backup_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Backup manifest saved to {manifest_path}")

if __name__ == "__main__":
    run_backup()
