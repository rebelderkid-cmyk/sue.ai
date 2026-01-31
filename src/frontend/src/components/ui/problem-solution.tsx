"use client"
import { motion } from "framer-motion"
import { Clock, ShieldAlert, Banknote, Zap, Lock, TrendingDown, ArrowRight } from "lucide-react"

const problems = [
    {
        icon: Clock,
        title: "Time Drain",
        stat: "2+ Hours",
        description: "Spent drafting a single contract. Manual research through scattered databases eats your billable hours.",
        pain: "Lost Revenue"
    },
    {
        icon: ShieldAlert,
        title: "Privacy Risk",
        stat: "100%",
        description: "Client data exposed to third-party AI servers. One breach destroys decades of reputation.",
        pain: "Career Liability"
    },
    {
        icon: Banknote,
        title: "High Cost",
        stat: "10,000+ THB",
        description: "Per Westlaw/LexisNexis seat. Premium tools priced for Big Law, not solo practitioners.",
        pain: "Margin Killer"
    }
]

const solutions = [
    {
        icon: Zap,
        title: "15-Minute Drafts",
        stat: "8x Faster",
        description: "From case facts to court-ready document. AI that understands Thai law precedents.",
        benefit: "More Cases, More Revenue"
    },
    {
        icon: Lock,
        title: "Self-Hosted LLM",
        stat: "0% Exposure",
        description: "Your data never leaves your network. PDPA compliant by architecture, not policy.",
        benefit: "Sleep Peacefully"
    },
    {
        icon: TrendingDown,
        title: "Accessible Pricing",
        stat: "90% Less",
        description: "Enterprise-grade legal AI at a fraction of the cost. Built for every lawyer.",
        benefit: "Higher Margins"
    }
]

export function ProblemSolution() {
    return (
        <section id="problem-solution" className="py-24 bg-white relative overflow-hidden">
            {/* Background Decoration */}
            <div className="absolute inset-0 pointer-events-none">
                <div className="absolute top-1/4 -left-20 w-80 h-80 bg-red-100/50 rounded-full blur-3xl" />
                <div className="absolute bottom-1/4 -right-20 w-80 h-80 bg-emerald-100/50 rounded-full blur-3xl" />
            </div>

            <div className="container mx-auto px-4 md:px-6 relative z-10">

                {/* Section Header */}
                <div className="text-center max-w-3xl mx-auto mb-16">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                    >
                        <span className="text-sm font-semibold text-red-600 uppercase tracking-wider">The Bottleneck</span>
                        <h2 className="text-3xl md:text-4xl font-bold mt-2 mb-4 text-gray-900">
                            Thai Legal Practice is <span className="text-red-600">Broken</span>
                        </h2>
                        <p className="text-gray-600 text-lg">
                            Every day, skilled attorneys waste hours on tasks that should take minutes.
                            Sensitive client data flows through insecure channels. The cost of justice remains out of reach.
                        </p>
                    </motion.div>
                </div>

                {/* Problems Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-20">
                    {problems.map((problem, i) => (
                        <motion.div
                            key={problem.title}
                            initial={{ opacity: 0, y: 30 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: i * 0.1 }}
                            className="bg-red-50/50 border border-red-100 rounded-2xl p-6 relative group hover:shadow-lg transition-all"
                        >
                            <div className="flex items-center gap-3 mb-4">
                                <div className="p-2 bg-red-100 rounded-xl text-red-600">
                                    <problem.icon className="w-5 h-5" />
                                </div>
                                <span className="text-2xl font-bold text-red-600">{problem.stat}</span>
                            </div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">{problem.title}</h3>
                            <p className="text-gray-600 text-sm mb-4">{problem.description}</p>
                            <div className="text-xs font-bold text-red-700 bg-red-100 px-3 py-1 rounded-full inline-block">
                                {problem.pain}
                            </div>
                        </motion.div>
                    ))}
                </div>

                {/* Transition Arrow */}
                <div className="flex justify-center mb-16">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        viewport={{ once: true }}
                        className="flex flex-col items-center"
                    >
                        <div className="text-sm font-semibold text-gray-400 mb-2">But what if...</div>
                        <div className="w-12 h-12 rounded-full bg-gray-900 text-white flex items-center justify-center shadow-lg">
                            <ArrowRight className="w-5 h-5" />
                        </div>
                    </motion.div>
                </div>

                {/* Solution Header */}
                <div className="text-center max-w-3xl mx-auto mb-16">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                    >
                        <span className="text-sm font-semibold text-emerald-600 uppercase tracking-wider">The Transformation</span>
                        <h2 className="text-3xl md:text-4xl font-bold mt-2 mb-4 text-gray-900">
                            Sue.Ai <span className="text-emerald-600">Fixes Everything</span>
                        </h2>
                        <p className="text-gray-600 text-lg">
                            We built the legal operating system that Thai attorneys deserve.
                            From delay to speed. From risk to confidence. From cost to value.
                        </p>
                    </motion.div>
                </div>

                {/* Solutions Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {solutions.map((solution, i) => (
                        <motion.div
                            key={solution.title}
                            initial={{ opacity: 0, y: 30 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: i * 0.1 }}
                            className="bg-white border border-emerald-200 rounded-2xl p-6 relative group hover:shadow-xl hover:border-emerald-300 transition-all shadow-sm"
                        >
                            <div className="flex items-center gap-3 mb-4">
                                <div className="p-2 bg-emerald-100 rounded-xl text-emerald-600">
                                    <solution.icon className="w-5 h-5" />
                                </div>
                                <span className="text-2xl font-bold text-emerald-600">{solution.stat}</span>
                            </div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">{solution.title}</h3>
                            <p className="text-gray-600 text-sm mb-4">{solution.description}</p>
                            <div className="text-xs font-bold text-emerald-700 bg-emerald-100 px-3 py-1 rounded-full inline-block">
                                {solution.benefit}
                            </div>
                        </motion.div>
                    ))}
                </div>

                {/* CTA Section */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="mt-16 text-center"
                >
                    <p className="text-gray-500 mb-4">Ready to transform your practice?</p>
                    <button className="bg-gray-900 text-white px-8 py-3 rounded-full font-semibold shadow-lg hover:bg-gray-800 transition-all inline-flex items-center gap-2 group">
                        Request Early Access
                        <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </button>
                </motion.div>

            </div>
        </section>
    )
}
