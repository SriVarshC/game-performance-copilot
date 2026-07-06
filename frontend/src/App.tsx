// ═══════════════════════════════════════════════════════════
// Game Performance Copilot — App Router
// Phase 1 — React Router v6 setup
// ═══════════════════════════════════════════════════════════

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";

// Pages (we'll create these next)
import Dashboard  from "./pages/Dashboard";
import Analytics  from "./pages/Analytics";
import Prediction from "./pages/Prediction";
import Copilot    from "./pages/Copilot";

// Layout
import Navbar  from "./components/Navbar";
import Sidebar from "./components/Sidebar";

function App() {
  return (
    <BrowserRouter>
      <div className="d-flex flex-column" style={{ minHeight: "100vh", backgroundColor: "#0f1117" }}>

        {/* Top navigation bar */}
        <Navbar />

        <div className="d-flex flex-grow-1">

          {/* Left sidebar */}
          <Sidebar />

          {/* Main content area */}
          <main className="flex-grow-1 p-4" style={{ overflowY: "auto" }}>
            <Routes>
              <Route path="/"           element={<Dashboard />}  />
              <Route path="/analytics"  element={<Analytics />}  />
              <Route path="/prediction" element={<Prediction />} />
              <Route path="/copilot"    element={<Copilot />}    />
              {/* Catch-all → redirect to dashboard */}
              <Route path="*"           element={<Navigate to="/" replace />} />
            </Routes>
          </main>

        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;