import React, { HTMLAttributes, useRef } from "react";

type CardItemProps = HTMLAttributes<HTMLElement> & {
  translateZ?: number | string
  as?: any
}

export function CardContainer({ children, className = "", ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`perspective-root ${className}`} {...rest} />
  )
}

export function CardBody({ children, className = "", ...rest }: HTMLAttributes<HTMLDivElement>) {
  const ref = useRef<HTMLDivElement | null>(null)

  function onMove(e: React.MouseEvent) {
    const el = ref.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const px = (x / rect.width) - 0.5
    const py = (y / rect.height) - 0.5
    // set CSS vars
    el.style.setProperty("--px", String(px))
    el.style.setProperty("--py", String(py))
  }

  function onLeave() {
    const el = ref.current
    if (!el) return
    el.style.setProperty("--px", "0")
    el.style.setProperty("--py", "0")
  }

  return (
    <div
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      className={`card-3d ${className}`}
      {...rest}
    >
      {children}
    </div>
  )
}

export function CardItem({ translateZ = 0, as: Component = "div", style, className = "", ...rest }: CardItemProps) {
  const tz = typeof translateZ === "number" ? `${translateZ}px` : String(translateZ)
  const itemStyle = { ...style, transform: `translateZ(${tz})` }
  return (
    <Component className={`card-item ${className}`} style={itemStyle} {...rest} />
  )
}

export default CardContainer

/* CSS (to be put in a global stylesheet or imported) - but we'll keep classes simple and rely on tailwind utilities in markup.

.perspective-root { perspective: 1200px; }
.card-3d { transform-style: preserve-3d; transition: transform 0.25s ease, box-shadow 0.25s ease; }
.card-3d:hover { transform: rotateX(calc(var(--py) * 6deg)) rotateY(calc(var(--px) * -6deg)); }
.card-item { transform-style: preserve-3d; }
*/
