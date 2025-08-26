import TariffCalculator from './components/TariffCalculator';
import { ModeToggle } from './components/mode-toggle';

function App() {
  return (
    <div className="min-h-screen bg-background font-sans antialiased">
      <div className="container relative flex min-h-screen flex-col">
        <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container flex h-14 items-center">
            <div className="mr-4 hidden md:flex">
              <a className="mr-6 flex items-center space-x-2" href="/">
                <span className="hidden font-bold sm:inline-block">
                  TARIFF Project
                </span>
              </a>
            </div>
            <div className="flex flex-1 items-center justify-end space-x-2">
              <ModeToggle />
            </div>
          </div>
        </header>
        <main className="flex-1">
          <div className="container relative">
            <section className="mx-auto flex max-w-[980px] flex-col items-center gap-2 py-8 md:py-12 md:pb-8 lg:py-24 lg:pb-20">
              <TariffCalculator />
            </section>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;