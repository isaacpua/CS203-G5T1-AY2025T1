import { Button } from "@/components/ui/button"
import { motion } from "framer-motion"
import { CardBody, CardContainer, CardItem } from "@/components/ui/3d-card"

// Define and export the variants for the card
export const cardVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { 
      duration: 0.5 
    } 
  }
};

/**
 * A reusable 3D feature card for the landing page.
 * @param {object} props
 * @param {React.ElementType} props.Icon - The icon component to display (e.g., BarChart3).
 * @param {string} props.title - The title for the card.
 * @param {string} props.description - The description text.
 * @param {string} props.buttonText - The text for the call-to-action button.
 * @param {() => void} props.onButtonClick - The function to call when the button is clicked.
 */
export default function FeatureCard({ 
  Icon, 
  title, 
  description, 
  buttonText, 
  onButtonClick 
}) {
  return (
    <motion.div variants={cardVariants} whileHover={{ y: -6 }} className="w-full">
      <CardContainer className="w-full">
        <CardBody className="bg-white/95 dark:bg-card/90 backdrop-blur-md border border-white/50 dark:border-white/20 shadow-2xl hover:shadow-3xl transition-all duration-300 flex flex-col items-stretch p-6 rounded-2xl min-h-120">
          <CardItem translateZ={80} className="flex items-center justify-center mb-4">
            <Icon className="w-12 h-12 text-primary" />
          </CardItem>
          <CardItem translateZ={60} className="font-semibold text-2xl mb-2 text-foreground dark:text-white text-center">
            {title}
          </CardItem>
          <CardItem as="p" translateZ={40} className="text-sm text-muted-foreground dark:text-neutral-300 text-center mb-4">
            {description}
          </CardItem>
          <div className="flex gap-3 mt-auto">
            <CardItem translateZ={20} className="w-full text-left">
              <Button
                size="lg"
                className="w-full bg-primary hover:bg-primary/90 text-primary-foreground"
                onClick={onButtonClick}
              >
                {buttonText}
              </Button>
            </CardItem>
          </div>
        </CardBody>
      </CardContainer>
    </motion.div>
  )
}
