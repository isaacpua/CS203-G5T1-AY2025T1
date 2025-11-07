import TariffCalculator from "./pages/TariffCalculator"
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from "react-router-dom"
import Login from "./pages/Login"
import ProtectedRoute from "./components/ProtectedRoute"
import HistoricalTariffExplorer from "./pages/HistoricalTariffExplorer"
import UserManagement from "./pages/UserManagement"
import Dashboard from "./pages/Dashboard"
import CalculationHistory from "./pages/CalculationHistory"
import Profile from "./pages/Profile"
import Header from "./components/Header"
import LandingPage from "./pages/LandingPage"
import { AuthProvider } from "./utils/AuthProvider"
import ChatbotPage from "./pages/Chatbot"
import Forecast from "./pages/Forecast"
import Newsletter from "./pages/Newsletter"
import AnimatedBackground from "./components/AnimatedBackground"

function AppContent() {
  const location = useLocation()
  const isLoginPage = location.pathname === "/login"

  return (
    <div className="min-h-screen bg-background font-sans antialiased">
      <AnimatedBackground />
      <div className="relative flex min-h-screen flex-col">
        {!isLoginPage && <Header />}
        <main className="flex-1">
          <Routes>
            {/* PUBLIC ROUTES */}
            <Route
              path="/login"
              element={
                <section className="flex flex-col items-center justify-center p-6 w-full">
                  <Login />
                </section>
              }
            />

            {/* PROTECTED ROUTES */}
            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<LandingPage />} />
              <Route
                path="/calculator"
                element={
                  <section className="container mx-auto py-8 md:py-12 lg:py-24">
                    <TariffCalculator />
                  </section>
                }
              />
              <Route
                path="/dashboard"
                element={
                  <section className="container mx-auto py-8 md:py-12 lg:py-24">
                    <Dashboard />
                  </section>
                }
              />
              <Route
                path="/historical"
                element={
                  <section className="container mx-auto py-8 md:py-12 lg:py-24">
                    <HistoricalTariffExplorer />
                  </section>
                }
              />
              <Route
                path="/calc-history"
                element={
                  <section className="container mx-auto py-8 md:py-12 lg:py-24">
                    <CalculationHistory />
                  </section>
                }
              />

              <Route
                path="/chatbot"
                element={
                  <section className="container mx-auto py-8 md:py-12 lg:py-24">
                    <ChatbotPage />
                  </section>
                }
              />

              <Route
                path="/newsletter"
                element={
                  <section className="container mx-auto py-8 md:py-12 lg:py-24">
                    <Newsletter />
                  </section>
                }
              />

              <Route path="/user-management" element={<UserManagement />} />
              <Route path="/profile" element={<Profile />} />
              <Route
                path="/forecast"
                element={
                  <section className="container mx-auto py-8 md:py-12 lg:py-24">
                    <Forecast />
                  </section>
                }
              />
            </Route>
            <Route path="*" element={<Navigate replace to="/" />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  )
}

export default App
