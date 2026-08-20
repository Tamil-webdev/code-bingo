import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { 
  Trophy, Plus, Play, Pause, Square, 
  ChevronRight, UserCheck, AlertCircle, FileSpreadsheet
} from "lucide-react";
import api from "../api";

interface Round {
  id: string;
  tournament_id: string;
  name: string;
  order: number;
  board_size: number;
  timer_seconds: number;
  difficulty: string;
  num_questions: number;
  qualification_count: number;
  status: string;
  participant_count: number;
}

interface Tournament {
  id: string;
  name: string;
  description: string;
  status: string;
  max_teams: number;
  num_rounds: number;
}

export const Tournaments: React.FC = () => {
  const [tournaments, setTournaments] = useState<Tournament[]>([]);
  const [activeTournament, setActiveTournament] = useState<Tournament | null>(null);
  const [rounds, setRounds] = useState<Round[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [teamsList, setTeamsList] = useState<{ id: string; team_name: string }[]>([]);

  // Tournament Form state
  const [showCreate, setShowCreate] = useState(false);
  const [tName, setTName] = useState("");
  const [tDesc, setTDesc] = useState("");
  const [tMaxTeams, setTMaxTeams] = useState(50);
  const [tNumRounds, setTNumRounds] = useState(3);

  // Round Form state
  const [showAddRound, setShowAddRound] = useState(false);
  const [rName, setRName] = useState("");
  const [rSize, setRSize] = useState(5);
  const [rTimer, setRTimer] = useState(600);
  const [rDiff, setRDiff] = useState("mixed");
  const [rQualCount, setRQualCount] = useState(10);

  const fetchTournaments = async () => {
    try {
      const response = await api.get("/api/tournaments/");
      setTournaments(response.data);
      if (response.data.length > 0) {
        // Select first active or first tournament by default
        const active = response.data.find((t: Tournament) => t.status === "active") || response.data[0];
        handleSelectTournament(active);
      } else {
        setLoading(false);
      }
    } catch (err) {
      setError("Failed to fetch tournaments");
      setLoading(false);
    }
  };

  const fetchTeams = async () => {
    try {
      const res = await api.get("/api/teams/");
      setTeamsList(res.data);
    } catch (err) {}
  };

  useEffect(() => {
    fetchTournaments();
    fetchTeams();
  }, []);

  const handleSelectTournament = async (t: Tournament) => {
    setActiveTournament(t);
    setLoading(true);
    setError("");
    try {
      const response = await api.get(`/api/tournaments/${t.id}`);
      setRounds(response.data.rounds || []);
      setLoading(false);
    } catch (err) {
      setError("Failed to load tournament rounds");
      setLoading(false);
    }
  };

  const handleCreateTournament = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tName.trim()) return;

    try {
      await api.post("/api/tournaments/", {
        name: tName.trim(),
        description: tDesc.trim() || null,
        max_teams: tMaxTeams,
        num_rounds: tNumRounds,
        rounds: [], // Created empty first
      });

      // Refresh list
      setShowCreate(false);
      setTName("");
      setTDesc("");
      fetchTournaments();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create tournament");
    }
  };

  const handleAddRound = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeTournament || !rName.trim()) return;

    try {
      await api.post(`/api/tournaments/${activeTournament.id}/rounds`, {
        name: rName.trim(),
        board_size: rSize,
        timer_seconds: rTimer,
        difficulty: rDiff,
        num_questions: rSize * rSize,
        qualification_count: rQualCount,
      });

      setShowAddRound(false);
      setRName("");
      handleSelectTournament(activeTournament);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to add round");
    }
  };

  const startTournament = async () => {
    if (!activeTournament) return;
    try {
      await api.post(`/api/tournaments/${activeTournament.id}/start`);
      fetchTournaments();
    } catch (err) {}
  };

  const handleRoundAction = async (roundId: string, action: "start" | "pause" | "resume" | "end") => {
    if (!activeTournament) return;
    try {
      await api.post(`/api/tournaments/rounds/${roundId}/${action}`);
      handleSelectTournament(activeTournament);
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to ${action} round`);
    }
  };

  const handleAddAllTeams = async (roundId: string) => {
    if (teamsList.length === 0) return;
    try {
      const ids = teamsList.map(t => t.id);
      await api.post(`/api/tournaments/rounds/${roundId}/add-teams`, ids);
      if (activeTournament) handleSelectTournament(activeTournament);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to add teams to round");
    }
  };

  const handleAdvanceTeams = async (roundId: string) => {
    try {
      const res = await api.post(`/api/tournaments/rounds/${roundId}/advance-qualified`);
      alert(`Teams advanced successfully! ${res.data.message}`);
      if (activeTournament) handleSelectTournament(activeTournament);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to advance teams");
    }
  };

  const handleExportCSV = (roundId: string) => {
    // Generate results download locally
    // Trigger window location to backend export or display alert.
    alert("Exporting Leaderboard results to CSV format...");
    window.open(`${api.defaults.baseURL}/api/game/leaderboard/${roundId}`);
  };

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-wide">
            Tournament <span className="text-amber-500">Manager</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Build custom tournament brackets, manage live rounds and qualifications
          </p>
        </div>

        <button
          onClick={() => setShowCreate(true)}
          className="px-5 py-2.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl flex items-center gap-2 text-sm transition self-start"
        >
          <Plus className="w-5 h-5" />
          Create Tournament
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/30 border border-rose-800/30 text-rose-300 rounded-xl flex gap-3 text-sm">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left column: Tournament Selectors */}
        <div className="space-y-4">
          <h2 className="text-sm font-semibold tracking-wider text-slate-500 uppercase font-mono">
            Tournaments
          </h2>
          <div className="space-y-3">
            {loading && tournaments.length === 0 ? (
              <div className="flex justify-center p-4">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-amber-500"></div>
              </div>
            ) : tournaments.map((t) => {
              const isActive = activeTournament?.id === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => handleSelectTournament(t)}
                  className={`w-full p-4 rounded-xl text-left border transition ${
                    isActive 
                      ? "bg-slate-800 border-amber-500/50 text-white" 
                      : "bg-[#0E1524]/60 border-slate-800 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-slate-200 truncate">{t.name}</h3>
                    <ChevronRight className="w-4 h-4 text-slate-500" />
                  </div>
                  <div className="flex items-center gap-4 mt-2 text-xs">
                    <span className={`px-2 py-0.5 rounded-full uppercase font-bold tracking-wider text-[10px] ${
                      t.status === "active" ? "bg-emerald-950/50 text-emerald-400 border border-emerald-800/30" : "bg-slate-900 text-slate-500"
                    }`}>
                      {t.status}
                    </span>
                    <span>{t.num_rounds} Rounds</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right column: Rounds Details */}
        <div className="lg:col-span-2 space-y-6">
          {activeTournament ? (
            <div className="p-6 rounded-2xl glass-card border-slate-800 space-y-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
                <div>
                  <h2 className="text-xl font-bold text-slate-200">{activeTournament.name}</h2>
                  <p className="text-slate-500 text-sm mt-1">{activeTournament.description}</p>
                </div>

                <div className="flex gap-3">
                  {activeTournament.status === "draft" && (
                    <button
                      onClick={startTournament}
                      className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold rounded-xl flex items-center gap-1.5 transition"
                    >
                      <Play className="w-4 h-4" />
                      Start Tournament
                    </button>
                  )}

                  <button
                    onClick={() => setShowAddRound(true)}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold rounded-xl flex items-center gap-1.5 transition"
                  >
                    <Plus className="w-4 h-4" />
                    Add Round
                  </button>
                </div>
              </div>

              {/* Rounds List */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold tracking-wider text-slate-500 uppercase font-mono">
                  Round Brackets
                </h3>

                {rounds.length === 0 ? (
                  <p className="text-slate-500 text-sm text-center py-6">
                    No rounds created yet for this tournament.
                  </p>
                ) : (
                  <div className="space-y-4">
                    {rounds.map((round) => (
                      <div key={round.id} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                          <div>
                            <h4 className="font-bold text-slate-200 text-base">{round.name}</h4>
                            <p className="text-xs text-slate-500 mt-1">
                              Board Size: {round.board_size}x{round.board_size} • Timer: {Math.floor(round.timer_seconds / 60)}m • Difficulty: {round.difficulty}
                            </p>
                          </div>

                          <div className="flex items-center gap-3">
                            <span className={`px-2 py-0.5 rounded-full uppercase font-bold text-[10px] tracking-wider ${
                              round.status === "active" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" :
                              round.status === "paused" ? "bg-amber-950 text-amber-400 border border-amber-800" :
                              round.status === "completed" ? "bg-blue-950 text-blue-400 border border-blue-800" :
                              "bg-slate-800 text-slate-400"
                            }`}>
                              {round.status}
                            </span>
                            
                            <Link
                              to={`/live/${round.id}`}
                              className="px-3 py-1 bg-amber-500/10 hover:bg-amber-500/20 text-amber-500 text-xs font-bold rounded-lg border border-amber-500/30 transition"
                            >
                              Live Board
                            </Link>
                          </div>
                        </div>

                        {/* Actions for this round */}
                        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800/40">
                          {round.status === "pending" && (
                            <>
                              <button
                                onClick={() => handleAddAllTeams(round.id)}
                                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold rounded-lg flex items-center gap-1 transition"
                              >
                                <UserCheck className="w-3.5 h-3.5" />
                                Add Registered Teams ({round.participant_count})
                              </button>

                              <button
                                onClick={() => handleRoundAction(round.id, "start")}
                                className="px-3 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold rounded-lg flex items-center gap-1 transition"
                              >
                                <Play className="w-3.5 h-3.5" />
                                Start Round
                              </button>
                            </>
                          )}

                          {round.status === "active" && (
                            <>
                              <button
                                onClick={() => handleRoundAction(round.id, "pause")}
                                className="px-3 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold rounded-lg flex items-center gap-1 transition"
                              >
                                <Pause className="w-3.5 h-3.5" />
                                Pause Round
                              </button>

                              <button
                                onClick={() => handleRoundAction(round.id, "end")}
                                className="px-3 py-1.5 bg-rose-500 hover:bg-rose-400 text-slate-950 text-xs font-bold rounded-lg flex items-center gap-1 transition"
                              >
                                <Square className="w-3.5 h-3.5" />
                                End Round
                              </button>
                            </>
                          )}

                          {round.status === "paused" && (
                            <button
                              onClick={() => handleRoundAction(round.id, "resume")}
                              className="px-3 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold rounded-lg flex items-center gap-1 transition"
                            >
                              <Play className="w-3.5 h-3.5" />
                              Resume Round
                            </button>
                          )}

                          {round.status === "completed" && (
                            <>
                              <button
                                onClick={() => handleAdvanceTeams(round.id)}
                                className="px-3 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold rounded-lg flex items-center gap-1 transition"
                              >
                                <Trophy className="w-3.5 h-3.5" />
                                Advance Qualified Teams
                              </button>

                              <button
                                onClick={() => handleExportCSV(round.id)}
                                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold rounded-lg flex items-center gap-1 transition"
                              >
                                <FileSpreadsheet className="w-3.5 h-3.5" />
                                Export Leaderboard
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <p className="text-slate-500 text-center py-12">
              Select or create a tournament to begin configuration.
            </p>
          )}
        </div>
      </div>

      {/* Create Tournament Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <form onSubmit={handleCreateTournament} className="w-full max-w-md p-6 rounded-2xl glass-card border-slate-700 space-y-6">
            <h2 className="text-xl font-bold text-slate-200">New Tournament</h2>

            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs uppercase font-mono font-bold text-slate-400">Name</label>
                <input
                  type="text"
                  value={tName}
                  onChange={(e) => setTName(e.target.value)}
                  placeholder="Inaugural coding bracket"
                  required
                  className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs uppercase font-mono font-bold text-slate-400">Description</label>
                <textarea
                  value={tDesc}
                  onChange={(e) => setTDesc(e.target.value)}
                  placeholder="Optional notes"
                  className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-slate-200 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs uppercase font-mono font-bold text-slate-400">Max Teams</label>
                  <input
                    type="number"
                    value={tMaxTeams}
                    onChange={(e) => setTMaxTeams(Number(e.target.value))}
                    required
                    className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-slate-200 focus:outline-none"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-xs uppercase font-mono font-bold text-slate-400">Num Rounds</label>
                  <input
                    type="number"
                    value={tNumRounds}
                    onChange={(e) => setTNumRounds(Number(e.target.value))}
                    required
                    className="w-full px-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-slate-200 focus:outline-none"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="px-4 py-2 bg-slate-800 text-slate-300 rounded-xl text-sm"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-amber-500 text-slate-950 font-bold rounded-xl text-sm"
              >
                Save
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Add Round Modal */}
      {showAddRound && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <form onSubmit={handleAddRound} className="w-full max-w-md p-6 rounded-2xl glass-card border-slate-700 space-y-5">
            <h2 className="text-xl font-bold text-slate-200 font-mono">Add Bracket Round</h2>

            <div className="space-y-3">
              <div className="space-y-1">
                <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Round Name</label>
                <input
                  type="text"
                  value={rName}
                  onChange={(e) => setRName(e.target.value)}
                  placeholder="e.g. Round 1, Semi-Finals, Finals"
                  required
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Board Size</label>
                  <select
                    value={rSize}
                    onChange={(e) => setRSize(Number(e.target.value))}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-200"
                  >
                    <option value={3}>3 x 3</option>
                    <option value={4}>4 x 4</option>
                    <option value={5}>5 x 5</option>
                    <option value={6}>6 x 6</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Timer (seconds)</label>
                  <input
                    type="number"
                    value={rTimer}
                    onChange={(e) => setRTimer(Number(e.target.value))}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-200"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Difficulty</label>
                  <select
                    value={rDiff}
                    onChange={(e) => setRDiff(e.target.value)}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-200"
                  >
                    <option value="mixed">Mixed</option>
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Qualification Count</label>
                  <input
                    type="number"
                    value={rQualCount}
                    onChange={(e) => setRQualCount(Number(e.target.value))}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-200"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowAddRound(false)}
                className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-xs font-bold"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-amber-500 text-slate-950 font-bold rounded-lg text-xs"
              >
                Create Round
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
