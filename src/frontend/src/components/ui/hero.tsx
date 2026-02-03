"use client"
import { Button } from "@/components/ui/button"
import { GlassCard } from "@/components/ui/glass-card"
import { motion } from "framer-motion"
import { ArrowRight, Sparkles, Scale, ShieldCheck } from "lucide-react"
import { DemoAnimation } from "@/components/ui/demo-animation"
import Link from "next/link"

export function Hero() {
    return (
        <section className="relative overflow-hidden pt-24 pb-16 md:pt-32 md:pb-24">
            <div className="container mx-auto px-4 md:px-6 relative z-10">
                <div className="flex flex-col items-center text-center space-y-8">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5 }}
                    >
                        <span className="inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium bg-secondary text-secondary-foreground mb-4">
                            <Sparkles className="mr-2 h-3 w-3" />
                            Law5 AI: The Next-Gen Legal Interface
                        </span>
                        <h1 className="text-4xl font-extrabold tracking-tight lg:text-6xl max-w-5xl mx-auto">
                            Transforming Data into <br className="hidden md:block" />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-gray-900 via-gray-700 to-gray-500 dark:from-white dark:via-gray-300 dark:to-gray-500">
                                Justice & Clarity
                            </span>
                        </h1>
                        <p className="mt-6 text-lg text-muted-foreground max-w-2xl mx-auto">
                            Law5 AI คือระบบปฏิบัติการกฎหมาย (Legal OS) ที่ช่วยทนายความวิเคราะห์คำพิพากษาศาลฎีกา ระเบียบ และข้อบังคับ เพื่อสร้างความได้เปรียบในเชิงคดีจากข้อมูลที่แม่นยำ
                        </p>
                    </motion.div>

                    <motion.div
                        className="flex flex-col sm:flex-row items-center space-y-3 sm:space-y-0 sm:space-x-4"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.2 }}
                    >
                        <Link href="/chat">
                            <Button size="lg" className="min-w-[180px] text-base group w-full sm:w-auto bg-indigo-600 hover:bg-indigo-700">
                                Start AI Chat
                                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                            </Button>
                        </Link>
                        <Link href="/search">
                            <Button variant="outline" size="lg" className="min-w-[180px] text-base group w-full sm:w-auto border-indigo-200 hover:bg-indigo-50 text-indigo-700">
                                <Scale className="mr-2 h-4 w-4" />
                                Research Tool
                            </Button>
                        </Link>
                    </motion.div>

                    {/* Branding / Trust Badges */}
                    <motion.div
                        className="flex items-center justify-center space-x-8 pt-4 opacity-70"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 0.7 }}
                        transition={{ delay: 0.6 }}
                    >
                        <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                            <Scale className="h-4 w-4" />
                            <span>Thai Law Trained</span>
                        </div>
                        <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                            <ShieldCheck className="h-4 w-4" />
                            <span>PDPA Compliant</span>
                        </div>
                    </motion.div>

                    {/* Hero Visual aka "The Artifact" */}
                    <motion.div
                        className="w-full max-w-5xl mt-16"
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.8, delay: 0.4 }}
                    >
                        <GlassCard className="aspect-[16/9] w-full flex items-center justify-center border-white/20 dark:border-white/10 shadow-2xl relative bg-gradient-to-br from-white/40 to-white/10 dark:from-white/5 dark:to-transparent overflow-hidden">
                            {/* Abstract UI Representation */}
                            <div className="absolute inset-0 bg-grid-slate-200/50 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] dark:bg-grid-slate-800/50" />

                            {/* Mock Interface: Intelligent Drafting */}
                            {/* Animated Demo Interface */}
                            <div className="relative z-10 w-full h-full flex items-center justify-center">
                                <DemoAnimation />
                            </div>
                        </GlassCard>

                        {/* Background Gradient Blurs */}
                        <div className="absolute -top-24 -left-20 w-72 h-72 bg-purple-500/20 rounded-full blur-3xl pointer-events-none mix-blend-multiply dark:mix-blend-normal dark:bg-purple-900/20" />
                        <div className="absolute -bottom-24 -right-20 w-72 h-72 bg-blue-500/20 rounded-full blur-3xl pointer-events-none mix-blend-multiply dark:mix-blend-normal dark:bg-blue-900/20" />
                    </motion.div>
                </div>
            </div>
        </section>
    )
}
