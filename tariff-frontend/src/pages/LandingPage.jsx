import { Button } from "@/components/ui/button"
import { Calculator, Wheat, Menu, BarChart3, TrendingUp, History } from "lucide-react"
import { useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { useState, useEffect } from "react"
import { CardBody, CardContainer, CardItem } from "@/components/ui/3d-card"

export default function LandingPage() {
  const navigate = useNavigate()
  const [contentVisible, setContentVisible] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      setContentVisible(true)
    }, 500)
    return () => clearTimeout(timer)
  }, [])

  const handleOpen = (path) => {
    navigate(path)
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-transparent">
      <div className="fixed inset-0 z-0 pointer-events-none">
        <video
          autoPlay
          loop
          muted
          playsInline
          className={`absolute inset-0 w-full h-full object-cover transition-all duration-1000 ${contentVisible ? "blur-sm scale-105" : "blur-0 scale-100"
            }`}
        >
          <source
            src="/Barn_Animation.mp4"
            type="video/mp4"
          />
        </video>
        <div
          className={`absolute inset-0 bg-black/40 transition-opacity duration-1000 ${contentVisible ? "opacity-60" : "opacity-30"
            }`}
        />
      </div>

      <section className="relative z-10 py-20 lg:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <motion.h1
              className="text-4xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight text-white drop-shadow-2xl"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.1 }}
            >
              <span className="text-white">Calculate Tariffs</span>
              <br />
              <span className="text-primary drop-shadow-lg">Anytime, Anywhere</span>
            </motion.h1>

            <motion.p
              className="text-xl text-white/95 mb-10 max-w-3xl mx-auto leading-relaxed drop-shadow-lg backdrop-blur-sm bg-black/20 rounded-lg p-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.2 }}
            >
              Streamline your international agricultural trade with instant, accurate tariff calculations. Get real-time
              rates, compliance insights, and detailed cost analysis for seamless global commerce.
            </motion.p>

            {/* Hero action buttons removed per request */}

            <motion.div
              className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 max-w-6xl mx-auto"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
            >
              <motion.div whileHover={{ y: -6 }} className="w-full">
                <CardContainer className="w-full">
                  <CardBody className="bg-white/95 dark:bg-card/90 backdrop-blur-md border border-white/50 dark:border-white/20 shadow-2xl hover:shadow-3xl transition-all duration-300 flex flex-col items-stretch p-6 rounded-2xl min-h-120">
                    <CardItem translateZ={80} className="flex items-center justify-center mb-4">
                      <BarChart3 className="w-12 h-12 text-primary" />
                    </CardItem>
                    <CardItem translateZ={60} className="font-semibold text-2xl mb-2 text-foreground dark:text-white text-center">Live Dashboard</CardItem>
                    <CardItem as="p" translateZ={40} className="text-sm text-muted-foreground dark:text-neutral-300 text-center mb-4">See a quick snapshot of your tariffs, trends, and key metrics.</CardItem>
                    <div className="flex gap-3 mt-auto">
                      <CardItem translateZ={20} className="w-full text-left">
                        <Button
                          size="lg"
                          className="w-full bg-primary hover:bg-primary/90 text-primary-foreground"
                          onClick={() => handleOpen('/dashboard')}
                        >
                          Open Dashboard
                        </Button>
                      </CardItem>
                    </div>
                  </CardBody>
                </CardContainer>
              </motion.div>

              <motion.div whileHover={{ y: -6 }} className="w-full" transition={{ delay: 0.06 }}>
                <CardContainer className="w-full">
                  <CardBody className="bg-white/95 dark:bg-card/90 backdrop-blur-md border border-white/50 dark:border-white/20 shadow-2xl hover:shadow-3xl transition-all duration-300 flex flex-col items-stretch p-6 rounded-2xl min-h-120">
                    <CardItem translateZ={80} className="flex items-center justify-center mb-4">
                      <TrendingUp className="w-12 h-12 text-primary" />
                    </CardItem>
                    <CardItem translateZ={60} className="font-semibold text-2xl mb-2 text-foreground dark:text-white text-center">Newsletter</CardItem>
                    <CardItem as="p" translateZ={40} className="text-sm text-muted-foreground dark:text-neutral-300 text-center mb-4">Subscribe for weekly tariff insights and export opportunities.</CardItem>
                    <div className="flex gap-3 mt-auto">
                      <CardItem translateZ={20} className="w-full text-left">
                        <Button
                          size="lg"
                          className="w-full bg-primary hover:bg-primary/90 text-primary-foreground"
                          onClick={() => handleOpen('/newsletter')}
                        >
                          Go to Newsletter
                        </Button>
                      </CardItem>
                    </div>
                  </CardBody>
                </CardContainer>
              </motion.div>

              <motion.div whileHover={{ y: -6 }} className="w-full" transition={{ delay: 0.12 }}>
                <CardContainer className="w-full">
                  <CardBody className="bg-white/95 dark:bg-card/90 backdrop-blur-md border border-white/50 dark:border-white/20 shadow-2xl hover:shadow-3xl transition-all duration-300 flex flex-col items-stretch p-6 rounded-2xl min-h-120">
                    <CardItem translateZ={80} className="flex items-center justify-center mb-4">
                      <Calculator className="w-12 h-12 text-primary" />
                    </CardItem>
                    <CardItem translateZ={60} className="font-semibold text-2xl mb-2 text-foreground dark:text-white text-center">MCP Assistant</CardItem>
                    <CardItem as="p" translateZ={40} className="text-sm text-muted-foreground dark:text-neutral-300 text-center mb-4">Chat with the assistant for tariff guidance, policy checks and automation.</CardItem>
                    <div className="flex gap-3 mt-auto">
                      <CardItem translateZ={20} className="w-full text-left">
                        <Button
                          size="lg"
                          className="w-full bg-primary hover:bg-primary/90 text-primary-foreground"
                          onClick={() => handleOpen('/chat')}
                        >
                          Open Assistant
                        </Button>
                      </CardItem>
                    </div>
                  </CardBody>
                </CardContainer>
              </motion.div>
            </motion.div>

            {/* Previews removed per request */}
          </div>
        </div>
      </section>
    </div>
  )
}
