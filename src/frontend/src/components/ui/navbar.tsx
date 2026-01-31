"use client"
import * as React from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { Menu, X, LogOut, User as UserIcon } from "lucide-react"
import { useUserStore } from "@/store/userStore"
import { auth } from "@/lib/firebase"
import { signOut } from "firebase/auth"
import { useRouter } from "next/navigation"

export function Navbar() {
    const [isOpen, setIsOpen] = React.useState(false)
    const { user, setUser } = useUserStore()
    const router = useRouter()

    const handleLogout = async () => {
        try {
            await signOut(auth)
            setUser(null)
            router.push("/")
        } catch (error) {
            console.error("Logout error", error)
        }
    }

    return (
        <header className="sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container mx-auto flex h-16 items-center px-4 md:px-6">
                <Link href="/" className="mr-6 flex items-center space-x-2">
                    {/* Logo Placeholder */}
                    <span className="text-xl font-bold tracking-tight">Sue.Ai</span>
                </Link>
                <nav className="hidden md:flex flex-1 items-center justify-between">
                    <div className="flex items-center space-x-6 text-sm font-medium">
                        <Link href="/chat" className="transition-colors hover:text-foreground/80 text-foreground/60">Chat</Link>
                        <Link href="#features" className="transition-colors hover:text-foreground/80 text-foreground/60">Features</Link>
                        <Link href="#pricing" className="transition-colors hover:text-foreground/80 text-foreground/60">Pricing</Link>
                    </div>
                    <div className="flex items-center space-x-4">
                        {user ? (
                            <div className="flex items-center gap-4">
                                <span className="text-sm text-muted-foreground mr-2">
                                    {user.email}
                                </span>
                                <Button variant="ghost" size="sm" onClick={handleLogout}>
                                    <LogOut className="mr-2 h-4 w-4" />
                                    Sign Out
                                </Button>
                                <Link href="/chat">
                                    <Button size="sm">Workspace</Button>
                                </Link>
                            </div>
                        ) : (
                            <>
                                <Link href="/login">
                                    <Button variant="ghost" size="sm">Log in</Button>
                                </Link>
                                <Link href="/login">
                                    <Button size="sm">Get Started</Button>
                                </Link>
                            </>
                        )}
                    </div>
                </nav>
                <button className="flex items-center space-x-2 md:hidden ml-auto" onClick={() => setIsOpen(!isOpen)}>
                    {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
                </button>
            </div>
            {/* Mobile Menu */}
            {isOpen && (
                <div className="md:hidden border-t p-4 space-y-4 bg-background">
                    <div className="flex flex-col space-y-4 text-sm font-medium">
                        <Link href="/chat" className="text-foreground/80" onClick={() => setIsOpen(false)}>Chat</Link>
                        <Link href="#features" className="text-foreground/80" onClick={() => setIsOpen(false)}>Features</Link>
                        <Link href="#pricing" className="text-foreground/80" onClick={() => setIsOpen(false)}>Pricing</Link>
                    </div>
                    <div className="flex flex-col space-y-2 pt-4">
                        {user ? (
                            <>
                                <div className="text-sm text-muted-foreground px-4 py-2 border rounded-md mb-2">
                                    {user.email}
                                </div>
                                <Button variant="ghost" className="justify-start" onClick={handleLogout}>Sign Out</Button>
                            </>
                        ) : (
                            <>
                                <Link href="/login" onClick={() => setIsOpen(false)}>
                                    <Button variant="ghost" className="justify-start w-full">Log in</Button>
                                </Link>
                                <Link href="/login" onClick={() => setIsOpen(false)}>
                                    <Button className="justify-start w-full">Get Started</Button>
                                </Link>
                            </>
                        )}
                    </div>
                </div>
            )}
        </header>
    )
}
