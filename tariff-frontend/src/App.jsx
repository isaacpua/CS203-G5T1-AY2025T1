import { useState } from "react";
import { ThemeProvider } from "./components/theme-provider";
import { ModeToggle } from "./components/mode-toggle";
import TariffCalculator from "./components/TariffCalculator";
import HistoricalTariffExplorer from "./components/HistoricalTariffExplorer";

function App() {
  const [tab, setTab] = useState("search"); // 'search' | 'historical'

  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <div className="min-h-screen bg-background text-foreground">
        {/* Header */}
        <header className="flex items-center justify-between px-4 py-3 border-b">
          <div className="text-xs tracking-wider uppercase opacity-70">
            TARIFF Project
          </div>
          <ModeToggle />
        </header>

        {/* Tabs */}
        <div className="px-4 py-3 border-b">
          <div className="inline-flex rounded-xl bg-muted p-1">
            <button
              className={`px-4 py-2 rounded-lg text-sm transition ${
                tab === "search"
                  ? "bg-background shadow"
                  : "opacity-70 hover:opacity-100"
              }`}
              onClick={() => setTab("search")}
            >
              Search & Compute
            </button>
            <button
              className={`px-4 py-2 rounded-lg text-sm transition ${
                tab === "historical"
                  ? "bg-background shadow"
                  : "opacity-70 hover:opacity-100"
              }`}
              onClick={() => setTab("historical")}
            >
              Historical Explorer
            </button>
          </div>
        </div>

        {/* Content */}
        <main className="max-w-6xl mx-auto p-4 grid gap-6">
          {tab === "search" ? (
            <TariffCalculator />
          ) : (
            <HistoricalTariffExplorer />
          )}
        </main>
      </div>
    </ThemeProvider>
  );
}

export default App;
