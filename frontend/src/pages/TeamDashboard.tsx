import React, { useState, useEffect, useRef } from "react";
import { Trophy, Clock, Target, AlertCircle, RefreshCw } from "lucide-react";
import { BingoBoard } from "../components/BingoBoard";
import type { Tile } from "../components/BingoBoard";
import { QuestionModal } from "../components/QuestionModal";
import api, { WS_URL } from "../api";
import confetti from "canvas-confetti";

export const TeamDashboard: React.FC = () => {
  const [board, setBoard] = useState<{ id: string; round_id: string; size: number; tiles: Tile[] } | null>(null);
  const [tournamentName, setTournamentName] = useState<string | null>(null);
  const [roundName, setRoundName] = useState("");
  const [score, setScore] = useState(0);
  const [rank, setRank] = useState(0);
  const [bingoCount, setBingoCount] = useState(0);
  const [remainingTime, setRemainingTime] = useState(0);
  const [roundActive, setRoundActive] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [wsConnected, setWsConnected] = useState(false);

  // Active question state
  const [activeTile, setActiveTile] = useState<Tile | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const user = JSON.parse(localStorage.getItem("bingo_user") || "{}");

  const triggerWinningConfetti = () => {
    confetti({
      particleCount: 150,
      spread: 80,
      origin: { y: 0.6 }
    });
  };

  const fetchTeamDashboardData = async () => {
    try {
      const statsRes = await api.get("/api/game/team/dashboard");
      setScore(statsRes.data.current_score);
      setRank(statsRes.data.current_rank);
      setBingoCount(statsRes.data.bingo_count);
      setRemainingTime(statsRes.data.remaining_time);
      setTournamentName(statsRes.data.current_tournament || null);
      setRoundName(statsRes.data.current_round || "No Active Round");
      setError("");

      // Find active round board if any
      const t_dashboard = statsRes.data;
      if (t_dashboard.current_round) {
        // Find round details to get ID
        const tournaments = await api.get("/api/tournaments/");
        const activeT = tournaments.data.find((t: any) => t.status === "active");
        if (activeT) {
          const tDetails = await api.get(`/api/tournaments/${activeT.id}`);
          const activeRound = tDetails.data.rounds.find((r: any) => r.status === "active");
          if (activeRound) {
            setRoundActive(true);
            const boardRes = await api.get(`/api/game/board/${activeRound.id}`);
            setBoard(boardRes.data);
            setupWebSocket(activeRound.id);
          } else {
            setRoundActive(false);
            setBoard(null);
          }
        }
      } else {
        setRoundActive(false);
        setBoard(null);
      }
      setLoading(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || "You do not have any active board session right now.");
      setLoading(false);
    }
  };

  const setupWebSocket = (roundId: string) => {
    if (socketRef.current) return; // Already setup

    const wsToken = localStorage.getItem("bingo_token") || "";
    const socket = new WebSocket(`${WS_URL}/api/game/ws/${roundId}?token=${wsToken}&user_id=${user.team_id}`);
    socketRef.current = socket;

    socket.onopen = () => {
      setWsConnected(true);
    };

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === "round_start") {
        setRoundActive(true);
        fetchTeamDashboardData();
      } else if (message.type === "round_end") {
        setRoundActive(false);
        setRemainingTime(0);
        alert("The current round has ended!");
      } else if (message.type === "timer_update") {
        setRemainingTime(message.data.remaining_seconds);
      } else if (message.type === "notification") {
        alert(message.data.message);
      }
    };

    socket.onclose = () => {
      setWsConnected(false);
      socketRef.current = null;
      // Auto-reconnect
      setTimeout(() => setupWebSocket(roundId), 3000);
    };
  };

  useEffect(() => {
    fetchTeamDashboardData();
    // A team is not connected to a round WebSocket until that round is active.
    // Polling keeps the dashboard in sync when an organizer starts a tournament
    // or its first round while the team is already on this page.
    const refreshInterval = window.setInterval(() => {
      // Once connected to an active round, WebSocket events are the source of
      // live updates. Continue polling only while waiting for a round.
      if (!socketRef.current) {
        fetchTeamDashboardData();
      }
    }, 5000);

    return () => {
      window.clearInterval(refreshInterval);
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, []);

  const handleTileClick = (tile: Tile) => {
    if (!roundActive || remainingTime <= 0) {
      alert("The round is not active!");
      return;
    }
    setActiveTile(tile);
  };

  const handleAnswerSubmitted = (answerResult: any) => {
    setActiveTile(null);
    setScore(answerResult.new_score);
    
    // Check if new bingo was created
    if (answerResult.new_bingo_count > bingoCount) {
      setBingoCount(answerResult.new_bingo_count);
      triggerWinningConfetti();
    }

    // Refresh board to display color updates
    if (board) {
      api.get(`/api/game/board/${board.round_id}`).then((res) => {
        setBoard(res.data);
      });
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

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
            Team: <span className="text-amber-500">{user.team_name || "Code Warrior"}</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1 flex items-center gap-2">
            {tournamentName ? `Active tournament: ${tournamentName}` : "No active tournament"}
            <span className="text-slate-600">•</span>
            Current bracket: {roundName}
            <span className={`w-2 h-2 rounded-full ${wsConnected ? "bg-emerald-500 animate-pulse" : "bg-rose-500"}`} title={wsConnected ? "Live Connection Active" : "Disconnected"} />
          </p>
        </div>

        <button 
          onClick={fetchTeamDashboardData}
          className="p-2.5 bg-slate-800 hover:bg-slate-700 rounded-xl text-slate-300 transition flex items-center gap-1 text-xs self-start"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/30 border border-rose-800/30 text-rose-300 rounded-xl flex gap-3 text-sm">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      {/* Stats row */}
      {roundActive && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="p-5 rounded-2xl glass border-slate-800 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase font-mono font-bold tracking-wider text-slate-500">Score</p>
              <h3 className="text-2xl font-extrabold text-amber-500 font-mono mt-1">{score}</h3>
            </div>
            <Trophy className="w-8 h-8 text-amber-500/20" />
          </div>

          <div className="p-5 rounded-2xl glass border-slate-800 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase font-mono font-bold tracking-wider text-slate-500">Current Rank</p>
              <h3 className="text-2xl font-extrabold text-white font-mono mt-1">#{rank || "-"}</h3>
            </div>
            <Target className="w-8 h-8 text-blue-500/20" />
          </div>

          <div className="p-5 rounded-2xl glass border-slate-800 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase font-mono font-bold tracking-wider text-slate-500">Total Bingos</p>
              <h3 className="text-2xl font-extrabold text-amber-500 font-mono mt-1">{bingoCount}</h3>
            </div>
            <Trophy className="w-8 h-8 text-amber-500/20" />
          </div>

          <div className="p-5 rounded-2xl glass border-slate-800 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase font-mono font-bold tracking-wider text-slate-500">Time Left</p>
              <h3 className={`text-2xl font-extrabold font-mono mt-1 ${remainingTime <= 60 ? "text-rose-500 animate-pulse" : "text-white"}`}>
                {formatTime(remainingTime)}
              </h3>
            </div>
            <Clock className="w-8 h-8 text-slate-500/20" />
          </div>
        </div>
      )}

      {/* Board Display */}
      {roundActive && board ? (
        <div className="py-6">
          <BingoBoard
            size={board.size}
            tiles={board.tiles}
            onTileClick={handleTileClick}
            disabled={!roundActive || remainingTime <= 0}
          />
        </div>
      ) : (
        <div className="p-12 rounded-2xl border border-slate-800/80 bg-slate-900/20 text-center space-y-4 max-w-xl mx-auto">
          <Trophy className="w-16 h-16 text-slate-500/30 mx-auto" />
          <h2 className="text-xl font-bold text-slate-300">
            {tournamentName ? `${tournamentName} is live` : "Waiting for Round to Start"}
          </h2>
          <p className="text-slate-500 text-sm max-w-md mx-auto leading-relaxed">
            {tournamentName
              ? "The organizer has not started your round yet. Keep this screen open; it will update automatically when the round begins."
              : "The organizer has not started a tournament yet. Keep this screen open; it will update automatically when one begins."}
          </p>
        </div>
      )}

      {/* Question Modal overlay */}
      {activeTile && (
        <QuestionModal
          tileId={activeTile.id}
          onClose={() => setActiveTile(null)}
          onAnswerSubmitted={handleAnswerSubmitted}
        />
      )}
    </div>
  );
};
