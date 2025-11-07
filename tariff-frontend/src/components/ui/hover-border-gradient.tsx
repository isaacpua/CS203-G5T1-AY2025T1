"use client"
import React, { HTMLAttributes } from "react"

type Props = HTMLAttributes<HTMLElement> & {
  as?: any
  containerClassName?: string
}

export function HoverBorderGradient({ as: Component = "div", className = "", containerClassName = "", children, ...rest }: Props) {
  return (
    <div className={`relative inline-block ${containerClassName}`}>
      {/* gradient border layer */}
      <span className="absolute -inset-px rounded-full bg-gradient-to-r from-emerald-400 via-green-300 to-cyan-400 opacity-80 blur-md transform transition-all duration-300 group-hover:scale-105" aria-hidden="true" />
      {/* inner border mask to create border effect */}
      <span className="absolute inset-0 rounded-full bg-[inherit] mix-blend-multiply" aria-hidden="true" />
      <Component
        {...rest}
        className={`relative z-10 group inline-flex items-center justify-center ${className}`}
      >
        {children}
      </Component>
    </div>
  )
}

export default HoverBorderGradient
