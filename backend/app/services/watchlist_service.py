import sqlite3
from pathlib import Path

USER_DB = "data/app/user_store.db"

class WatchlistService:
    @staticmethod
    def get_connection():
        return sqlite3.connect(USER_DB)

    @classmethod
    def get_watchlists(cls):
        conn = cls.get_connection()
        cur = conn.cursor()
        wls = cur.execute("SELECT watchlist_id, name, description, created_at FROM watchlists").fetchall()
        
        result = []
        for w in wls:
            wid = w[0]
            players = cur.execute("""
                SELECT wp.player_id, ap.player_name, wp.priority, wp.target_role, ap.estimated_price_mid, wp.added_at
                FROM watchlist_players wp
                JOIN player_auction_pool ap ON wp.player_id = ap.player_id
                WHERE wp.watchlist_id = ?
            """, (wid,)).fetchall()

            player_list = []
            for p in players:
                player_list.append({
                    "player_id": p[0],
                    "player_name": p[1],
                    "priority": p[2],
                    "target_role": p[3],
                    "estimated_price": p[4],
                    "added_at": p[5]
                })

            result.append({
                "watchlist_id": wid,
                "name": w[1],
                "description": w[2],
                "created_at": w[3],
                "player_count": len(player_list),
                "players": player_list
            })
        conn.close()
        return result

    @classmethod
    def create_watchlist(cls, name: str, description: str = ""):
        conn = cls.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO watchlists (name, description) VALUES (?, ?)", (name, description))
        wid = cur.lastrowid
        conn.commit()
        conn.close()
        return {"watchlist_id": wid, "name": name, "description": description}

    @classmethod
    def add_player(cls, watchlist_id: int, player_id: int, priority: str = "Medium", target_role: str = ""):
        conn = cls.get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO watchlist_players (watchlist_id, player_id, priority, target_role)
            VALUES (?, ?, ?, ?)
        """, (watchlist_id, player_id, priority, target_role))
        conn.commit()
        conn.close()
        return {"status": "SUCCESS", "watchlist_id": watchlist_id, "player_id": player_id}

    @classmethod
    def remove_player(cls, watchlist_id: int, player_id: int):
        conn = cls.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM watchlist_players WHERE watchlist_id = ? AND player_id = ?", (watchlist_id, player_id))
        conn.commit()
        conn.close()
        return {"status": "DELETED"}

    @classmethod
    def get_player_notes(cls, player_id: int):
        conn = cls.get_connection()
        cur = conn.cursor()
        notes = cur.execute("""
            SELECT note_id, author, content, verdict, created_at
            FROM player_notes WHERE player_id = ?
            ORDER BY created_at DESC
        """, (player_id,)).fetchall()
        conn.close()
        return [{
            "note_id": n[0],
            "author": n[1],
            "content": n[2],
            "verdict": n[3],
            "created_at": n[4]
        } for n in notes]

    @classmethod
    def add_player_note(cls, player_id: int, content: str, verdict: str = "Shortlist", author: str = "Analyst"):
        conn = cls.get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO player_notes (player_id, author, content, verdict)
            VALUES (?, ?, ?, ?)
        """, (player_id, author, content, verdict))
        nid = cur.lastrowid
        conn.commit()
        conn.close()
        return {"note_id": nid, "player_id": player_id, "verdict": verdict, "status": "SAVED"}
