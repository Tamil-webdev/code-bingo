import React, { useState, useEffect, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { Trophy, Clock, Medal, Users, ArrowLeft, Wifi, WifiOff } from "lucide-react";
import api, { WS_URL } from "../api";

interface LeaderboardEntry {
  rank: number;
  team_id: string;
  team_name: string;
  score: number;
  bingo_count: number;
  correct_answers: number;
  accuracy: number;
  completion_percentage: number;
  avg_time: number;
}

export const LiveLeaderboardPage: React.FC = () => {
  const { roundId } = useParams<{ roundId: string }>();
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [roundName, setRoundName] = useState("");
  const [timerSeconds, setTimerSeconds] = useState(600);
  const [remainingTime, setRemainingTime] = useState(600);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const socketRef = useRef<WebSocket | null>(null);

  // Fetch initial leaderboard and round details
  const fetchRoundData = async () => {
    try {
      const roundRes = await api.get(`/api/tournaments/rounds/${roundId}`);
      setRoundName(roundRes.data.name);
      setTimerSeconds(roundRes.data.timer_seconds);
      
      if (roundRes.data.actual_start) {
        const elapsed = (Date.now() - new Date(roundRes.data.actual_start).getTime()) / 1000;
        setRemainingTime(Math.max(0, roundRes.data.timer_seconds - Math.floor(elapsed)));
      } else {
        setRemainingTime(roundRes.data.timer_seconds);
      }

      const lbRes = await api.get(`/api/game/leaderboard/${roundId}`);
      setEntries(lbRes.data.entries || []);
      setLoading(false);
    } catch (err) {
      setError("Failed to fetch leaderboard data");
      setLoading(false);
    }
  };

  useEffect(() => {
    // Print to fix tsc warning
    console.log("Timer configured for: ", timerSeconds);
    fetchRoundData();

    // Setup WebSocket connection
    const connectWS = () => {
      const wsToken = localStorage.getItem("bingo_token") || "";
      const socket = new WebSocket(`${WS_URL}/api/game/ws/${roundId}?token=${wsToken}`);
      socketRef.current = socket;

      socket.onopen = () => {
        setConnected(true);
        // Request immediate leaderboard
        socket.send(JSON.stringify({ type: "request_leaderboard" }));
      };

      socket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === "leaderboard_update") {
          setEntries(message.data);
        } else if (message.type === "timer_update") {
          setRemainingTime(message.data.remaining_seconds);
        } else if (message.type === "round_end") {
          setRemainingTime(0);
          alert("The round has ended!");
        }
      };

      socket.onclose = () => {
        setConnected(false);
        // Auto-reconnect after 3 seconds
        setTimeout(connectWS, 3000);
      };

      socket.onerror = () => {
        setConnected(false);
      };
    };

    connectWS();

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [roundId]);

  // Format timer seconds to MM:SS
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#070B13]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#070B13] text-slate-100 p-6 md:p-12 relative overflow-hidden">
      {/* Background glow decorators */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-amber-500/5 rounded-full blur-3xl -z-10"></div>

      <div className="max-w-6xl mx-auto space-y-8">
        {/* Navigation / Control Row */}
        <div className="flex items-center justify-between pb-6 border-b border-slate-800">
          <Link
            to="/admin/tournaments"
            className="flex items-center gap-2 text-slate-400 hover:text-white transition-all duration-200 text-sm font-semibold"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Tournaments
          </Link>

          <div className="flex items-center gap-4">
            {connected ? (
              <span className="flex items-center gap-1.5 px-3 py-1 bg-emerald-950/40 text-emerald-400 border border-emerald-800/30 rounded-full text-xs font-mono font-bold">
                <Wifi className="w-3.5 h-3.5" />
                WS LIVE
              </span>
            ) : (
              <span className="flex items-center gap-1.5 px-3 py-1 bg-rose-950/40 text-rose-400 border border-rose-800/30 rounded-full text-xs font-mono font-bold">
                <WifiOff className="w-3.5 h-3.5" />
                DISCONNECTED
              </span>
            )}
          </div>
        </div>

        {error && (
          <div className="p-4 bg-rose-950/40 border border-rose-800/30 text-rose-300 rounded-xl text-sm">
            {error}
          </div>
        )}

        {/* Title Header / Timer Box */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
          <div className="md:col-span-2 space-y-2">
            <h1 className="text-3xl md:text-4xl font-extrabold tracking-wide text-slate-100">
              Live <span className="text-amber-500">Leaderboard</span>
            </h1>
            <p className="text-slate-400 font-medium text-lg">
              {roundName || "Qualifying Bracket Round"}
            </p>
          </div>

          <div className="p-6 rounded-2xl glass-card border-slate-800 flex items-center justify-between shadow-lg">
            <div className="space-y-1">
              <span className="text-xs uppercase font-mono font-bold text-slate-500 tracking-wider">Remaining Time</span>
              <h2 className={`text-3xl font-extrabold font-mono ${remainingTime <= 60 ? "text-rose-500 animate-pulse" : "text-white"}`}>
                {formatTime(remainingTime)}
              </h2>
            </div>
            <div className="p-3 bg-slate-800 rounded-xl">
              <Clock className="w-6 h-6 text-slate-400" />
            </div>
          </div>
        </div>

        {/* Leaderboard Table */}
        <div className="rounded-2xl glass-card border-slate-800 shadow-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800/80 bg-slate-900/40 text-slate-400 text-xs font-bold font-mono uppercase tracking-wider">
                  <th className="py-4 px-6 text-center w-20">Rank</th>
                  <th className="py-4 px-6">Team Name</th>
                  <th className="py-4 px-6 text-center">Score</th>
                  <th className="py-4 px-6 text-center">Bingos</th>
                  <th className="py-4 px-6 text-center">Solved</th>
                  <th className="py-4 px-6 text-center">Accuracy</th>
                  <th className="py-4 px-6 text-center">Avg Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {entries.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-slate-500 text-sm">
                      <Users className="w-12 h-12 mx-auto mb-4 opacity-20" />
                      Waiting for answers to be submitted...
                    </td>
                  </tr>
                ) : (
                  entries.map((entry) => {
                    const isTopThree = entry.rank <= 3;
                    const rankColor = 
                      entry.rank === 1 ? "text-amber-400 bg-amber-500/10 border-amber-500/25" :
                      entry.rank === 2 ? "text-slate-300 bg-slate-300/10 border-slate-300/25" :
                      entry.rank === 3 ? "text-amber-600 bg-amber-600/10 border-amber-600/25" :
                      "text-slate-400 bg-slate-800/40 border-slate-700/40";

                    return (
                      <tr 
                        key={entry.team_id}
                        className={`hover:bg-slate-800/10 transition-colors duration-150 ${
                          isTopThree ? "bg-slate-800/5" : ""
                        }`}
                      >
                        <td className="py-5 px-6">
                          <div className={`flex items-center justify-center w-8 h-8 rounded-full border text-sm font-bold font-mono ${rankColor}`}>
                            {isTopThree ? <Medal className="w-4.5 h-4.5" /> : entry.rank}
                          </div>
                        </td>
                        <td className="py-5 px-6 font-bold text-slate-200 text-base">
                          {entry.team_name}
                        </td>
                        <td className="py-5 px-6 text-center font-extrabold text-amber-500 font-mono text-lg">
                          {entry.score}
                        </td>
                        <td className="py-5 px-6 text-center">
                          <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full font-bold font-mono text-xs ${
                            entry.bingo_count > 0 ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" : "bg-slate-800 text-slate-500"
                          }`}>
                            <Trophy className="w-3.5 h-3.5" />
                            {entry.bingo_count}
                          </span>
                        </td>
                        <td className="py-5 px-6 text-center font-medium font-mono text-slate-300">
                          {entry.correct_answers}
                        </td>
                        <td className="py-5 px-6 text-center font-medium font-mono text-slate-300">
                          {Math.round(entry.accuracy)}%
                        </td>
                        <td className="py-5 px-6 text-center font-medium font-mono text-slate-300">
                          {Math.round(entry.avg_time)}s
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
