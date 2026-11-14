"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  formatCurrency,
  formatRating,
  formatEvidenceLevel,
  formatRoleTitle,
  CRICKET_TOOLTIPS,
} from "@/lib/presentation";
import {
  BookmarkCheck,
  Plus,
  Trash2,
  Download,
  FolderPlus,
  User,
  Shield,
  Layers,
  Sparkles,
  Eye,
  Info,
} from "lucide-react";

export default function WatchlistPage() {
  const [watchlists, setWatchlists] = useState<any[]>([]);
  const [activeWatchlistId, setActiveWatchlistId] = useState<number | null>(null);
  const [newListName, setNewListName] = useState("");
  const [newListDesc, setNewListDesc] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadWatchlists();
  }, []);

  async function loadWatchlists() {
    setLoading(true);
    try {
      const data = await api.getWatchlists();
      setWatchlists(data);
      if (data.length > 0 && !activeWatchlistId) {
        setActiveWatchlistId(data[0].watchlist_id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateWatchlist(e: React.FormEvent) {
    e.preventDefault();
    if (!newListName.trim()) return;
    try {
      await api.createWatchlist(newListName, newListDesc);
      setNewListName("");
      setNewListDesc("");
      setShowCreateModal(false);
      await loadWatchlists();
    } catch (err) {
      console.error(err);
    }
  }

  async function handleRemovePlayer(wid: number, pid: number) {
    try {
      await api.removeWatchlistPlayer(wid, pid);
      await loadWatchlists();
    } catch (err) {
      console.error(err);
    }
  }

  function exportShortlist(format: "json" | "csv") {
    const active = watchlists.find((w) => w.watchlist_id === activeWatchlistId);
    if (!active) return;

    if (format === "json") {
      const blob = new Blob([JSON.stringify(active, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${active.name.toLowerCase().replace(/\s+/g, "_")}.json`;
      a.click();
    } else {
      let csv = "player_id,player_name,priority,target_role,estimated_price\n";
      active.players.forEach((p: any) => {
        csv += `${p.player_id},"${p.player_name}",${p.priority},"${p.target_role}",${p.estimated_price}\n`;
      });
      const blob = new Blob([csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${active.name.toLowerCase().replace(/\s+/g, "_")}.csv`;
      a.click();
    }
  }

  const active = watchlists.find((w) => w.watchlist_id === activeWatchlistId);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-rr-navy flex items-center gap-2.5">
            <BookmarkCheck className="w-6 h-6 text-rr-pink" />
            Scouting Watchlists & Target Portfolios
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Organize recruitment shortlists, assign tactical priorities, track valuation caps, and export strategic dossiers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-rr-primary"
          >
            <FolderPlus className="w-4 h-4" />
            <span>Create New Watchlist</span>
          </button>
        </div>
      </div>

      {/* Main Watchlist Container */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Watchlist Sidebar List */}
        <div className="space-y-2">
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider px-1">
            Active Watchlists
          </div>

          <div className="space-y-1.5">
            {watchlists.map((w) => (
              <button
                key={w.watchlist_id}
                onClick={() => setActiveWatchlistId(w.watchlist_id)}
                className={`w-full text-left p-3.5 rounded-xl border transition-all flex items-center justify-between shadow-xs ${
                  activeWatchlistId === w.watchlist_id
                    ? "bg-pink-50 border-pink-200 text-rr-navy font-bold"
                    : "bg-white border-slate-200 text-slate-600 hover:text-rr-navy hover:bg-slate-50"
                }`}
              >
                <div>
                  <div className="text-xs font-bold">{w.name}</div>
                  <div className="text-[11px] text-slate-500 font-normal">
                    {w.player_count || (w.players?.length || 0)} candidates
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Watchlist Detail & Player List */}
        <div className="md:col-span-3 space-y-4">
          {active ? (
            <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-xs space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
                <div>
                  <h2 className="text-lg font-bold text-rr-navy">{active.name}</h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {active.description || "Active recruitment targets for franchise consideration."}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => exportShortlist("csv")}
                    className="btn-rr-secondary text-xs py-1.5 px-3"
                  >
                    <Download className="w-3.5 h-3.5 text-rr-pink" />
                    <span>Export CSV</span>
                  </button>
                  <button
                    onClick={() => exportShortlist("json")}
                    className="btn-rr-secondary text-xs py-1.5 px-3"
                  >
                    <Download className="w-3.5 h-3.5 text-rr-navy" />
                    <span>Export JSON</span>
                  </button>
                </div>
              </div>

              {/* Player Items Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-50 text-rr-navy font-bold border-b border-slate-200 uppercase tracking-wider text-[11px]">
                    <tr>
                      <th className="py-2.5 px-3">Player</th>
                      <th className="py-2.5 px-3">Target Tactical Role</th>
                      <th className="py-2.5 px-3 text-center">Recruitment Priority</th>
                      <th className="py-2.5 px-3 text-right">Estimated Price</th>
                      <th className="py-2.5 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {active.players.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="py-12 text-center text-slate-400">
                          No players added to this watchlist yet. Use Player Discovery to shortlist recruitment targets.
                        </td>
                      </tr>
                    ) : (
                      active.players.map((p: any) => (
                        <tr key={p.player_id} className="hover:bg-pink-50/20 transition-colors">
                          <td className="py-3 px-3">
                            <Link
                              href={`/players/${p.player_id}`}
                              className="font-bold text-rr-navy hover:text-rr-pink transition-colors text-xs"
                            >
                              {p.player_name}
                            </Link>
                          </td>
                          <td className="py-3 px-3 font-medium text-slate-600">
                            {formatRoleTitle(p.target_role) || "Core Squad Option"}
                          </td>
                          <td className="py-3 px-3 text-center">
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                                p.priority === "High"
                                  ? "bg-pink-50 text-rr-pink border-pink-200"
                                  : "bg-slate-100 text-slate-700 border-slate-200"
                              }`}
                            >
                              {p.priority} Priority
                            </span>
                          </td>
                          <td className="py-3 px-3 text-right font-bold text-rr-navy">
                            {formatCurrency(p.estimated_price)}
                          </td>
                          <td className="py-3 px-3 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <Link
                                href={`/players/${p.player_id}`}
                                className="p-1 rounded text-slate-500 hover:text-rr-pink"
                                title="View Profile"
                              >
                                <Eye className="w-3.5 h-3.5" />
                              </Link>
                              <button
                                onClick={() => handleRemovePlayer(active.watchlist_id, p.player_id)}
                                className="p-1 rounded text-slate-400 hover:text-red-600 transition-colors"
                                title="Remove from Watchlist"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="p-12 text-center bg-white rounded-xl border border-slate-200 text-slate-400 text-xs">
              Select or create a watchlist to view candidates.
            </div>
          )}
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-rr-navy">
              Create Scouting Watchlist
            </h3>
            <form onSubmit={handleCreateWatchlist} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-600 block mb-1">
                  Watchlist Title:
                </label>
                <input
                  type="text"
                  placeholder="e.g. Indian Middle-Overs Batters"
                  value={newListName}
                  onChange={(e) => setNewListName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:border-rr-pink"
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-600 block mb-1">
                  Scouting Description (Optional):
                </label>
                <textarea
                  placeholder="e.g. Primary targets for auction slot #3"
                  value={newListDesc}
                  onChange={(e) => setNewListDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:border-rr-pink h-20"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn-rr-secondary"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-rr-primary">
                  Save Watchlist
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
