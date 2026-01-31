"use client"
import * as React from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send, Bot, User } from "lucide-react"
import { cn } from "@/lib/utils"

interface Message {
    id: string
    role: 'user' | 'assistant'
    content: string
}

export default function ChatPage() {
    const [messages, setMessages] = React.useState<Message[]>([
        { id: '1', role: 'assistant', content: 'Hello. I am Sue.Ai. How can I assist you today?' }
    ])
    const [input, setInput] = React.useState('')

    const handleSend = (e: React.FormEvent) => {
        e.preventDefault()
        if (!input.trim()) return

        const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input }
        setMessages(prev => [...prev, userMsg])
        setInput('')

        // Mock response
        setTimeout(() => {
            const aiMsg: Message = { id: (Date.now() + 1).toString(), role: 'assistant', content: 'I have received your request. This is a simulation of my capabilities.' }
            setMessages(prev => [...prev, aiMsg])
        }, 1000)
    }

    return (
        <div className="flex flex-col h-[calc(100vh-8rem)]">
            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto space-y-4 p-4 rounded-lg bg-muted/10 border mb-4">
                {messages.map((msg) => (
                    <div key={msg.id} className={cn("flex w-full", msg.role === 'user' ? "justify-end" : "justify-start")}>
                        <div className={cn(
                            "flex max-w-[80%] rounded-2xl px-4 py-3 text-sm shadow-sm",
                            msg.role === 'user'
                                ? "bg-primary text-primary-foreground ml-2 rounded-tr-sm"
                                : "bg-card border mr-2 rounded-tl-sm"
                        )}>
                            <div className="mr-3 mt-1 flex-shrink-0 opacity-70">
                                {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                            </div>
                            <div className="leading-relaxed">
                                {msg.content}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Input Area */}
            <div className="relative">
                <form onSubmit={handleSend} className="flex gap-2">
                    <Input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type your instruction..."
                        className="flex-1 py-6 pl-6 pr-12 text-base rounded-full shadow-lg border-muted-foreground/10 focus-visible:ring-primary/20 bg-background"
                    />
                    <Button
                        type="submit"
                        size="icon"
                        className="absolute right-2 top-1.5 h-9 w-9 rounded-full shadow-sm"
                        disabled={!input.trim()}
                    >
                        <Send className="h-4 w-4" />
                    </Button>
                </form>
            </div>
        </div>
    )
}
