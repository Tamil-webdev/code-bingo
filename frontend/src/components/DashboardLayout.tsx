import React from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { 
  Trophy, LayoutDashboard, Calendar, Users, 
  HelpCircle, LogOut, Shield, Compass, User
} from "lucide-react";
import { logout } from "../services/authService";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const user = JSON.parse(localStorage.getItem("bingo_user") || "{}");

  const isAdmin = user.role === "admin";

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const navItems = isAdmin 
    ? [
        { name: "Dashboard", path: "/admin", icon: LayoutDashboard },
        { name: "Tournaments", path: "/admin/tournaments", icon: Calendar },
        { name: "Teams", path: "/admin/teams", icon: Users },
        { name: "Questions", path: "/admin/questions", icon: HelpCircle },
      ]
    : [
        { name: "Play Board", path: "/team", icon: Trophy },
      ];

  return (
    <div className="flex h-screen bg-[#070B13] text-slate-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800 bg-[#0E1524]/60 backdrop-blur-xl flex flex-col justify-between p-4 hidden md:flex">
        <div className="space-y-8">
          {/* Logo */}
          <div className="flex items-center gap-3 px-2">
            <div className="p-2 bg-amber-500/10 border border-amber-500/30 rounded-xl">
              <Trophy className="w-6 h-6 text-amber-500" />
            </div>
            <div>
              <h1 className="font-bold text-lg leading-tight tracking-wide">
                BINGO <span className="text-amber-500">Code</span>
              </h1>
              <p className="text-[10px] text-slate-500 font-semibold tracking-widest uppercase">
                Tournament
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1.5">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              const Icon = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold tracking-wide transition-all duration-200 ${
                    isActive
                      ? "bg-amber-500 text-slate-950 shadow-lg shadow-amber-500/15"
                      : "text-slate-400 hover:text-white hover:bg-slate-800/40"
                  }`}
                >
                  <Icon className="w-4.5 h-4.5" />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Info & Logout */}
        <div className="space-y-4 pt-4 border-t border-slate-800">
          <div className="flex items-center gap-3 px-2">
            <div className="p-2 bg-slate-800/80 rounded-full border border-slate-700">
              {isAdmin ? (
                <Shield className="w-5 h-5 text-amber-400" />
              ) : (
                <User className="w-5 h-5 text-blue-400" />
              )}
            </div>
            <div className="overflow-hidden">
              <p className="text-sm font-bold text-slate-200 truncate">
                {user.username || "User"}
              </p>
              <p className="text-xs text-slate-500 capitalize">{user.role || "Role"}</p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold text-rose-400 hover:text-rose-300 hover:bg-rose-950/20 transition-all duration-200"
          >
            <LogOut className="w-4.5 h-4.5" />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-16 border-b border-slate-800 bg-[#0E1524]/20 backdrop-blur-md flex items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <Compass className="w-5 h-5 text-slate-500" />
            <span className="text-xs uppercase font-mono tracking-wider font-semibold text-slate-500">
              {isAdmin ? "Admin Space" : "Team Space"}
            </span>
          </div>

          {/* Mobile navigation header */}
          <div className="flex items-center gap-4 md:hidden">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              const Icon = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`p-2 rounded-lg transition ${
                    isActive ? "text-amber-500" : "text-slate-400 hover:text-white"
                  }`}
                >
                  <Icon className="w-5 h-5" />
                </Link>
              );
            })}
            <button onClick={handleLogout} className="text-rose-400 p-2">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Content Body */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          {children}
        </main>
      </div>
    </div>
  );
};
