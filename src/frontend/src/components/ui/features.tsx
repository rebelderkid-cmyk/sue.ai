"use client"
import { GlassCard } from "@/components/ui/glass-card"
import { motion } from "framer-motion"
import { FileText, Search, Scale, Clock, Shield, Zap } from "lucide-react"

export function Features() {
    const features = [
        {
            title: "Intelligent Drafting",
            description: "Draft contracts, lawsuits, and case documents from case facts. Instant editing with AI analysis. Reduce time from 2 hrs to 15 mins.",
            icon: FileText,
            stat: "<30s TTD"
        },
        {
            title: "Contextual Search",
            description: "Search by context, not just keywords. Describe case facts in sentences, and AI finds matching Supreme Court decisions.",
            icon: Search,
            stat: "Deep Search"
        },
        {
            title: "Litigation Support",
            description: "Analyze opponent's lawsuits to find counter-arguments and suggest case strategies based on precedents.",
            icon: Scale,
            stat: "Strategic Edge"
        }
    ]

    const metrics = [
        { label: "Drafting Speed", value: "~15m", icon: Clock },
        { label: "Data Privacy", value: "PDPA", icon: Shield },
        { label: "Hallucinations", value: "0%", icon: Zap },
    ]

    return (
        <section id="features" className="py-24 bg-muted/30">
            <div className="container mx-auto px-4 md:px-6">
                <div className="text-center mb-16">
                    <h2 className="text-3xl font-bold tracking-tight md:text-5xl">The Legal Operating System</h2>
                    <p className="mt-4 text-muted-foreground max-w-2xl mx-auto">
                        Sue.Ai solves the critical bottlenecks obstructing justice: Inefficiency, Privacy Risk, and the High Cost of Justice.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {features.map((feature, i) => (
                        <motion.div
                            key={feature.title}
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: i * 0.1 }}
                        >
                            <GlassCard hoverEffect className="h-full flex flex-col items-start">
                                <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center mb-6 text-primary">
                                    <feature.icon className="h-5 w-5" />
                                </div>
                                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                                <p className="text-muted-foreground mb-4 flex-1">{feature.description}</p>
                                <div className="text-xs font-bold bg-secondary px-3 py-1 rounded-full text-secondary-foreground">
                                    {feature.stat}
                                </div>
                            </GlassCard>
                        </motion.div>
                    ))}
                </div>

                <div className="mt-20">
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 lg:gap-8 border-t pt-10">
                        {metrics.map((metric, i) => (
                            <div key={metric.label} className="flex flex-col items-center text-center">
                                <metric.icon className="h-6 w-6 text-muted-foreground mb-2" />
                                <div className="text-2xl md:text-3xl font-bold">{metric.value}</div>
                                <div className="text-sm text-muted-foreground">{metric.label}</div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </section>
    )
}
