"use client"

import { motion, useInView, useAnimation, Variant } from "framer-motion"
import { useRef, useEffect } from "react"
import { cn } from "@/lib/utils"

interface ScrollRevealProps {
    children: React.ReactNode
    className?: string
    width?: "fit-content" | "100%"
    delay?: number
    direction?: "up" | "down" | "left" | "right"
    duration?: number
    distance?: number
    threshold?: number
    once?: boolean
}

export const ScrollReveal = ({
    children,
    className,
    width = "fit-content",
    delay = 0,
    direction = "up",
    duration = 0.5,
    distance = 30,
    threshold = 0.2,
    once = true,
}: ScrollRevealProps) => {
    const ref = useRef(null)
    const isInView = useInView(ref, { once, amount: threshold })
    const controls = useAnimation()

    useEffect(() => {
        if (isInView) {
            controls.start("visible")
        } else if (!once) {
            controls.start("hidden")
        }
    }, [isInView, controls, once])

    const getDirectionOffset = () => {
        switch (direction) {
            case "up": return { y: distance }
            case "down": return { y: -distance }
            case "left": return { x: distance }
            case "right": return { x: -distance }
            default: return { y: distance }
        }
    }

    const variants = {
        hidden: { opacity: 0, ...getDirectionOffset() },
        visible: {
            opacity: 1,
            x: 0,
            y: 0,
            transition: {
                duration,
                delay,
                ease: [0.25, 0.25, 0, 1] // Custom ease curve for elegance
            }
        },
    }

    return (
        <div ref={ref} style={{ width, overflow: "hidden" }}>
            <motion.div
                variants={variants}
                initial="hidden"
                animate={controls}
                className={className}
            >
                {children}
            </motion.div>
        </div>
    )
}

export const StaggerContainer = ({
    children,
    className,
    delay = 0,
    staggerDelay = 0.1,
}: {
    children: React.ReactNode
    className?: string
    delay?: number
    staggerDelay?: number
}) => {
    const ref = useRef(null)
    const isInView = useInView(ref, { once: true, amount: 0.2 })
    const controls = useAnimation()

    useEffect(() => {
        if (isInView) {
            controls.start("visible")
        }
    }, [isInView, controls])

    const containerVariants = {
        hidden: {},
        visible: {
            transition: {
                staggerChildren: staggerDelay,
                delayChildren: delay,
            },
        },
    }

    return (
        <motion.div
            ref={ref}
            variants={containerVariants}
            initial="hidden"
            animate={controls}
            className={className}
        >
            {children}
        </motion.div>
    )
}

export const StaggerItem = ({ children, className }: { children: React.ReactNode, className?: string }) => {
    const itemVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: {
            opacity: 1,
            y: 0,
            transition: { duration: 0.5, ease: "easeOut" }
        },
    }

    return (
        <motion.div variants={itemVariants} className={className}>
            {children}
        </motion.div>
    )
}
