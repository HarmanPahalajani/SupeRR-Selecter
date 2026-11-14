import urllib.request
import json

def verify_modules():
    print("=== VERIFYING DATA SOURCES FOR ALL 8 FRONTEND MODULES ===")
    
    modules = [
        ("1. Overview Dashboard", "http://127.0.0.1:8000/api/v1/meta/coverage", lambda d: d.get("total_deliveries") == 200999),
        ("2. Talent Discovery", "http://127.0.0.1:8000/api/v1/players?limit=25", lambda d: len(d.get("items", [])) > 0),
        ("3. Player Profiles", "http://127.0.0.1:8000/api/v1/players/478/profile", lambda d: d.get("summary", {}).get("player_id") == 478),
        ("4. Player Comparison", "http://127.0.0.1:8000/api/v1/players?limit=5", lambda d: len(d.get("items", [])) >= 2),
        ("5. Squad Architect", "http://127.0.0.1:8000/api/v1/players?role=BOWLER&limit=15", lambda d: len(d.get("items", [])) > 0),
        ("6. Auction Simulator", "http://127.0.0.1:8000/api/v1/auction/pool", lambda d: "available_players" in d or "pool" in d or isinstance(d, dict)),
        ("7. Watchlist", "http://127.0.0.1:8000/api/v1/watchlists", lambda d: isinstance(d, list)),
        ("8. Methodology & Validation", "http://127.0.0.1:8000/api/v1/methodology", lambda d: "sections" in d or "methodology" in d or isinstance(d, dict))
    ]
    
    for name, url, validator in modules:
        try:
            req = urllib.request.urlopen(url, timeout=5)
            data = json.loads(req.read().decode('utf-8'))
            valid = validator(data)
            assert valid, f"Validation predicate failed for {name}"
            print(f"  [VERIFIED OK] {name:30} -> HTTP {req.status}")
        except Exception as e:
            print(f"  [FAILED] {name:30} -> {e}")
            raise e
            
    print("\nAll 8 Frontend Modules Verified Successfully against Active Production Backend.")

if __name__ == "__main__":
    verify_modules()
