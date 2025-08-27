import TariffCalculator from './components/TariffCalculator';
import { ModeToggle } from './components/mode-toggle';

function App() {
  return (
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
          <section className="mx-auto flex max-w-[980px] flex-col items-center gap-2 py-8 md:py-12 md:pb-8 lg:py-24 lg:pb-20">
            <TariffCalculator />
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;