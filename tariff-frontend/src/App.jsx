import TariffCalculator from './pages/TariffCalculator';
import { ModeToggle } from './components/mode-toggle';
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from './pages/Login';
import ProtectedRoute from './components/ProtectedRoute';
import { useState, useEffect } from 'react';
import HistoricalTariffExplorer from './pages/HistoricalTariffExplorer';
import UserManagement from './pages/UserManagement';
import Dashboard from './components/Dashboard';
import Profile from './pages/Profile';
import Header from './components/Header';

function App() {
  const [user, setUser] = useState(null);

  // Restore user on initial load
  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  // Persist user when it changes
  useEffect(() => {
    if (user) {
      localStorage.setItem("user", JSON.stringify(user));
    } else {
      localStorage.removeItem("user");
    }
  }, [user]);

  return (
    <Router>
      <div className="min-h-screen bg-background font-sans antialiased">
        <div className="relative flex min-h-screen flex-col">
          <Header user={user} setUser={setUser} />
          <main className="flex-1">
            <Routes>
              {/* PUBLIC ROUTES */}
              <Route path="/">
                <Route index element={
                  <section className="flex flex-col items-center justify-center p-6 w-full">
                    <Login setUser={setUser} />
                  </section>
                } />
                <Route path="login" element={
                    <section className="flex flex-col items-center justify-center p-6 w-full">
                      <Login setUser={setUser} />
                    </section>
                  } />
              </Route>

              {/* PROTECTED ROUTES */}
              <Route element={<ProtectedRoute />}>
                <Route path="/calculator" element={
                    <section className="mx-auto flex max-w-[980px] flex-col items-center gap-2 py-8 md:py-12 md:pb-8 lg:py-24 lg:pb-20">
                      <TabsWithTariff />
                    </section>
                  }
                />
                <Route path="/user-management" element={<UserManagement />} />
                <Route path="/profile" element={<Profile user={user} />} />
              </Route>
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

function TabsWithTariff() {
  const [tab, setTab] = useState("search");

  return (
    <div className="w-full">
      <div className="mb-4 border-b">
        <div className="inline-flex rounded-xl bg-muted p-1">
          <button
            className={`px-4 py-2 rounded-lg text-sm transition ${tab === "search" ? "bg-background shadow" : "opacity-70 hover:opacity-100"
              }`}
            onClick={() => setTab("search")}
          >
            Search &amp; Compute
          </button>
          <button
            className={`px-4 py-2 rounded-lg text-sm transition ${tab === "dashboard" ? "bg-background shadow" : "opacity-70 hover:opacity-100"
              }`}
            onClick={() => setTab("dashboard")}
          >
            Dashboard
          </button>
          <button
            className={`px-4 py-2 rounded-lg text-sm transition ${tab === "historical" ? "bg-background shadow" : "opacity-70 hover:opacity-100"
              }`}
            onClick={() => setTab("historical")}
          >
            Historical Explorer
          </button>
        </div>
      </div>

      <div className="grid gap-6">
        {tab === "search" && <TariffCalculator />}
        {tab === "dashboard" && <Dashboard />}
        {tab === "historical" && <HistoricalTariffExplorer />}
      </div>
    </div>
  );
}

export default App;
