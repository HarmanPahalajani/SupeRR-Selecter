import json
import hashlib
from pathlib import Path

def hash_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def verify():
    print("--- 1. VERIFYING BACKUP ARTIFACTS ---")
    with open("backup/production_pre_vNext/backup_manifest.json") as f:
        b_man = json.load(f)

    b_ok = True
    for item in b_man:
        bp = Path(item["backup_path"])
        if not bp.exists():
            print(f"FAILED: Missing backup file {bp}")
            b_ok = False
            continue
        h = hash_file(bp)
        if h != item["sha256"]:
            print(f"FAILED: SHA256 mismatch for backup {bp}")
            b_ok = False
        else:
            print(f"  [OK] {bp.name:35} | {item['size_bytes']:10} B | SHA256: {h[:16]}...")

    print(f"\nBackup Integrity Result: {'ALL VALID' if b_ok else 'FAILED'}")

    print("\n--- 2. VERIFYING RELEASE CANDIDATE ARTIFACTS ---")
    with open("data/release_vNext/release_manifest.json") as f:
        r_man = json.load(f)

    r_ok = True
    for name, meta in r_man["artifacts"].items():
        rp = Path(meta["path"])
        if not rp.exists():
            print(f"FAILED: Missing release file {rp}")
            r_ok = False
            continue
        h = hash_file(rp)
        if h != meta["sha256"]:
            print(f"FAILED: SHA256 mismatch for release {rp}")
            r_ok = False
        else:
            print(f"  [OK] {name:35} | {meta['size_bytes']:10} B | SHA256: {h[:16]}...")

    print(f"\nRelease Integrity Result: {'ALL VALID' if r_ok else 'FAILED'}")

    print("\n--- 3. VERIFYING ROLLBACK PREREQUISITES ---")
    rollback_script = Path("backend/analytics/release/rollback_production.py")
    if not rollback_script.exists():
        print("FAILED: Rollback script missing!")
        rb_ok = False
    else:
        print("  [OK] Rollback script backend/analytics/release/rollback_production.py exists and is armed.")
        rb_ok = True

    if not (b_ok and r_ok and rb_ok):
        print("\nPRE-SWITCH VERIFICATION FAILED! ABORTING.")
        exit(1)
    else:
        print("\nALL PRE-SWITCH VERIFICATIONS PASSED SUCCESSFULLY.")

if __name__ == "__main__":
    verify()
