// ═══════════════════════════════════════════════════════════
// Game Performance Copilot — App Router
// Phase 8 — adds AuthProvider + Login + ProtectedRoute
// Phase 11 — adds Performance monitoring page
// ═══════════════════════════════════════════════════════════

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";

// Pages
import Dashboard    from "./pages/Dashboard";
import Analytics    from "./pages/Analytics";
import Prediction   from "./pages/Prediction";
import Copilot      from "./pages/Copilot";
import Login        from "./pages/Login";
import Performance  from "./pages/Performance";

// Layout
import Navbar  from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import ProtectedRoute from "./components/ProtectedRoute";

// Auth
import { AuthProvider, useAuth } from "./contexts/AuthContext";

function AppShell() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="d-flex flex-column" style={{ minHeight: "100vh", backgroundColor: "#0f1117" }}>

      {/* Top navigation bar */}
      <Navbar />

      <div className="d-flex flex-grow-1">

        {/* Left sidebar — only shown once logged in */}
        {isAuthenticated && <Sidebar />}

        {/* Main content area */}
        <main className="flex-grow-1 p-4" style={{ overflowY: "auto" }}>
          <Routes>
            <Route path="/login" element={<Login />} />

            <Route path="/" element={
              <ProtectedRoute><Dashboard /></ProtectedRoute>
            } />
            <Route path="/analytics" element={
              <ProtectedRoute><Analytics /></ProtectedRoute>
            } />
            <Route path="/prediction" element={
              <ProtectedRoute><Prediction /></ProtectedRoute>
            } />
            <Route path="/copilot" element={
              <ProtectedRoute><Copilot /></ProtectedRoute>
            } />
            <Route path="/performance" element={
              <ProtectedRoute><Performance /></ProtectedRoute>
            } />

            {/* Catch-all → redirect to dashboard (which itself redirects to
                /login if not authenticated, via ProtectedRoute) */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>

      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppShell />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;