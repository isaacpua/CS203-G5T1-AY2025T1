import TariffCalculator from './pages/TariffCalculator';
import { ModeToggle } from './components/mode-toggle';
import HelloWorld from './components/HelloWorld';
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from './pages/Login';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background font-sans antialiased">
        <div className="relative flex min-h-screen flex-col">
          <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="flex h-14 items-center justify-between px-4">
              <a className="flex items-center space-x-2" href="/">
                <span className="font-bold">
                  TARIFF Project
                </span>
              </a>
              <ModeToggle />
            </div>
          </header>
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<ProtectedRoute><HelloWorld /></ProtectedRoute>} />
              <Route path="/calculator"
                element={
                  <section className="mx-auto flex max-w-[980px] flex-col items-center gap-2 py-8 md:py-12 md:pb-8 lg:py-24 lg:pb-20">
                    <ProtectedRoute><TariffCalculator /></ProtectedRoute>
                  </section>
                }
              />
              <Route path="/login" element={
                <section className="flex flex-col items-center justify-center p-6 w-full">
                  <Login />
                </section>}
              />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
