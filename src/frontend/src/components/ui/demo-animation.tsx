"use client"
import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Loader2, ShieldCheck, FileText, MousePointer2, Lock, Sparkles, Zap, BrainCircuit } from "lucide-react"
import { cn } from "@/lib/utils"

export function DemoAnimation() {
    const [step, setStep] = React.useState<"idle" | "typing" | "processing" | "options" | "selecting" | "generating" | "reviewing" | "verified">("idle")
    const [text, setText] = React.useState("")

    const fullText = "Draft a partnership agreement..."

    React.useEffect(() => {
        let timeout: NodeJS.Timeout

        const runSequence = async () => {
            // 1. Reset
            setStep("idle")
            setText("")
            await new Promise(r => setTimeout(r, 1000))

            // 2. Typing Phase
            setStep("typing")
            for (let i = 0; i <= fullText.length; i++) {
                setText(fullText.slice(0, i))
                await new Promise(r => setTimeout(r, 40))
            }
            await new Promise(r => setTimeout(r, 400))

            // 3. Processing (Thinking)
            setStep("processing")
            await new Promise(r => setTimeout(r, 1800))

            // 4. Show Strategy Options
            setStep("options")
            await new Promise(r => setTimeout(r, 2000))

            // 5. Simulating Selection
            setStep("selecting")
            await new Promise(r => setTimeout(r, 800))

            // 6. Generating (Top of Doc)
            setStep("generating")
            await new Promise(r => setTimeout(r, 1200))

            // 7. Reviewing (Scrolling Down)
            setStep("reviewing")
            await new Promise(r => setTimeout(r, 1800))

            // 8. Security Verified
            setStep("verified")

            // Loop
            timeout = setTimeout(runSequence, 6000)
        }

        runSequence()

        return () => clearTimeout(timeout)
    }, [])

    return (
        <div className="w-full h-full flex flex-col items-center justify-center p-4">
            {/* Main Container - Pure Light Aesthetic */}
            <div className="w-full max-w-lg bg-white backdrop-blur-xl rounded-2xl border border-gray-200 shadow-2xl overflow-hidden flex flex-col relative ring-1 ring-black/5">

                {/* Header - Minimalist Light */}
                <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 bg-gray-50/50">
                    <div className="flex gap-1.5 opacity-60 hover:opacity-100 transition-opacity">
                        <div className="w-2.5 h-2.5 rounded-full bg-red-400" />
                        <div className="w-2.5 h-2.5 rounded-full bg-yellow-400" />
                        <div className="w-2.5 h-2.5 rounded-full bg-green-400" />
                    </div>
                    <div className="ml-auto flex items-center gap-1.5 text-[10px] font-medium text-gray-400 uppercase tracking-wider">
                        <ShieldCheck className="w-3 h-3" />
                        Sue.Ai <span className="opacity-50">|</span> Secure Enclave
                    </div>
                </div>

                {/* Content Area */}
                <div className="p-6 space-y-5 min-h-[380px] flex flex-col relative bg-white">

                    {/* Input Area: "The Prompt" */}
                    <div className="relative z-20 flex-shrink-0">
                        <div className="relative group">
                            <div className={cn(
                                "w-full min-h-[52px] rounded-xl border pl-4 pr-32 py-3 text-sm shadow-sm transition-all duration-300 flex items-center relative overflow-hidden",
                                "bg-white border-gray-200",
                                step === "typing" || step === "processing" ? "ring-2 ring-blue-500/10 border-blue-500/30" : "hover:border-gray-300"
                            )}>
                                <span className="z-10 relative bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600 font-medium">
                                    {text}
                                </span>
                                {step === "typing" && (
                                    <motion.span
                                        animate={{ opacity: [1, 0] }}
                                        transition={{ repeat: Infinity, duration: 0.8 }}
                                        className="inline-block w-0.5 h-4 ml-0.5 bg-blue-600 z-10 relative"
                                    />
                                )}

                                {/* Integrated Action Button - Minimal Light Version */}
                                <div className="absolute right-1.5 top-1.5 bottom-1.5 z-20">
                                    <motion.button
                                        disabled
                                        className={cn(
                                            "h-full px-4 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 shadow-sm border",
                                            "bg-white text-gray-900 border-gray-200 hover:bg-gray-50 hover:border-gray-300"
                                        )}
                                        animate={step === "processing" ? { scale: 0.95, opacity: 0.9 } : { scale: 1, opacity: 1 }}
                                    >
                                        {step === "processing" ? (
                                            <>
                                                <Loader2 className="h-3.5 w-3.5 animate-spin text-gray-400" />
                                                <span className="text-gray-500">Thinking</span>
                                            </>
                                        ) : (
                                            <>
                                                <Sparkles className="h-3.5 w-3.5 text-blue-600" />
                                                <span>Draft</span>
                                            </>
                                        )}
                                    </motion.button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Dynamic Stage Area */}
                    <div className="relative flex-1 rounded-xl bg-gray-50/50 border border-dash border-gray-100 overflow-hidden flex flex-col items-center justify-center">

                        {/* 1. Idle / Empty State */}
                        {(step === "idle" || step === "typing") && (
                            <div className="text-center space-y-3 opacity-40">
                                <div className="w-12 h-12 rounded-2xl bg-white border border-gray-200 shadow-sm mx-auto flex items-center justify-center">
                                    <BrainCircuit className="w-6 h-6 text-gray-400" />
                                </div>
                                <p className="text-xs font-medium text-gray-500">Awaiting Case Facts</p>
                            </div>
                        )}

                        {/* 2. Processing: "The Brain" */}
                        <AnimatePresence>
                            {step === "processing" && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    className="absolute inset-0 flex flex-col items-center justify-center bg-white/80 backdrop-blur-sm z-10"
                                >
                                    <div className="relative w-16 h-16 mb-4">
                                        <div className="absolute inset-0 rounded-full border-2 border-blue-500/20 animate-ping-slow" />
                                        <div className="absolute inset-0 rounded-full border-2 border-blue-500/20 animate-ping-slower delay-300" />
                                        <div className="absolute inset-0 flex items-center justify-center">
                                            <Zap className="w-6 h-6 text-blue-500 animate-pulse" />
                                        </div>
                                    </div>
                                    <div className="text-xs font-medium text-gray-500 animate-pulse">
                                        Synthesizing 10,000+ Precedents...
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* 3. Strategy Selection: "The Choice" */}
                        <AnimatePresence>
                            {(step === "options" || step === "selecting") && (
                                <motion.div className="flex gap-3 w-full h-full p-4 items-center justify-center">
                                    {/* Option A (Standard) */}
                                    <motion.div
                                        initial={{ opacity: 0, scale: 0.9, x: -10 }}
                                        animate={{ opacity: 1, scale: 1, x: 0 }}
                                        exit={{ opacity: 0, scale: 0.9 }}
                                        className="flex-1 h-full max-h-[220px] bg-white rounded-lg border border-gray-200 p-3 shadow-sm flex flex-col relative opacity-50 grayscale transition-all"
                                    >
                                        <div className="text-[10px] uppercase font-bold text-gray-400 tracking-wider mb-1">Standard</div>
                                        <div className="font-semibold text-sm mb-2 text-gray-900">Balanced</div>
                                        <div className="space-y-1.5 flex-1 opacity-60">
                                            <div className="h-1.5 w-full bg-gray-100 rounded-full" />
                                            <div className="h-1.5 w-3/4 bg-gray-100 rounded-full" />
                                        </div>
                                    </motion.div>

                                    {/* Option B (Premium/Smart) */}
                                    <motion.div
                                        initial={{ opacity: 0, scale: 0.9, x: 10 }}
                                        animate={{ opacity: 1, scale: 1, x: 0 }}
                                        exit={{ opacity: 0, scale: 1.05 }}
                                        layoutId="selected-card"
                                        className="flex-1 h-full max-h-[220px] bg-white rounded-lg border-2 border-blue-600 ring-4 ring-blue-50 p-3 shadow-xl flex flex-col relative z-20"
                                    >
                                        <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-sm whitespace-nowrap">
                                            AI Recommended
                                        </div>
                                        <div className="text-[10px] uppercase font-bold text-blue-600 tracking-wider mb-1 mt-1">Strategic</div>
                                        <div className="font-semibold text-sm mb-2 text-gray-900">Pro-Founder</div>

                                        <div className="space-y-2 mb-2">
                                            <div className="flex justify-between text-[10px] border-b border-gray-100 pb-1 border-dashed">
                                                <span className="text-gray-500">Equity</span>
                                                <span className="font-mono font-medium text-gray-900">60%</span>
                                            </div>
                                            <div className="flex justify-between text-[10px] border-b border-gray-100 pb-1 border-dashed">
                                                <span className="text-gray-500">Control</span>
                                                <span className="font-mono font-medium text-gray-900">Super-Voting</span>
                                            </div>
                                            <div className="flex justify-between text-[10px] border-b border-gray-100 pb-1 border-dashed">
                                                <span className="text-gray-500">Vesting</span>
                                                <span className="font-mono font-medium text-gray-900">None</span>
                                            </div>
                                        </div>

                                        {/* Pointer Cursor */}
                                        {step === "selecting" && (
                                            <motion.div
                                                initial={{ opacity: 0, x: 40, y: 40 }}
                                                animate={{ opacity: 1, x: 10, y: 10 }}
                                                className="absolute bottom-2 right-2 z-30 drop-shadow-xl"
                                            >
                                                <MousePointer2 className="h-5 w-5 fill-black text-white" />
                                            </motion.div>
                                        )}
                                    </motion.div>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* 4. Drafting & Review: "The Result" */}
                        <AnimatePresence>
                            {(step === "generating" || step === "reviewing" || step === "verified") && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="absolute inset-0 bg-white flex flex-col"
                                >
                                    {/* Document Toolbar */}
                                    <div className="flex items-center justify-between px-3 py-2 border-b border-gray-100 bg-gray-50/50">
                                        <div className="flex items-center gap-2">
                                            <FileText className="w-3.5 h-3.5 text-blue-600" />
                                            <span className="text-xs font-semibold text-gray-700">Partnership_Agreement_v1.pdf</span>
                                        </div>
                                        <div className="text-[10px] text-gray-400">Auto-saved</div>
                                    </div>

                                    {/* Review Content */}
                                    <div className="flex-1 overflow-hidden relative p-4">
                                        <motion.div
                                            className="font-mono text-[10px] leading-relaxed text-gray-600 max-w-[90%] mx-auto"
                                            animate={step === "reviewing" || step === "verified" ? { y: -80 } : { y: 0 }}
                                            transition={{ duration: 2.5, ease: "easeInOut" }}
                                        >
                                            <div className="mb-4 text-center">
                                                <p className="font-serif text-sm font-bold text-gray-900 mb-1">SHAREHOLDERS AGREEMENT</p>
                                                <div className="h-px w-20 bg-gray-200 mx-auto" />
                                            </div>

                                            <p className="mb-3 text-justify">
                                                THIS AGREEMENT is made on <span className="bg-yellow-50 text-yellow-700 px-1 rounded border border-yellow-200 font-medium">[ DATE ]</span>
                                                BETWEEN <span className="bg-blue-50 text-blue-700 px-1 rounded border border-blue-200 font-medium">[ FOUNDER ]</span>
                                                AND <span className="bg-blue-50 text-blue-700 px-1 rounded border border-blue-200 font-medium">[ INVESTOR ]</span>.
                                            </p>

                                            <div className="space-y-3 pl-2 border-l-2 border-gray-200">
                                                <div>
                                                    <p className="font-bold text-xs mb-0.5 text-gray-900">1.2 Equity Structure</p>
                                                    <p>The Founder shall retain <span className="font-bold border-b border-blue-300 text-blue-600">60% ownership</span> of the fully diluted capitalization table.</p>
                                                </div>
                                                <div>
                                                    <p className="font-bold text-xs mb-0.5 text-gray-900">1.3 Board Control</p>
                                                    <p>The Founder is entitled to appoint <span className="font-bold border-b border-blue-300 text-blue-600">2 of 3</span> Board seats.</p>
                                                </div>
                                                <div className="opacity-50 blur-[0.5px]">
                                                    <p className="font-bold text-xs mb-0.5">1.4 Transfer Restrictions</p>
                                                    <p>No securities may be transferred without prior written consent...</p>
                                                </div>
                                            </div>
                                        </motion.div>

                                        {/* Verified Overlay - Clean Light Version */}
                                        <AnimatePresence>
                                            {step === "verified" && (
                                                <motion.div
                                                    initial={{ opacity: 0, scale: 0.95 }}
                                                    animate={{ opacity: 1, scale: 1 }}
                                                    transition={{ type: "spring", bounce: 0.4 }}
                                                    className="absolute inset-x-4 bottom-4"
                                                >
                                                    <div className="bg-white/90 backdrop-blur-md border border-emerald-200 text-emerald-800 p-3 rounded-xl shadow-xl flex items-center justify-between ring-1 ring-emerald-500/20">
                                                        <div className="flex items-center gap-2.5">
                                                            <div className="p-1.5 bg-emerald-100 rounded-lg text-emerald-600 shadow-sm">
                                                                <Lock className="w-3.5 h-3.5" />
                                                            </div>
                                                            <div className="flex flex-col">
                                                                <span className="text-xs font-bold text-emerald-700">Verified Secure</span>
                                                                <span className="text-[9px] font-medium opacity-70">PDPA Compliant • Self-Hosted</span>
                                                            </div>
                                                        </div>
                                                        <div className="flex min-h-[20px] items-center px-1.5 bg-emerald-50 rounded border border-emerald-100">
                                                            <span className="text-[9px] font-mono font-bold text-emerald-700">100% Valid</span>
                                                        </div>
                                                    </div>
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>

                    </div>
                </div>
            </div>
        </div>
    )
}
