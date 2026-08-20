import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { 
  Trophy, Users, HelpCircle, Activity, 
  ArrowUpRight, AlertCircle, CircleDot 
} from "lucide-react";
import api from "../api";

interface Stats {
  total_tournaments: number;
  active_tournaments: number;
  total_teams: number;
  total_questions: number;
  total_rounds: number;
  active_rounds: number;
  online_teams: number;
}

export const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchStats = async () => {
    try {
      const response = await api.get("/api/game/admin/dashboard");
      setStats(response.data);
      setLoading(false);
    } catch (err: any) {
      setError("Failed to load dashboard metrics");
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    // Auto-update every 10 seconds
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Top Welcome Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-wide">
            Admin <span className="text-amber-500">Dashboard</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Real-time control center for tournaments and team progression
          </p>
        </div>
        
        <div className="flex items-center gap-2 px-4 py-2 bg-emerald-950/40 border border-emerald-500/20 text-emerald-400 rounded-full text-xs font-mono font-bold self-start">
          <CircleDot className="w-4.5 h-4.5 animate-pulse" />
          <span>REAL-TIME UPDATE ACTIVE</span>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/30 border border-rose-800/30 text-rose-300 rounded-xl flex gap-3 text-sm">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Card 1: Active Tournament */}
          <div className="p-6 rounded-2xl glass border-slate-800 flex items-center justify-between">
            <div className="space-y-2">
              <p className="text-xs uppercase font-mono font-bold tracking-wider text-slate-500">
                Tournaments Active
              </p>
              <h3 className="text-3xl font-extrabold">{stats.active_tournaments} / {stats.total_tournaments}</h3>
            </div>
            <div className="p-4 bg-amber-500/10 rounded-2xl">
              <Trophy className="w-6 h-6 text-amber-500" />
            </div>
          </div>

          {/* Card 2: Teams Registered */}
          <div className="p-6 rounded-2xl glass border-slate-800 flex items-center justify-between">
            <div className="space-y-2">
              <p className="text-xs uppercase font-mono font-bold tracking-wider text-slate-500">
                Teams Online / Total
              </p>
              <h3 className="text-3xl font-extrabold">{stats.online_teams} / {stats.total_teams}</h3>
            </div>
            <div className="p-4 bg-blue-500/10 rounded-2xl">
              <Users className="w-6 h-6 text-blue-500" />
            </div>
          </div>

          {/* Card 3: Questions Pool */}
          <div className="p-6 rounded-2xl glass border-slate-800 flex items-center justify-between">
            <div className="space-y-2">
              <p className="text-xs uppercase font-mono font-bold tracking-wider text-slate-500">
                Questions Bank
              </p>
              <h3 className="text-3xl font-extrabold">{stats.total_questions}</h3>
            </div>
            <div className="p-4 bg-indigo-500/10 rounded-2xl">
              <HelpCircle className="w-6 h-6 text-indigo-500" />
            </div>
          </div>

          {/* Card 4: Active Rounds */}
          <div className="p-6 rounded-2xl glass border-slate-800 flex items-center justify-between">
            <div className="space-y-2">
              <p className="text-xs uppercase font-mono font-bold tracking-wider text-slate-500">
                Rounds Playing Now
              </p>
              <h3 className="text-3xl font-extrabold">{stats.active_rounds} / {stats.total_rounds}</h3>
            </div>
            <div className="p-4 bg-rose-500/10 rounded-2xl">
              <Activity className="w-6 h-6 text-rose-500" />
            </div>
          </div>
        </div>
      )}

      {/* Admin Action Panels */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="p-8 rounded-2xl glass-card border-slate-800 space-y-6">
          <h2 className="text-xl font-bold tracking-wide">Tournament Administration</h2>
          <p className="text-slate-400 text-sm leading-relaxed">
            Create unlimited Rounds, custom board sizes (3x3 up to 6x6), define qualifications constraints, control timer speeds, and coordinate qualification advancements.
          </p>
          <div className="flex gap-4">
            <Link
              to="/admin/tournaments"
              className="px-5 py-2.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl flex items-center gap-2 text-sm transition-all duration-200"
            >
              Manage Tournaments
              <ArrowUpRight className="w-4 h-4" />
            </Link>
          </div>
        </div>

        <div className="p-8 rounded-2xl glass-card border-slate-800 space-y-6">
          <h2 className="text-xl font-bold tracking-wide">Question Bank & Team Portals</h2>
          <p className="text-slate-400 text-sm leading-relaxed">
            Manually create teams or seed credentials in bulk via CSV imports. Add, delete or update coding challenges programmatically with full CSV templates.
          </p>
          <div className="flex gap-4">
            <Link
              to="/admin/questions"
              className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-xl flex items-center gap-2 text-sm transition-all duration-200"
            >
              Question Bank
              <ArrowUpRight className="w-4 h-4" />
            </Link>
            <Link
              to="/admin/teams"
              className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-xl flex items-center gap-2 text-sm transition-all duration-200"
            >
              Manage Teams
              <ArrowUpRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
