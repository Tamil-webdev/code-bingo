import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Trophy,
  KeyRound,
  AlertCircle,
  Mail,
  UserPlus,
  LogIn,
  Users,
} from "lucide-react";
import {
  firebaseSignUp,
  tournamentLogin,
} from "../services/authService";
import { useAuth } from "../context/AuthContext";

type AuthMode = "signin" | "signup";

function getFirebaseErrorMessage(code: string): string {
  switch (code) {
    case "auth/email-already-in-use":
      return "An account with this email already exists. Try signing in instead.";
    case "auth/invalid-email":
      return "Please enter a valid email address.";
    case "auth/weak-password":
      return "Password must be at least 6 characters.";
    case "auth/user-not-found":
    case "auth/wrong-password":
    case "auth/invalid-credential":
      return "Invalid email or password.";
    case "auth/too-many-requests":
      return "Too many attempts. Please wait a moment and try again.";
    default:
      return "Authentication failed. Please try again.";
  }
}

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { appUser, loading: authLoading } = useAuth();
  const [mode, setMode] = useState<AuthMode>("signin");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [teamName, setTeamName] = useState("");
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (authLoading) return;
    const token = localStorage.getItem("bingo_token");
    const user = appUser ?? JSON.parse(localStorage.getItem("bingo_user") || "null");
    if (token && user?.role) {
      navigate(user.role === "admin" ? "/admin" : "/team", { replace: true });
    }
  }, [authLoading, appUser, navigate]);

  const redirectByRole = (role: string) => {
    navigate(role === "admin" ? "/admin" : "/team");
  };

  const handleFirebaseSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim() || !teamName.trim()) return;

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const data = await firebaseSignUp(
        email.trim(),
        password.trim(),
        teamName.trim()
      );
      redirectByRole(data.role);
    } catch (err: unknown) {
      const firebaseCode = (err as { code?: string })?.code;
      if (firebaseCode) {
        setError(getFirebaseErrorMessage(firebaseCode));
      } else {
        const apiDetail = (err as { response?: { data?: { detail?: string } } })?.response
          ?.data?.detail;
        setError(apiDetail || "Account creation failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleTournamentLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) return;

    setLoading(true);
    setError("");

    try {
      const data = await tournamentLogin(username.trim(), password.trim());
      redirectByRole(data.role);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number; data?: { detail?: string } } })
        ?.response?.status;
      if (status === 409) {
        setError(
          "This account is already logged in elsewhere. Only one device session allowed."
        );
      } else {
        setError(
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
            "Invalid credentials. Try again."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#070B13] flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#070B13] flex flex-col items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl -z-10 animate-pulse" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl -z-10" />

      <div className="w-full max-w-md p-8 rounded-2xl glass-card border-slate-800 shadow-2xl space-y-6 relative">
        <div className="text-center space-y-3">
          <div className="inline-flex p-3 bg-amber-500/10 border border-amber-500/25 rounded-2xl shadow-inner mb-2">
            <Trophy className="w-8 h-8 text-amber-500" />
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-wide">CODE BINGO</h1>
          <p className="text-slate-400 text-sm">
            {mode === "signup"
              ? "Create your team account to join tournaments"
              : "Sign in with your tournament credentials"}
          </p>
        </div>

        <div className="flex p-1 bg-slate-900/80 border border-slate-800 rounded-xl">
          <button
            type="button"
            onClick={() => {
              setMode("signin");
              setError("");
            }}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold transition ${
              mode === "signin"
                ? "bg-amber-500 text-slate-950"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <LogIn className="w-4 h-4" />
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setMode("signup");
              setError("");
            }}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold transition ${
              mode === "signup"
                ? "bg-amber-500 text-slate-950"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <UserPlus className="w-4 h-4" />
            Create Account
          </button>
        </div>

        {error && (
          <div className="p-4 bg-rose-950/40 border border-rose-800/50 rounded-xl flex gap-3 text-rose-300 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {mode === "signin" && (
          <form onSubmit={handleTournamentLogin} className="space-y-5">
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-400 font-mono tracking-wider uppercase">
                Username
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  disabled={loading}
                  autoComplete="username"
                  placeholder="e.g. team_binary"
                  className="w-full pl-11 pr-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500 font-mono transition"
                />
                <Mail className="absolute left-4 top-3.5 w-4.5 h-4.5 text-slate-500" />
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-400 font-mono tracking-wider uppercase">
                Password
              </label>
              <div className="relative">
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={loading}
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className="w-full pl-11 pr-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500 font-mono transition"
                />
                <KeyRound className="absolute left-4 top-3.5 w-4.5 h-4.5 text-slate-500" />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !username || !password}
              className="w-full py-3.5 bg-amber-500 hover:bg-amber-400 disabled:bg-slate-800 text-slate-950 disabled:text-slate-500 font-bold rounded-xl shadow-lg shadow-amber-500/10 hover:shadow-amber-500/20 transition-all duration-200 active:translate-y-0.5"
            >
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>
        )}

        {mode === "signup" && (
          <form onSubmit={handleFirebaseSignUp} className="space-y-5">
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-400 font-mono tracking-wider uppercase">
                Team Name
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={teamName}
                  onChange={(e) => setTeamName(e.target.value)}
                  required
                  disabled={loading}
                  placeholder="e.g. Code Warriors"
                  className="w-full pl-11 pr-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500 font-mono transition"
                />
                <Users className="absolute left-4 top-3.5 w-4.5 h-4.5 text-slate-500" />
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-400 font-mono tracking-wider uppercase">
                Email
              </label>
              <div className="relative">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={loading}
                  placeholder="you@example.com"
                  className="w-full pl-11 pr-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500 font-mono transition"
                />
                <Mail className="absolute left-4 top-3.5 w-4.5 h-4.5 text-slate-500" />
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-400 font-mono tracking-wider uppercase">
                Password
              </label>
              <div className="relative">
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={loading}
                  minLength={6}
                  placeholder="At least 6 characters"
                  className="w-full pl-11 pr-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500 font-mono transition"
                />
                <KeyRound className="absolute left-4 top-3.5 w-4.5 h-4.5 text-slate-500" />
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-400 font-mono tracking-wider uppercase">
                Confirm Password
              </label>
              <div className="relative">
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  disabled={loading}
                  placeholder="••••••••"
                  className="w-full pl-11 pr-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500 font-mono transition"
                />
                <KeyRound className="absolute left-4 top-3.5 w-4.5 h-4.5 text-slate-500" />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !email || !password || !teamName || !confirmPassword}
              className="w-full py-3.5 bg-amber-500 hover:bg-amber-400 disabled:bg-slate-800 text-slate-950 disabled:text-slate-500 font-bold rounded-xl shadow-lg shadow-amber-500/10 hover:shadow-amber-500/20 transition-all duration-200 active:translate-y-0.5"
            >
              {loading ? "Creating account..." : "Create Account"}
            </button>
          </form>
        )}

      </div>
    </div>
  );
};
