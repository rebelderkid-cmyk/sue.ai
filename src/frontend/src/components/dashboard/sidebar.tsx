"use client"
import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
    LayoutDashboard,
    MessageSquare,
    Settings,
    LogOut,
    ChevronLeft,
    ChevronRight,
    PlusCircle
} from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

interface SidebarProps {
    collapsed: boolean
    setCollapsed: (collapsed: boolean) => void
}

export function Sidebar({ collapsed, setCollapsed }: SidebarProps) {
    const pathname = usePathname()

    const links = [
        { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
        { href: "/dashboard/chat", label: "Chat", icon: MessageSquare },
        { href: "/dashboard/settings", label: "Settings", icon: Settings },
    ]

    return (
        <motion.aside
            initial={false}
            animate={{ width: collapsed ? 80 : 280 }}
            className={cn(
                "relative flex flex-col border-r bg-card h-screen z-30 transition-all duration-300 ease-in-out hidden md:flex",
            )}
        >
            <div className="flex items-center justify-between p-4 h-16 border-b">
                <AnimatePresence mode="wait">
                    {!collapsed && (
                        <motion.span
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="text-xl font-bold tracking-tight"
                        >
                            Sue.Ai
                        </motion.span>
                    )}
                </AnimatePresence>
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setCollapsed(!collapsed)}
                    className="ml-auto"
                >
                    {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
                </Button>
            </div>

            <div className="flex-1 overflow-y-auto py-4 px-3 space-y-2">
                {/* New Chat Button */}
                <Button
                    variant={collapsed ? "ghost" : "default"}
                    className={cn("w-full justify-start mb-6", collapsed && "justify-center px-0")}
                    size={collapsed ? "icon" : "default"}
                >
                    {collapsed ? <PlusCircle className="h-5 w-5" /> : (
                        <>
                            <PlusCircle className="mr-2 h-4 w-4" />
                            New Chat
                        </>
                    )}
                </Button>

                {links.map((link) => {
                    const Icon = link.icon
                    const isActive = pathname === link.href;
                    return (
                        <Link key={link.href} href={link.href} passHref>
                            <Button
                                variant={isActive ? "secondary" : "ghost"}
                                className={cn(
                                    "w-full justify-start",
                                    collapsed && "justify-center px-0"
                                )}
                                size={collapsed ? "icon" : "default"}
                            >
                                <Icon className={cn("h-4 w-4", !collapsed && "mr-3")} />
                                {!collapsed && <span>{link.label}</span>}
                            </Button>
                        </Link>
                    )
                })}
            </div>

            <div className="p-4 border-t mt-auto">
                <Button
                    variant="ghost"
                    className={cn("w-full justify-start text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20", collapsed && "justify-center px-0")}
                    size={collapsed ? "icon" : "default"}
                >
                    <LogOut className={cn("h-4 w-4", !collapsed && "mr-3")} />
                    {!collapsed && <span>Sign Out</span>}
                </Button>
            </div>
        </motion.aside>
    )
}
