"use client"
import * as React from "react"
import { Sidebar } from "@/components/dashboard/sidebar"
import { Menu } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const [collapsed, setCollapsed] = React.useState(false)

    // Mobile drawer state could be added here

    return (
        <div className="flex min-h-screen bg-background text-foreground">
            <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />

            <div className="flex-1 flex flex-col min-h-screen">
                {/* Mobile Header */}
                <header className="md:hidden flex items-center p-4 border-b h-16 bg-card">
                    <Button variant="ghost" size="icon" className="mr-2">
                        <Menu className="h-6 w-6" />
                    </Button>
                    <span className="font-bold text-lg">Sue.Ai</span>
                </header>

                <main className="flex-1 p-6 overflow-y-auto">
                    {children}
                </main>
            </div>
        </div>
    )
}
