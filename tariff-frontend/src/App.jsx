import TariffCalculatorv2 from './pages/TariffCalculatorv2';
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from './pages/Login';
import ProtectedRoute from './components/ProtectedRoute';
import { useState } from 'react';
import HistoricalTariffExplorer from './pages/HistoricalTariffExplorer';
import UserManagement from './pages/UserManagement';
import Dashboard from './components/Dashboard';
import Profile from './pages/Profile';
import Header from './components/Header';
import LandingPage from './pages/LandingPage';
import { AuthProvider } from './utils/AuthProvider';

function AppContent() {

  return (
    <Router>
      <div className="min-h-screen bg-background font-sans antialiased">
        <div className="relative flex min-h-screen flex-col">
          <Header />
          <main className="flex-1">
            <Routes>
              {/* PUBLIC ROUTES */}
              <Route path="/login" element={
                <section className="flex flex-col items-center justify-center p-6 w-full">
                  <Login />
                </section>
              } />

              {/* PROTECTED ROUTES */}
              <Route element={<ProtectedRoute />}>
                <Route path="/" element={<LandingPage />} />
                <Route path="/calculator" element={
                  <section className="container mx-auto py-8 md:py-12 lg:py-24">
                    <TabsWithTariff/>
                  </section>
                } />
                <Route path="/user-management" element={<UserManagement />} />
                <Route path="/profile" element={<Profile />} />
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
        {tab === "search" && <TariffCalculatorv2 />}
        {tab === "dashboard" && <Dashboard />}
        {tab === "historical" && <HistoricalTariffExplorer />}
      </div>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
