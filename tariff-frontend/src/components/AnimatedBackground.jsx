"use client"

import { motion } from "framer-motion"

export default function AnimatedBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      {/* Subtle gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-secondary/5 to-accent/5" />

      {/* Animated farm elements */}
      <motion.div
        className="absolute top-20 left-10 text-6xl opacity-20"
        animate={{
          y: [0, -15, 0],
          x: [0, 10, 0],
          rotate: [0, 5, 0],
        }}
        transition={{
          duration: 6,
          repeat: Number.POSITIVE_INFINITY,
          ease: "easeInOut",
        }}
      >
        🌾
      </motion.div>

      <motion.div
        className="absolute top-40 right-20 text-5xl opacity-15"
        animate={{
          y: [0, -20, 0],
          rotate: [0, -5, 0],
        }}
        transition={{
          duration: 5,
          repeat: Number.POSITIVE_INFINITY,
          ease: "easeInOut",
          delay: 0.5,
        }}
      >
        🌻
      </motion.div>

      <motion.div
        className="absolute bottom-32 left-1/4 text-4xl opacity-20"
        animate={{
          y: [0, -10, 0],
          x: [0, 15, 0],
        }}
        transition={{
          duration: 7,
          repeat: Number.POSITIVE_INFINITY,
          ease: "easeInOut",
          delay: 1,
        }}
      >
        🥚
      </motion.div>

      <motion.div
        className="absolute top-1/3 right-1/4 text-5xl opacity-15"
        animate={{
          y: [0, -18, 0],
          rotate: [0, 3, 0],
        }}
        transition={{
          duration: 6.5,
          repeat: Number.POSITIVE_INFINITY,
          ease: "easeInOut",
          delay: 1.5,
        }}
      >
        🌽
      </motion.div>

      <motion.div
        className="absolute bottom-20 right-32 text-4xl opacity-20"
        animate={{
          y: [0, -12, 0],
          x: [0, -10, 0],
        }}
        transition={{
          duration: 5.5,
          repeat: Number.POSITIVE_INFINITY,
          ease: "easeInOut",
          delay: 2,
        }}
      >
        🐔
      </motion.div>

      <motion.div
        className="absolute top-1/2 left-16 text-5xl opacity-15"
        animate={{
          scale: [1, 1.05, 1],
          rotate: [0, -3, 0],
        }}
        transition={{
          duration: 4,
          repeat: Number.POSITIVE_INFINITY,
          ease: "easeInOut",
          delay: 0.8,
        }}
      >
        🌱
      </motion.div>

      <motion.div
        className="absolute bottom-1/3 right-1/3 text-4xl opacity-20"
        animate={{
          y: [0, -15, 0],
          rotate: [0, 5, 0],
        }}
        transition={{
          duration: 6.2,
          repeat: Number.POSITIVE_INFINITY,
          ease: "easeInOut",
          delay: 1.2,
        }}
      >
        🏡
      </motion.div>

      <motion.div
        className="absolute top-2/3 left-1/3 text-3xl opacity-15"
        animate={{
          y: [0, -8, 0],
          x: [0, 12, 0],
        }}
        transition={{
          duration: 5.8,
          repeat: Number.POSITIVE_INFINITY,
          ease: "easeInOut",
          delay: 2.5,
        }}
      >
        🌿
      </motion.div>
    </div>
  )
}
