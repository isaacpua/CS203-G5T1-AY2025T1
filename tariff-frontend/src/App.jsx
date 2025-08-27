import TariffCalculator from './components/TariffCalculator';
import { ModeToggle } from './components/mode-toggle';

function App() {
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-16 items-center justify-between px-4 md:px-6 lg:px-8">
          <span className="font-bold text-xl">
            TARIFF Project
          </span>
          <ModeToggle />
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center p-4 md:p-6 lg:p-8">
        <TariffCalculator />
      </main>
    </div>
  );
}

export default App;
