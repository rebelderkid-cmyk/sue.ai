"use client"
import * as React from "react"
import { cn } from "@/lib/utils"
import { motion, HTMLMotionProps } from "framer-motion"

interface GlassCardProps extends HTMLMotionProps<"div"> {
    hoverEffect?: boolean
}

const GlassCard = React.forwardRef<HTMLDivElement, GlassCardProps>(
    ({ className, children, hoverEffect = false, ...props }, ref) => {
        return (
            <motion.div
                ref={ref}
                className={cn(
                    "glass rounded-xl p-6 transition-all duration-300",
                    hoverEffect && "hover:shadow-xl hover:border-white/40 dark:hover:border-white/20",
                    className
                )}
                initial={hoverEffect ? { opacity: 0, y: 20 } : undefined}
                whileInView={hoverEffect ? { opacity: 1, y: 0 } : undefined}
                viewport={{ once: true }}
                {...props}
            >
                {children}
            </motion.div>
        )
    }
)
GlassCard.displayName = "GlassCard"

export { GlassCard }
