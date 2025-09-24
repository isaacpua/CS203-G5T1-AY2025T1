import React from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Calculator } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function LandingPage() {
  const navigate = useNavigate();

  const ToCalculatorButton = () => {
    return (
      <Button
        size="lg"
        className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-lg px-8 py-6 shadow-lg hover:shadow-xl transition-all duration-300"
        onClick={() => navigate("/calculator", { replace: true })}
      >
        Start Calculating Now
        <Calculator className="ml-2 h-5 w-5" />
      </Button>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-900 dark:via-slate-800 dark:to-indigo-950">

      <section className="relative py-20 lg:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <Badge className="mb-6 bg-blue-100 text-blue-700 hover:bg-blue-200 px-4 py-2 dark:bg-blue-900 dark:text-blue-300 dark:hover:bg-blue-800">
              ✨ Trusted by 50,000+ global traders
            </Badge>
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold text-gray-900 dark:text-gray-100 mb-6 leading-tight">
              <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                Calculate Tariffs
              </span>
              <br />
              <span className="text-gray-800 dark:text-gray-200">Anytime, Anywhere</span>
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-300 mb-10 max-w-3xl mx-auto leading-relaxed">
              Streamline your international trade with instant, accurate tariff calculations.
              Get real-time rates, compliance insights, and detailed cost analysis for seamless global commerce.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <ToCalculatorButton />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
