import shutil
import hashlib
import json
from pathlib import Path

def hash_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def backup_current_production():
    backup_dir = Path("backup/production_pre_ratings_fix")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    files_to_backup = [
        Path("data/processed/fact_player_metrics.parquet"),
        Path("data/app/analytics.duckdb"),
        Path("data/app/user_store.db")
    ]
    
    manifest = []
    print("=== EXECUTING PRE-RATINGS-FIX COLD BACKUP ===")
    for src in files_to_backup:
        assert src.exists(), f"Source file {src} does not exist!"
        dst = backup_dir / src.name
        shutil.copy2(src, dst)
        h = hash_file(dst)
        size = dst.stat().st_size
        manifest.append({
            "source": str(src),
            "backup": str(dst),
            "size_bytes": size,
            "sha256": h
        })
        print(f"  [BACKED UP] {src.name:30} -> {size:10} B | SHA256: {h[:16]}...")
        
    manifest_path = backup_dir / "backup_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Backup manifest saved to {manifest_path}!")
    return manifest

if __name__ == "__main__":
    backup_current_production()
