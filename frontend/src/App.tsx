import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { Login } from "./pages/Login";
import { AdminDashboard } from "./pages/AdminDashboard";
import { Tournaments } from "./pages/Tournaments";
import { Teams } from "./pages/Teams";
import { Questions } from "./pages/Questions";
import { LiveLeaderboardPage } from "./pages/LiveLeaderboardPage";
import { TeamDashboard } from "./pages/TeamDashboard";
import { DashboardLayout } from "./components/DashboardLayout";

// Guard wrapper for Admin access
const AdminGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = localStorage.getItem("bingo_token");
  const user = JSON.parse(localStorage.getItem("bingo_user") || "{}");

  if (!token || user.role !== "admin") {
    return <Navigate to="/login" replace />;
  }

  return <DashboardLayout>{children}</DashboardLayout>;
};

// Guard wrapper for Team access
const TeamGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = localStorage.getItem("bingo_token");
  const user = JSON.parse(localStorage.getItem("bingo_user") || "{}");

  if (!token || user.role !== "team") {
    return <Navigate to="/login" replace />;
  }

  return <DashboardLayout>{children}</DashboardLayout>;
};

function App() {
  return (
    <Router>
      <Routes>
        {/* Public login */}
        <Route path="/login" element={<Login />} />

        {/* Admin space */}
        <Route
          path="/admin"
          element={
            <AdminGuard>
              <AdminDashboard />
            </AdminGuard>
          }
        />
        <Route
          path="/admin/tournaments"
          element={
            <AdminGuard>
              <Tournaments />
            </AdminGuard>
          }
        />
        <Route
          path="/admin/teams"
          element={
            <AdminGuard>
              <Teams />
            </AdminGuard>
          }
        />
        <Route
          path="/admin/questions"
          element={
            <AdminGuard>
              <Questions />
            </AdminGuard>
          }
        />

        {/* Live projector leaderboard view */}
        <Route path="/live/:roundId" element={<LiveLeaderboardPage />} />

        {/* Team space */}
        <Route
          path="/team"
          element={
            <TeamGuard>
              <TeamDashboard />
            </TeamGuard>
          }
        />

        {/* Fallbacks */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
