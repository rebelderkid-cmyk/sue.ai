"use client"
import { Navbar } from "@/components/ui/navbar";
import { Hero } from "@/components/ui/hero";
import { ProblemSolution } from "@/components/ui/problem-solution";
import { Features } from "@/components/ui/features";

export default function Home() {
    return (
        <main className="min-h-screen relative selection:bg-primary/20">
            <Navbar />
            <Hero />
            <ProblemSolution />
            <Features />

            {/* Footer Placeholder for visual balance */}
            <footer className="border-t py-12 bg-muted/30">
                <div className="container mx-auto px-4 md:px-6 text-center text-sm text-muted-foreground">
                    <p>&copy; 2026 Sue.Ai Inc. All rights reserved.</p>
                </div>
            </footer>
        </main>
    );
}
