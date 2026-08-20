import React, { useState, useEffect } from "react";
import { Plus, Users, Upload, Key, FileText, AlertCircle, Trash2 } from "lucide-react";
import api from "../api";

interface TeamMember {
  id: string;
  name: string;
  email: string | null;
  role_in_team: string | null;
}

interface Team {
  id: string;
  team_name: string;
  college_name: string | null;
  username: string;
  members: TeamMember[];
}

export const Teams: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Modals
  const [showCreate, setShowCreate] = useState(false);
  const [showGenerate, setShowGenerate] = useState(false);
  const [generatedCreds, setGeneratedCreds] = useState<any[]>([]);

  // Create form state
  const [tName, setTName] = useState("");
  const [tCollege, setTCollege] = useState("");
  const [tUser, setTUser] = useState("");
  const [tPass, setTPass] = useState("");

  // Generate form state
  const [genCount, setGenCount] = useState(10);
  const [genPrefix, setGenPrefix] = useState("team");
  const [genCollege, setGenCollege] = useState("");

  const fetchTeams = async () => {
    try {
      const response = await api.get("/api/teams/");
      setTeams(response.data);
      setLoading(false);
    } catch (err) {
      setError("Failed to fetch teams list");
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTeams();
  }, []);

  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tName.trim() || !tUser.trim() || !tPass.trim()) return;

    try {
      await api.post("/api/teams/", {
        team_name: tName.trim(),
        college_name: tCollege.trim() || null,
        username: tUser.trim(),
        password: tPass.trim(),
        members: []
      });

      setSuccess("Team created successfully!");
      setShowCreate(false);
      // Reset fields
      setTName("");
      setTCollege("");
      setTUser("");
      setTPass("");
      fetchTeams();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create team");
    }
  };

  const handleGenerateCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await api.post(`/api/teams/generate-credentials?count=${genCount}&prefix=${genPrefix}&college=${genCollege}`);
      setGeneratedCreds(response.data);
      setSuccess("Successfully generated credentials!");
      setShowGenerate(false);
      fetchTeams();
    } catch (err: any) {
      setError("Failed to auto-generate teams");
    }
  };

  const handleDeleteTeam = async (id: string) => {
    if (!confirm("Are you sure you want to delete this team?")) return;
    try {
      await api.delete(`/api/teams/${id}`);
      setSuccess("Team deleted");
      fetchTeams();
    } catch (err) {
      setError("Failed to delete team");
    }
  };

  const handleCSVUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      setError("");
      setSuccess("");
      const response = await api.post("/api/teams/import-csv", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setGeneratedCreds(response.data);
      setSuccess("CSV Roster imported successfully!");
      fetchTeams();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to import CSV roster");
    }
  };

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-wide">
            Team <span className="text-amber-500">Registry</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Generate team login credentials, manage student rosters, and upload bulk CSV templates
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <label className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-xl flex items-center gap-2 text-sm cursor-pointer transition">
            <Upload className="w-4.5 h-4.5" />
            Import CSV
            <input type="file" accept=".csv" onChange={handleCSVUpload} className="hidden" />
          </label>

          <button
            onClick={() => setShowGenerate(true)}
            className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-xl flex items-center gap-2 text-sm transition"
          >
            <Key className="w-4.5 h-4.5" />
            Batch Credentials
          </button>

          <button
            onClick={() => setShowCreate(true)}
            className="px-5 py-2.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl flex items-center gap-2 text-sm transition"
          >
            <Plus className="w-5 h-5" />
            Add Single Team
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/30 border border-rose-800/30 text-rose-300 rounded-xl flex gap-3 text-sm">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="p-4 bg-emerald-950/30 border border-emerald-800/30 text-emerald-300 rounded-xl text-sm">
          {success}
        </div>
      )}

      {/* Generated Credentials display block */}
      {generatedCreds.length > 0 && (
        <div className="p-6 rounded-2xl bg-amber-950/20 border border-amber-500/25 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-amber-400 flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Generated Login Credentials (Save these now!)
            </h3>
            <button
              onClick={() => setGeneratedCreds([])}
              className="text-xs text-slate-400 hover:text-white"
            >
              Clear display
            </button>
          </div>
          <div className="max-h-60 overflow-y-auto border border-slate-800 rounded-lg font-mono text-xs divide-y divide-slate-800">
            <div className="grid grid-cols-3 p-2 bg-slate-900 text-slate-400 font-bold">
              <span>Team Name</span>
              <span>Username</span>
              <span>Password</span>
            </div>
            {generatedCreds.map((cred, idx) => (
              <div key={idx} className="grid grid-cols-3 p-2 text-slate-200">
                <span>{cred.team_name}</span>
                <span>{cred.username}</span>
                <span className="text-amber-300 font-bold">{cred.password}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Teams Grid List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
        </div>
      ) : teams.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          <Users className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p>No teams registered yet. Use buttons above to import or create.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {teams.map((team) => (
            <div key={team.id} className="p-6 rounded-2xl glass-card border-slate-800 space-y-4">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-bold text-lg text-slate-100">{team.team_name}</h3>
                  <p className="text-xs text-slate-400 mt-0.5">{team.college_name || "No College"}</p>
                </div>
                <button
                  onClick={() => handleDeleteTeam(team.id)}
                  className="p-2 text-slate-500 hover:text-rose-400 transition"
                >
                  <Trash2 className="w-4.5 h-4.5" />
                </button>
              </div>

              <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400 font-mono">
                <span>Username: <span className="text-slate-200">{team.username}</span></span>
                <span>One Session Limit</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Team Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <form onSubmit={handleCreateTeam} className="w-full max-w-md p-6 rounded-2xl glass-card border-slate-700 space-y-4">
            <h2 className="text-xl font-bold text-slate-200">Register New Team</h2>

            <div className="space-y-3">
              <div className="space-y-1">
                <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Team Name</label>
                <input
                  type="text"
                  value={tName}
                  onChange={(e) => setTName(e.target.value)}
                  placeholder="e.g. Code Ninjas"
                  required
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[10px] uppercase font-mono font-bold text-slate-400">College / Institution</label>
                <input
                  type="text"
                  value={tCollege}
                  onChange={(e) => setTCollege(e.target.value)}
                  placeholder="e.g. MIT"
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Username</label>
                  <input
                    type="text"
                    value={tUser}
                    onChange={(e) => setTUser(e.target.value)}
                    placeholder="e.g. team_ninjas"
                    required
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Password</label>
                  <input
                    type="password"
                    value={tPass}
                    onChange={(e) => setTPass(e.target.value)}
                    placeholder="••••••••"
                    required
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-xs font-bold"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-amber-500 text-slate-950 font-bold rounded-lg text-xs"
              >
                Register
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Batch Generator Modal */}
      {showGenerate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <form onSubmit={handleGenerateCredentials} className="w-full max-w-md p-6 rounded-2xl glass-card border-slate-700 space-y-4">
            <h2 className="text-xl font-bold text-slate-200">Batch Credential Generator</h2>

            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Count</label>
                  <input
                    type="number"
                    value={genCount}
                    onChange={(e) => setGenCount(Number(e.target.value))}
                    min={1}
                    max={100}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Username Prefix</label>
                  <input
                    type="text"
                    value={genPrefix}
                    onChange={(e) => setGenPrefix(e.target.value)}
                    placeholder="e.g. team"
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Default College</label>
                <input
                  type="text"
                  value={genCollege}
                  onChange={(e) => setGenCollege(e.target.value)}
                  placeholder="e.g. MIT"
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowGenerate(false)}
                className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-xs font-bold"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-amber-500 text-slate-950 font-bold rounded-lg text-xs"
              >
                Generate
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
