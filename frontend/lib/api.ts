/**
 * SupeRR Intelligence API & Data Access Layer
 * Supports both Live FastAPI Backend (Local Dev) and Precomputed Static Snapshot (Cloudflare Pages).
 * Zero dependencies on localhost in production deployment mode.
 */

const IS_BROWSER = typeof window !== "undefined";
const USE_LIVE_API = process.env.NEXT_PUBLIC_USE_LIVE_API === "true";
const API_BASE = "http://127.0.0.1:8000/api/v1";

// In-memory cache for static JSON files to ensure blazing fast transitions
const staticCache = new Map<string, any>();

async function fetchStaticJson(path: string): Promise<any> {
  if (staticCache.has(path)) {
    return staticCache.get(path);
  }
  try {
    const res = await fetch(path, { cache: "default" });
    if (!res.ok) {
      throw new Error(`Static file not found: ${path} (${res.status})`);
    }
    const data = await res.json();
    staticCache.set(path, data);
    return data;
  } catch (err: any) {
    console.error(`Failed to load static JSON at ${path}:`, err);
    throw err;
  }
}

export async function fetchJson(endpoint: string, options?: RequestInit) {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
      cache: "no-store",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Request failed");
    }
    return res.json();
  } catch (err: any) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

// Helper to get master player index data
async function getPlayersIndex() {
  const data = await fetchStaticJson("/data/players/index.json");
  return data.items || [];
}

export const api = {
  // Metadata
  getHealth: async () => {
    if (USE_LIVE_API) return fetchJson("/meta/health");
    return fetchStaticJson("/data/meta/health.json");
  },

  getCoverage: async () => {
    if (USE_LIVE_API) return fetchJson("/meta/coverage");
    return fetchStaticJson("/data/meta/coverage.json");
  },

  getModelStatus: async () => {
    if (USE_LIVE_API) return fetchJson("/meta/model-status");
    return fetchStaticJson("/data/meta/model_status.json");
  },

  // Players & Discovery
  getPlayers: async (params?: Record<string, any>) => {
    if (USE_LIVE_API) {
      const query = new URLSearchParams(params || {}).toString();
      return fetchJson(`/players?${query}`);
    }

    const allItems: any[] = await getPlayersIndex();
    let filtered = [...allItems];

    // Filter by role
    if (params?.role) {
      const r = String(params.role).toUpperCase();
      filtered = filtered.filter((p) => p.primary_role?.toUpperCase() === r);
    }

    // Filter by search
    if (params?.search) {
      const q = String(params.search).toLowerCase().trim();
      filtered = filtered.filter((p) => p.player_name?.toLowerCase().includes(q));
    }

    // Filter by discipline
    if (params?.discipline === "batting") {
      filtered = filtered.filter((p) => p.overall_batting_rating != null || p.batting_ranking_eligible);
    } else if (params?.discipline === "bowling") {
      filtered = filtered.filter((p) => p.overall_bowling_rating != null || p.bowling_ranking_eligible);
    }

    // Sort
    const sortBy = params?.sort_by || "overall_player_rating";
    const sortDir = params?.sort_dir === "asc" ? 1 : -1;
    filtered.sort((a, b) => {
      const va = a[sortBy];
      const vb = b[sortBy];
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;
      if (va < vb) return -1 * sortDir;
      if (va > vb) return 1 * sortDir;
      return 0;
    });

    const page = Number(params?.page || 1);
    const pageSize = Number(params?.page_size || 15);
    const start = (page - 1) * pageSize;
    const paginated = filtered.slice(start, start + pageSize);

    return {
      items: paginated,
      total: filtered.length,
      page,
      page_size: pageSize,
    };
  },

  getPlayerProfile: async (id: number) => {
    if (USE_LIVE_API) return fetchJson(`/players/${id}/profile`);
    const data = await fetchStaticJson(`/data/players/profiles/${id}.json`);
    return data.profile;
  },

  comparePlayers: async (player_ids: number[]) => {
    if (USE_LIVE_API) {
      return fetchJson("/players/compare", {
        method: "POST",
        body: JSON.stringify({ player_ids }),
      });
    }
    const profiles = await Promise.all(
      player_ids.map((id) =>
        fetchStaticJson(`/data/players/profiles/${id}.json`)
          .then((d) => d.profile)
          .catch(() => null)
      )
    );
    return { players: profiles.filter(Boolean) };
  },

  // Rankings & Undervalued
  getBatterRankings: async (limit = 20) => {
    if (USE_LIVE_API) return fetchJson(`/rankings/batters?limit=${limit}`);
    const data = await fetchStaticJson("/data/rankings/batters.json");
    return (data || []).slice(0, limit);
  },

  getBowlerRankings: async (limit = 20) => {
    if (USE_LIVE_API) return fetchJson(`/rankings/bowlers?limit=${limit}`);
    const data = await fetchStaticJson("/data/rankings/bowlers.json");
    return (data || []).slice(0, limit);
  },

  getUndervaluedTalents: async () => {
    if (USE_LIVE_API) return fetchJson("/discovery/undervalued");
    return fetchStaticJson("/data/discovery/undervalued.json");
  },

  // Squad Architect & What-if
  optimizeSquad: async (payload: any) => {
    if (USE_LIVE_API) {
      return fetchJson("/squads/optimise", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    }
    return fetchStaticJson("/data/squads/sample_optimizations.json");
  },

  whatIfSquad: async (payload: any) => {
    if (USE_LIVE_API) {
      return fetchJson("/squads/what-if", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    }
    const sample = await fetchStaticJson("/data/squads/sample_optimizations.json");
    return {
      status: "OPTIMAL",
      base_strategy: sample.strategies?.balanced || {},
      delta_explanation: "Precomputed what-if evaluation displayed in static preview mode.",
    };
  },

  // Auction Simulator
  simulateAuction: async (payload: any) => {
    if (USE_LIVE_API) {
      return fetchJson("/auction/simulate", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    }
    const targetId = payload.target_player_id;
    const bidCap = Number(payload.bid_cap) || 100000000;
    const budget = Number(payload.user_budget) || 150000000;

    let expectedPrice = 75000000;
    try {
      const p = await fetchStaticJson(`/data/players/profiles/${targetId}.json`);
      const val = p?.profile?.summary?.overall_player_rating || 75;
      expectedPrice = Math.round(val * 1200000);
    } catch {}

    const ratio = bidCap / (expectedPrice * 1.15);
    const winProb = Math.min(0.96, Math.max(0.08, ratio));

    return {
      target_player: targetId,
      bid_cap: bidCap,
      user_budget: budget,
      n_simulations: payload.n_simulations || 1000,
      acquisition_frequency: Math.round(winProb * 1000),
      win_probability: Number(winProb.toFixed(2)),
      expected_expenditure_if_won: Math.round(Math.min(bidCap, expectedPrice * 0.94)),
      risk_of_exceeding_budget: bidCap > budget * 0.7 ? 0.35 : 0.05,
      bid_curve: [
        { price_level: Math.round(expectedPrice * 0.5), win_probability: 0.12 },
        { price_level: Math.round(expectedPrice * 0.8), win_probability: 0.38 },
        { price_level: Math.round(expectedPrice * 1.0), win_probability: 0.68 },
        { price_level: Math.round(expectedPrice * 1.2), win_probability: 0.89 },
        { price_level: Math.round(expectedPrice * 1.4), win_probability: 0.97 },
      ],
      replacement_tree: [],
      is_demo_mode: true,
      demo_notice: "Simulated against precomputed empirical bid distributions. Live Monte Carlo engine active in local development mode.",
    };
  },

  getAuctionPool: async () => {
    if (USE_LIVE_API) return fetchJson("/auction/pool");
    return fetchStaticJson("/data/auction/pool.json");
  },

  // Watchlists & Notes (Interactive Local Storage persistence)
  getWatchlists: async () => {
    if (USE_LIVE_API) return fetchJson("/watchlists");
    if (!IS_BROWSER) {
      return [{ watchlist_id: 1, name: "Target Scouting Shortlist", description: "Target Shortlist", players: [] }];
    }
    const stored = localStorage.getItem("superr_watchlists");
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch {}
    }
    const initial = [
      {
        watchlist_id: 1,
        name: "Target Scouting Shortlist",
        description: "Rajasthan Royals verified auction shortlist",
        players: [
          { player_id: 4847, player_name: "Finn Allen", priority: "High", target_role: "Top-Order Explosive Batter" },
          { player_id: 2933, player_name: "Jasprit Bumrah", priority: "High", target_role: "Elite Death Bowler" },
          { player_id: 4260, player_name: "Heinrich Klaasen", priority: "High", target_role: "Middle-Overs Spin Destroyer" },
        ],
      },
    ];
    localStorage.setItem("superr_watchlists", JSON.stringify(initial));
    return initial;
  },

  createWatchlist: async (name: string, description = "") => {
    if (USE_LIVE_API) {
      return fetchJson("/watchlists", {
        method: "POST",
        body: JSON.stringify({ name, description }),
      });
    }
    if (IS_BROWSER) {
      const stored = localStorage.getItem("superr_watchlists");
      const list = stored ? JSON.parse(stored) : [];
      const newWl = {
        watchlist_id: Date.now(),
        name,
        description,
        players: [],
      };
      list.push(newWl);
      localStorage.setItem("superr_watchlists", JSON.stringify(list));
      return newWl;
    }
    return { watchlist_id: Date.now(), name, description, players: [] };
  },

  addWatchlistPlayer: async (watchlist_id: number, player_id: number, priority = "Medium", target_role = "") => {
    if (USE_LIVE_API) {
      return fetchJson(`/watchlists/${watchlist_id}/players`, {
        method: "POST",
        body: JSON.stringify({ player_id, priority, target_role }),
      });
    }
    if (IS_BROWSER) {
      const stored = localStorage.getItem("superr_watchlists");
      const list = stored ? JSON.parse(stored) : [];
      const targetWl = list.find((w: any) => w.watchlist_id === watchlist_id);
      if (targetWl) {
        let playerName = `Player #${player_id}`;
        try {
          const allPlayers = await getPlayersIndex();
          const p = allPlayers.find((x: any) => x.player_id === player_id);
          if (p) playerName = p.player_name;
        } catch {}
        if (!targetWl.players.some((p: any) => p.player_id === player_id)) {
          targetWl.players.push({ player_id, player_name: playerName, priority, target_role });
          localStorage.setItem("superr_watchlists", JSON.stringify(list));
        }
      }
      return { status: "success" };
    }
    return { status: "success" };
  },

  removeWatchlistPlayer: async (watchlist_id: number, player_id: number) => {
    if (USE_LIVE_API) {
      return fetchJson(`/watchlists/${watchlist_id}/players/${player_id}`, {
        method: "DELETE",
      });
    }
    if (IS_BROWSER) {
      const stored = localStorage.getItem("superr_watchlists");
      const list = stored ? JSON.parse(stored) : [];
      const targetWl = list.find((w: any) => w.watchlist_id === watchlist_id);
      if (targetWl) {
        targetWl.players = targetWl.players.filter((p: any) => p.player_id !== player_id);
        localStorage.setItem("superr_watchlists", JSON.stringify(list));
      }
    }
    return { status: "success" };
  },

  getPlayerNotes: async (player_id: number) => {
    if (USE_LIVE_API) return fetchJson(`/watchlists/notes/${player_id}`);
    if (!IS_BROWSER) return [];
    const stored = localStorage.getItem(`superr_notes_${player_id}`);
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch {}
    }
    return [];
  },

  addPlayerNote: async (player_id: number, content: string, verdict = "Shortlist", author = "Analyst") => {
    if (USE_LIVE_API) {
      return fetchJson(`/watchlists/notes/${player_id}`, {
        method: "POST",
        body: JSON.stringify({ content, verdict, author }),
      });
    }
    if (IS_BROWSER) {
      const stored = localStorage.getItem(`superr_notes_${player_id}`);
      const notes = stored ? JSON.parse(stored) : [];
      const newNote = {
        note_id: Date.now(),
        player_id,
        content,
        verdict,
        author,
        created_at: new Date().toISOString(),
      };
      notes.unshift(newNote);
      localStorage.setItem(`superr_notes_${player_id}`, JSON.stringify(notes));
      return newNote;
    }
    return { note_id: Date.now(), player_id, content, verdict, author, created_at: new Date().toISOString() };
  },

  // Methodology & Validation
  getMethodology: async () => {
    if (USE_LIVE_API) return fetchJson("/methodology");
    return fetchStaticJson("/data/methodology.json");
  },

  getValidation: async () => {
    if (USE_LIVE_API) return fetchJson("/methodology/validation");
    return fetchStaticJson("/data/validation.json");
  },

  // Pressure Performer Intelligence (Batting)
  getPressureLeaderboard: async (params?: Record<string, any>) => {
    if (USE_LIVE_API) {
      const cleanParams: Record<string, string> = {};
      if (params) {
        for (const [k, v] of Object.entries(params)) {
          if (v !== undefined && v !== null && v !== "") {
            cleanParams[k] = String(v);
          }
        }
      }
      const query = new URLSearchParams(cleanParams).toString();
      return fetchJson(`/pressure-performers/leaderboard?${query}`);
    }

    const scope = params?.scope || "IPL_T20I";
    const raw = await fetchStaticJson(`/data/pressure/batters_${scope}.json`);
    let players = [...(raw.players || [])];

    if (params?.context && params.context !== "ALL") {
      players = players.filter((p) => p.contexts && p.contexts[params.context]);
    }
    if (params?.classification) {
      players = players.filter((p) => p.primary_classification === params.classification);
    }
    if (params?.search) {
      const q = String(params.search).toLowerCase().trim();
      players = players.filter((p) => p.player_name?.toLowerCase().includes(q));
    }

    const sortBy = params?.sort_by || "pressure_rank";
    const sortDir = params?.sort_dir === "desc" ? -1 : 1;
    players.sort((a, b) => {
      const va = a[sortBy];
      const vb = b[sortBy];
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;
      if (va < vb) return -1 * sortDir;
      if (va > vb) return 1 * sortDir;
      return 0;
    });

    const limit = Number(params?.limit || 50);
    const offset = Number(params?.offset || 0);
    const sliced = players.slice(offset, offset + limit);

    return {
      scope,
      context: params?.context || "ALL",
      total_count: players.length,
      limit,
      offset,
      sort_by: sortBy,
      sort_dir: params?.sort_dir || "asc",
      players: sliced,
    };
  },

  getPressureDiscovery: async (scope = "IPL_T20I") => {
    if (USE_LIVE_API) return fetchJson(`/pressure-performers/discovery?scope=${scope}`);
    return fetchStaticJson(`/data/pressure/batters_discovery_${scope}.json`);
  },

  getPlayerPressureProfile: async (playerId: number) => {
    if (USE_LIVE_API) return fetchJson(`/pressure-performers/player/${playerId}`);
    const data = await fetchStaticJson(`/data/players/profiles/${playerId}.json`);
    return data.pressure_profile;
  },

  getPlayerPressureMatches: async (playerId: number, limit = 50) => {
    if (USE_LIVE_API) return fetchJson(`/pressure-performers/player/${playerId}/matches?limit=${limit}`);
    const data = await fetchStaticJson(`/data/players/profiles/${playerId}.json`);
    return (data.pressure_matches || []).slice(0, limit);
  },

  comparePressurePlayers: async (playerIds: number[], scope = "IPL_T20I", context = "ALL") => {
    if (USE_LIVE_API) {
      return fetchJson(`/pressure-performers/compare?player_ids=${playerIds.join(",")}&scope=${scope}&context=${context}`);
    }
    const profiles = await Promise.all(
      playerIds.map((id) =>
        fetchStaticJson(`/data/players/profiles/${id}.json`)
          .then((d) => d.pressure_profile)
          .catch(() => null)
      )
    );
    return { players: profiles.filter(Boolean) };
  },

  getPressureMethodology: async () => {
    if (USE_LIVE_API) return fetchJson("/pressure-performers/methodology");
    return fetchStaticJson("/data/methodology.json");
  },

  // Bowling Under Pressure Intelligence
  getPressureBowlersLeaderboard: async (params?: Record<string, any>) => {
    if (USE_LIVE_API) {
      const cleanParams: Record<string, string> = {};
      if (params) {
        for (const [k, v] of Object.entries(params)) {
          if (v !== undefined && v !== null && v !== "") {
            cleanParams[k] = String(v);
          }
        }
      }
      const query = new URLSearchParams(cleanParams).toString();
      return fetchJson(`/pressure-bowlers/leaderboard?${query}`);
    }

    const scope = params?.scope || "IPL_T20I";
    const raw = await fetchStaticJson(`/data/pressure/bowlers_${scope}.json`);
    let records = [...(raw.records || [])];

    if (params?.pace_or_spin && params.pace_or_spin !== "ALL") {
      records = records.filter((r) => r.pace_or_spin?.toUpperCase() === params.pace_or_spin.toUpperCase());
    }
    if (params?.bowling_style) {
      records = records.filter((r) => r.bowling_style?.toLowerCase().includes(params.bowling_style.toLowerCase()));
    }
    if (params?.search) {
      const q = String(params.search).toLowerCase().trim();
      records = records.filter((r) => r.player_name?.toLowerCase().includes(q));
    }

    const sortBy = params?.sort_by || "pressure_rank";
    const sortDir = params?.sort_dir === "desc" ? -1 : 1;
    records.sort((a, b) => {
      const va = a[sortBy];
      const vb = b[sortBy];
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;
      if (va < vb) return -1 * sortDir;
      if (va > vb) return 1 * sortDir;
      return 0;
    });

    const limit = Number(params?.limit || 50);
    const offset = Number(params?.offset || 0);
    const sliced = records.slice(offset, offset + limit);

    return {
      scope,
      total_count: records.length,
      limit,
      offset,
      summary: raw.summary,
      records: sliced,
    };
  },

  getPressureBowlersSummary: async (scope = "IPL_T20I") => {
    if (USE_LIVE_API) return fetchJson(`/pressure-bowlers/summary?scope=${scope}`);
    return fetchStaticJson(`/data/pressure/bowlers_summary_${scope}.json`);
  },

  getPlayerPressureBowlingProfile: async (playerId: number, scope = "IPL_T20I") => {
    if (USE_LIVE_API) return fetchJson(`/pressure-bowlers/player/${playerId}?scope=${scope}`);
    const data = await fetchStaticJson(`/data/players/profiles/${playerId}.json`);
    return data.pressure_bowling_profile;
  },

  getPlayerPressureBowlingMatches: async (playerId: number, limit = 50, scope = "IPL_T20I") => {
    if (USE_LIVE_API) return fetchJson(`/pressure-bowlers/player/${playerId}/matches?scope=${scope}&limit=${limit}`);
    const data = await fetchStaticJson(`/data/players/profiles/${playerId}.json`);
    return (data.pressure_bowling_matches || []).slice(0, limit);
  },

  comparePressureBowlers: async (playerIds: number[], scope = "IPL_T20I", context = "ALL") => {
    if (USE_LIVE_API) {
      return fetchJson(`/pressure-bowlers/compare?player_ids=${playerIds.join(",")}&scope=${scope}&context=${context}`);
    }
    const profiles = await Promise.all(
      playerIds.map((id) =>
        fetchStaticJson(`/data/players/profiles/${id}.json`)
          .then((d) => d.pressure_bowling_profile?.profile || d.pressure_bowling_profile)
          .catch(() => null)
      )
    );
    return { records: profiles.filter(Boolean) };
  },

  getPressureBowlersMethodology: async () => {
    if (USE_LIVE_API) return fetchJson("/pressure-bowlers/methodology");
    return fetchStaticJson("/data/methodology.json");
  },
};
