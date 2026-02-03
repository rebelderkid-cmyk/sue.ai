"use client"
import * as React from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send, Bot, User, ArrowLeft, Sparkles, X, BookOpen, Gavel, Scale, Menu, ExternalLink, Brain, BrainCircuit, Database, Loader2, Clock, PanelLeft } from "lucide-react"
import { cn } from "@/lib/utils"
import Link from "next/link"
import { motion, AnimatePresence } from "framer-motion"
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ChatHistorySidebar } from "@/components/ChatHistorySidebar"
import { useSearchParams, useRouter } from "next/navigation"
import { useUserStore } from "@/store/userStore"
import { useChatStore } from "@/store/chatStore"

interface Source {
    id: string
    year: string
    outcome: string
    text: string
    pdf_url?: string
    source?: string
    title?: string
    snippet?: string
    filename?: string
    content?: string
}

interface Message {
    id: string
    role: 'user' | 'assistant'
    content: string
    sources?: Source[]
}

// Memoized Input Component to prevent re-renders
const InputArea = React.memo(({
    input,
    setInput,
    handleSend,
    deepSearch,
    isTyping
}: {
    input: string,
    setInput: (v: string) => void,
    handleSend: (e: React.FormEvent) => void,
    deepSearch: boolean,
    isTyping: boolean
}) => {
    return (
        <form onSubmit={handleSend} className="relative flex items-center max-w-3xl mx-auto">
            <Input
                autoFocus
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={deepSearch ? "ถามคำถามเชิงลึก (Deep Research)..." : "พิมพ์คำถามหรือประเด็นที่ต้องการค้นคว้า..."}
                className={cn(
                    "w-full pl-6 pr-14 py-5 md:py-7 text-base rounded-full shadow-lg transition-all backdrop-blur-sm",
                    deepSearch
                        ? "bg-background/80 border-primary/30 ring-1 ring-primary/10" // Increased opacity
                        : "bg-background/80 border-muted-foreground/10"
                )}
            />
            <Button
                type="submit"
                size="icon"
                className={cn(
                    "absolute right-2 h-10 w-10 rounded-full shadow-md transition-all hover:scale-105",
                    deepSearch && "bg-primary shadow-primary/20"
                )}
                disabled={!input.trim() || isTyping}
            >
                {input.trim() ? <Send className="h-5 w-5" /> : <Sparkles className="h-5 w-5 opacity-50" />}
            </Button>
        </form>
    );
});
InputArea.displayName = "InputArea";

// Source List Component with Expand/Collapse
const SourceList = ({ sources, setSelectedSource }: { sources: Source[], setSelectedSource: (s: Source) => void }) => {
    const [expanded, setExpanded] = React.useState(false);
    const displayedSources = expanded ? sources : sources.slice(0, 5);
    const remaining = sources.length - 5;

    if (!sources || sources.length === 0) return null;

    return (
        <div className="mt-4 pt-3 border-t border-border/20">
            <p className="text-xs font-semibold mb-2 opacity-70 flex items-center gap-1">
                <BookOpen size={12} /> ฎีกาที่เกี่ยวข้อง ({sources.length} รายการ):
            </p>
            <div className="flex flex-wrap gap-2">
                {displayedSources.map((src, idx) => (
                    <button
                        key={idx}
                        onClick={() => setSelectedSource(src)}
                        className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-zinc-900 hover:bg-indigo-50 dark:hover:bg-zinc-800 rounded-lg text-xs transition-all border border-gray-200 dark:border-zinc-700 hover:border-indigo-200 dark:hover:border-indigo-500 shadow-sm text-left group"
                    >
                        <Gavel size={12} className={cn("shrink-0 transition-colors", src.source === 'LAW' ? "text-orange-600 dark:text-orange-400" : "text-indigo-600 dark:text-indigo-400")} />
                        {src.source === 'LAW' ? (
                            <span className="font-medium text-zinc-800 dark:text-zinc-100 truncate max-w-[150px] group-hover:text-indigo-700 dark:group-hover:text-indigo-300 transition-colors">{src.title || src.id}</span>
                        ) : (
                            <div className="flex flex-col">
                                <span className="font-bold text-zinc-900 dark:text-white group-hover:text-indigo-700 dark:group-hover:text-indigo-300 transition-colors">ฎีกาที่ {src.id}</span>
                                <span className="text-[10px] text-zinc-500 dark:text-zinc-400">ปี {src.year}</span>
                            </div>
                        )}
                    </button>
                ))}

                {!expanded && sources.length > 5 && (
                    <button
                        onClick={() => setExpanded(true)}
                        className="flex items-center gap-1 px-3 py-1.5 bg-primary/10 hover:bg-primary/20 text-primary rounded-lg text-xs font-bold transition-colors"
                    >
                        +{remaining} ดูเพิ่มเติม
                    </button>
                )}

                {expanded && sources.length > 5 && (
                    <button
                        onClick={() => setExpanded(false)}
                        className="flex items-center gap-1 px-3 py-1.5 bg-muted hover:bg-muted/80 text-muted-foreground rounded-lg text-xs font-medium transition-colors"
                    >
                        ย่อลง
                    </button>
                )}
            </div>
        </div>
    );
};

// Main Content Component (Logic)
function ChatContent() {
    const { user } = useUserStore();
    const searchParams = useSearchParams();
    const router = useRouter();
    const cid = searchParams.get('cid'); // Current Conversation ID

    // Store Hooks
    const { sessions, activeSessionId, createSession, setActiveSession, addMessage } = useChatStore();

    // Sync URL Session ID with Store
    React.useEffect(() => {
        if (cid) {
            if (activeSessionId !== cid) setActiveSession(cid);
        } else {
            // Check if we need to create a session or just wait (Wait for now, auto-create on send)
            if (!activeSessionId) {
                const newId = createSession(); // Pre-create for cleaner UX
                setActiveSession(newId);
                // Don't push URL yet to keep it clean until interaction
            }
        }
    }, [cid, activeSessionId, createSession, setActiveSession]);

    // Derived State
    const currentSession = activeSessionId ? sessions[activeSessionId] : null;
    const storeMessages = currentSession?.messages || [];

    // Local State
    const [showWelcome, setShowWelcome] = React.useState(true);

    // Check if we have history -> Hide welcome
    React.useEffect(() => {
        if (storeMessages.length > 0) setShowWelcome(false);
        else setShowWelcome(true);
    }, [storeMessages.length]);

    const [input, setInput] = React.useState('');
    const [isTyping, setIsTyping] = React.useState(false);

    // Streaming State (Temporary holding buffers)
    const [streamingContent, setStreamingContent] = React.useState('');
    const [streamingSources, setStreamingSources] = React.useState<Source[]>([]);
    const [agentMode, setAgentMode] = React.useState<'SEARCH' | 'ANSWER'>('SEARCH'); // Visual Mode

    const [selectedSource, setSelectedSource] = React.useState<Source | null>(null);
    const [showFilters, setShowFilters] = React.useState(false);
    const [filters, setFilters] = React.useState({ year: 2500, outcome: '' });

    // UI State
    const [mobileSidebarOpen, setMobileSidebarOpen] = React.useState(false); // Mobile Drawer
    const [desktopSidebarOpen, setDesktopSidebarOpen] = React.useState(true); // Desktop Collapsible

    // Combine store messages with current streaming message for display
    const messages = React.useMemo(() => {
        if (isTyping && streamingContent) {
            return [...storeMessages, {
                id: 'streaming-temp',
                role: 'assistant' as const,
                content: streamingContent,
                sources: streamingSources
            }];
        }
        return storeMessages;
    }, [storeMessages, isTyping, streamingContent, streamingSources]);
    const [statusText, setStatusText] = React.useState('กำลังประมวลผล...')

    const [deepSearch, setDeepSearch] = React.useState(false)
    const [docLimit, setDocLimit] = React.useState(5)

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!input.trim() || isTyping) return

        let currentId = activeSessionId;
        if (!currentId) {
            currentId = createSession();
            setActiveSession(currentId);
        }

        const userMsgContent = input.trim();
        setInput('');
        setIsTyping(true);
        setAgentMode('SEARCH');
        setShowWelcome(false);
        setStreamingContent('');
        setStreamingSources([]);
        setStatusText('กำลังติดต่อ Sue.AI...');

        // 1. Add User Message to Store
        addMessage(currentId, { role: 'user', content: userMsgContent });

        try {
            // Prepare History for Backend from Store
            // We get messages *before* the one we just added, effectively.
            // Or just grab the last 10 from the session. 
            // Since `addMessage` is synchronous in Zustand, the session should already have the user message.
            // But we might want to exclude it if backend treats 'history' as 'previous turns'.
            // Let's include everything for robust context.
            const currentSession = sessions[currentId];
            const history = currentSession ? currentSession.messages.slice(-10).map(m => ({
                role: m.role,
                content: m.content
            })) : [];

            // API Config
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
            const token = user ? await user.getIdToken() : '';

            const activeFilters: any = {}
            if (filters.outcome) activeFilters.outcome = filters.outcome
            if (filters.year > 2500) activeFilters.year = `>=${filters.year}`

            const res = await fetch(`${apiUrl}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': token ? `Bearer ${token}` : ''
                },
                body: JSON.stringify({
                    question: userMsgContent, // Current Question
                    filters: activeFilters,
                    history: history, // Context
                    deep_search: deepSearch,
                    doc_limit: docLimit
                }),
            });

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}));
                throw new Error(errorData.error || `API Error: ${res.statusText}`);
            }
            if (!res.body) throw new Error("No response body");

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let aggregatedContent = '';
            let aggregatedSources: Source[] = [];
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;
                const lines = buffer.split('\n\n');
                buffer = lines.pop() || ''; // Keep incomplete part for next loop

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.slice(6);
                        if (dataStr.trim() === '[DONE]') break;
                        try {
                            const data = JSON.parse(dataStr);
                            if (data.type === 'chunk') {
                                aggregatedContent += data.text;
                                setStreamingContent(aggregatedContent);
                                // Visual Feedback: if simple loading, switch to ANSWER mode when content starts
                                if (agentMode === 'SEARCH' && aggregatedContent.length > 5) setAgentMode('ANSWER');
                            } else if (data.type === 'sources') {
                                aggregatedSources = data.data;
                                setStreamingSources(aggregatedSources);
                            } else if (data.type === 'status') {
                                setStatusText(data.text);
                                if (data.mode) setAgentMode(data.mode);
                            }
                        } catch (e) { }
                    }
                }
            }

            // End Stream: Commit Assistant Message to Store
            addMessage(currentId, {
                role: 'assistant',
                content: aggregatedContent,
                sources: aggregatedSources
            });

        } catch (error) {
            console.error(error);
            addMessage(currentId, {
                role: 'assistant',
                content: `⚠️ เกิดข้อผิดพลาด: ${error instanceof Error ? error.message : 'Unknown Error'}`
            });
        } finally {
            setIsTyping(false);
            setStreamingContent('');
            setStreamingSources([]);
            setStatusText('พร้อมทำงาน');
            setAgentMode('SEARCH');
        }
    };

    return (
        <div className="flex h-[100dvh] bg-background font-sans overflow-hidden relative">

            <ChatHistorySidebar
                // Mobile Props
                isMobileOpen={mobileSidebarOpen}
                onMobileClose={() => setMobileSidebarOpen(false)}

                // Desktop Props
                isDesktopOpen={desktopSidebarOpen}
                toggleDesktop={() => setDesktopSidebarOpen(!desktopSidebarOpen)}

                onSelectConversation={(id) => {
                    if (id) setActiveSession(id);
                    setMobileSidebarOpen(false); // Close mobile drawer on select
                }}
            />

            <div className="flex flex-col flex-1 h-full min-w-0 transition-all duration-300">
                <header className="h-16 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-30 shrink-0">
                    <div className="container flex h-full items-center px-4 md:px-6">
                        <Link href="/" className="mr-4 flex items-center space-x-2 transition-colors hover:text-foreground/80 text-muted-foreground hover:text-primary md:hidden">
                            <ArrowLeft className="h-4 w-4" />
                        </Link>
                        <div className="flex items-center space-x-2 flex-1">
                            {/* Mobile Menu Trigger */}
                            <Button variant="ghost" size="icon" className="md:hidden mr-1" onClick={() => setMobileSidebarOpen(true)}>
                                <Menu className="h-5 w-5" />
                            </Button>

                            {/* Desktop Sidebar Toggle */}
                            <Button
                                variant="ghost"
                                size="icon"
                                className="hidden md:flex mr-2 text-muted-foreground hover:text-primary transition-all rounded-lg"
                                onClick={() => setDesktopSidebarOpen(!desktopSidebarOpen)}
                                title={desktopSidebarOpen ? "ซ่อนเมนู" : "แสดงเมนู"}
                            >
                                <PanelLeft className="h-5 w-5" />
                            </Button>

                            <div className="flex items-center gap-2">
                                <span className="font-bold inline-block text-zinc-800">Law5 AI</span>
                                <span className="hidden sm:inline-block text-[10px] px-2 py-0.5 rounded-full bg-primary/20 text-primary font-bold">AI Neuro</span>
                            </div>
                        </div>
                    </div>
                </header>

                {/* Filters Removed as per request */}

                <main className="flex-1 container max-w-3xl mx-auto flex flex-col min-h-0 overflow-hidden relative">
                    <div className="flex-1 overflow-y-auto space-y-6 p-4 scroll-smooth pb-24 no-scrollbar">
                        {messages.map((msg) => (
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                key={msg.id}
                                className={cn("flex w-full", msg.role === 'user' ? "justify-end" : "justify-start")}
                            >
                                <div className={cn(
                                    "flex flex-col px-4 py-3 md:px-5 md:py-4 text-sm shadow-sm",
                                    msg.role === 'user'
                                        ? "bg-primary text-primary-foreground rounded-2xl rounded-tr-sm max-w-[90%] md:max-w-[80%]"
                                        : "bg-secondary text-secondary-foreground border border-border/50 rounded-2xl rounded-tl-sm w-full"
                                )}>

                                    {/* Insight Card Parser & Renderer */}
                                    {(() => {
                                        let contentToRender = msg.content;
                                        let insightCardData = null;

                                        // Try to extract JSON block (Support both ''' and ``` fences)
                                        const jsonMatch = contentToRender.match(/(?:^|\s)(?:'''|```)(?:json)?\s*(\{[\s\S]*?"type"\s*:\s*"insight_card"[\s\S]*?\})\s*(?:'''|```)/);
                                        if (jsonMatch && jsonMatch[1]) {
                                            try {
                                                insightCardData = JSON.parse(jsonMatch[1]);
                                                // Remove the JSON block from the text to be rendered
                                                contentToRender = contentToRender.replace(jsonMatch[0], '').trim();
                                            } catch (e) {
                                                console.error("Failed to parse Insight Card JSON", e);
                                            }
                                        }

                                        // Timeline Parser (Legal Timeline) - Support both fences
                                        let timelineData = null;
                                        const timelineMatch = contentToRender.match(/(?:'''|```)(?:json)?\s*(\{\s*"type"\s*:\s*"timeline"[\s\S]*?\})\s*(?:'''|```)/);
                                        if (timelineMatch && timelineMatch[1]) {
                                            try {
                                                timelineData = JSON.parse(timelineMatch[1]);
                                                contentToRender = contentToRender.replace(timelineMatch[0], '').trim();
                                            } catch (e) {
                                                console.error("Failed to parse Timeline JSON", e);
                                            }
                                        }

                                        return (
                                            <>
                                                {/* Render Insight Card if data exists */}
                                                {insightCardData && (
                                                    <div className="mb-5 p-4 rounded-xl bg-background/50 border border-border/60 shadow-sm backdrop-blur-sm relative overflow-hidden group">
                                                        <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-primary/50 to-transparent opacity-50"></div>

                                                        {/* Header: Verdict Badge */}
                                                        <div className="flex justify-between items-start mb-3">
                                                            <div>
                                                                <h4 className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider mb-1">ผลการวิเคราะห์เบื้องต้น</h4>
                                                                <div className={cn(
                                                                    "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold border shadow-sm",
                                                                    insightCardData.verdict?.toLowerCase().includes('win') ? "bg-green-100 text-green-700 border-green-200" :
                                                                        insightCardData.verdict?.toLowerCase().includes('lose') ? "bg-red-100 text-red-700 border-red-200" :
                                                                            "bg-yellow-100 text-yellow-800 border-yellow-200"
                                                                )}>
                                                                    {insightCardData.verdict?.toLowerCase().includes('win') ? <Sparkles size={12} /> :
                                                                        insightCardData.verdict?.toLowerCase().includes('lose') ? <X size={12} /> : <Scale size={12} />}
                                                                    {insightCardData.verdict === 'Uncertain' ? 'ก้ำกึ่ง / ต้องพิจารณาข้อเท็จจริงเพิ่ม' :
                                                                        insightCardData.verdict === 'Likely Win' ? 'มีโอกาสชนะคดีสูง' :
                                                                            insightCardData.verdict === 'Likely Lose' ? 'มีความเสี่ยงสูง / โอกาสแพ้' : insightCardData.verdict}
                                                                </div>
                                                            </div>
                                                            <div className="text-right">
                                                                <span className="text-[10px] font-bold text-muted-foreground block mb-0.5">ความมั่นใจ (Confidence)</span>
                                                                <div className="flex items-center justify-end gap-1">
                                                                    <div className="flex gap-0.5">
                                                                        {[1, 2, 3].map(lvl => (
                                                                            <div key={lvl} className={cn(
                                                                                "w-1.5 h-3 rounded-sm",
                                                                                (insightCardData.confidence === 'High' && lvl <= 3) ||
                                                                                    (insightCardData.confidence === 'Medium' && lvl <= 2) ||
                                                                                    (insightCardData.confidence === 'Low' && lvl <= 1)
                                                                                    ? "bg-primary" : "bg-primary/20"
                                                                            )} />
                                                                        ))}
                                                                    </div>
                                                                    <span className="text-xs font-semibold text-primary">{insightCardData.confidence}</span>
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* Grid Info: Risk & Law */}
                                                        <div className="grid grid-cols-2 gap-3 text-xs">
                                                            <div className="bg-background/80 p-2 rounded-lg border border-border/30">
                                                                <span className="text-muted-foreground font-semibold block mb-1 text-[10px] uppercase">ระดับความเสี่ยง (Risk)</span>
                                                                <span className={cn(
                                                                    "font-bold",
                                                                    insightCardData.risk_level === 'High' ? "text-red-600" :
                                                                        insightCardData.risk_level === 'Medium' ? "text-orange-500" : "text-green-600"
                                                                )}>{insightCardData.risk_level} Risk</span>
                                                            </div>
                                                            <div className="bg-background/80 p-2 rounded-lg border border-border/30">
                                                                <span className="text-muted-foreground font-semibold block mb-1 text-[10px] uppercase">กฎหมายหลัก (Key Law)</span>
                                                                <span className="font-medium text-foreground truncate block">
                                                                    <ReactMarkdown components={{ p: ({ children }) => <span>{children}</span> }}>
                                                                        {insightCardData.key_law?.replace(/(มาตรา\s*[0-9๐-๙]+)/g, '[$1](cite:law:$1)') || '-'}
                                                                    </ReactMarkdown>
                                                                </span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Render Timeline if exists */}
                                                {timelineData && timelineData.events && (
                                                    <div className="mb-6 mt-4 p-4 rounded-xl border border-border/40 bg-background/30">
                                                        <h4 className="flex items-center gap-2 text-xs font-bold text-muted-foreground uppercase tracking-wider mb-5 pl-1">
                                                            <Clock size={14} /> ลำดับเหตุการณ์ (Timeline)
                                                        </h4>
                                                        <div className="relative border-l-2 border-indigo-200 dark:border-indigo-800 ml-2.5 space-y-6 pb-2">
                                                            {timelineData.events.map((evt: any, i: number) => (
                                                                <div key={i} className="relative pl-6">
                                                                    <div className="absolute -left-[9px] top-1.5 h-4 w-4 rounded-full border-4 border-background bg-indigo-500 shadow-sm z-10"></div>
                                                                    <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-3 mb-1">
                                                                        <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300 shrink-0 w-fit shadow-sm">
                                                                            {evt.date}
                                                                        </span>
                                                                        <h5 className="font-bold text-sm text-foreground">{evt.title}</h5>
                                                                    </div>
                                                                    <p className="text-xs text-muted-foreground leading-relaxed bg-muted/30 p-2.5 rounded-lg border border-border/30">
                                                                        {evt.description}
                                                                    </p>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                <div className="leading-relaxed w-full min-w-0">
                                                    <ReactMarkdown
                                                        remarkPlugins={[remarkGfm]}
                                                        // CRITICAL: Allow 'cite:' protocol
                                                        urlTransform={(url) => url}
                                                        components={{
                                                            p: ({ children }: any) => <div className="mb-4 last:mb-0 leading-relaxed">{children}</div>,
                                                            h1: ({ children }: any) => <h1 className="text-2xl font-bold mt-6 mb-4 text-foreground border-b pb-2">{children}</h1>,
                                                            h2: ({ children }: any) => <h2 className="text-xl font-bold mt-5 mb-3 text-foreground tracking-tight">{children}</h2>,
                                                            h3: ({ children }: any) => <h3 className="text-lg font-bold mt-4 mb-2 text-foreground">{children}</h3>,
                                                            strong: ({ children }: any) => <strong className="font-bold text-foreground">{children}</strong>,
                                                            ul: ({ children }: any) => <ul className="list-disc ml-6 mb-4 space-y-1">{children}</ul>,
                                                            ol: ({ children }: any) => <ol className="list-decimal ml-6 mb-4 space-y-1">{children}</ol>,
                                                            li: ({ children }: any) => <li className="mb-1">{children}</li>,
                                                            // Custom Link Handler for Smart Citations (High-Fidelity)
                                                            a: ({ href, children }: any) => {
                                                                const text = String(children);
                                                                const isDeka = href?.includes('cite:deka:') || text.includes('ฎีกา');
                                                                const isLaw = href?.includes('cite:law:') || text.includes('มาตรา') || text.includes('ป.วิ');

                                                                if (isDeka) {
                                                                    // Extract ID flexibly
                                                                    let id = (href || '').replace(/cite:deka:/, '').trim();
                                                                    if (!id || id === text || id.startsWith('http')) {
                                                                        const match = text.match(/\d+\/\d+/);
                                                                        if (match) id = match[0];
                                                                    }

                                                                    const source = msg.sources?.find(s => s.id.includes(id) || (id && s.id.includes(id)));
                                                                    const hasSource = !!source;

                                                                    return (
                                                                        <span className="relative inline-block group align-middle">
                                                                            <button
                                                                                type="button"
                                                                                onClick={(e) => {
                                                                                    e.preventDefault();
                                                                                    e.stopPropagation();
                                                                                    if (source) setSelectedSource(source);
                                                                                }}
                                                                                className={cn(
                                                                                    "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md mx-1 text-xs font-bold transition-all select-none peer",
                                                                                    "border shadow-sm",
                                                                                    hasSource
                                                                                        ? "bg-indigo-50 text-indigo-700 border-indigo-200 hover:bg-indigo-100 hover:border-indigo-300 hover:shadow-md cursor-pointer"
                                                                                        : "bg-slate-100 text-slate-500 border-slate-200 cursor-not-allowed opacity-70"
                                                                                )}
                                                                                disabled={!hasSource}
                                                                            >
                                                                                <Gavel size={10} className={cn(hasSource ? "text-indigo-600" : "text-slate-400")} />
                                                                                <span className="truncate max-w-[180px]">{text}</span>
                                                                                {hasSource && <ExternalLink size={8} className="opacity-50" />}
                                                                            </button>

                                                                            {/* Smart Hover Card (Appears on Hover) */}
                                                                            {hasSource && (
                                                                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 p-3 bg-white dark:bg-zinc-900 border border-border/50 rounded-xl shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 pointer-events-none origin-bottom scale-95 group-hover:scale-100">
                                                                                    <div className="flex items-center gap-2 mb-2 border-b border-border/30 pb-2">
                                                                                        <div className="p-1 bg-indigo-50 rounded-md">
                                                                                            <Gavel size={12} className="text-indigo-600" />
                                                                                        </div>
                                                                                        <span className="text-xs font-bold text-foreground truncate flex-1">
                                                                                            ฎีกาที่ {source.id} <span className="text-[10px] text-muted-foreground font-normal ml-1">({source.year})</span>
                                                                                        </span>
                                                                                        <span className={cn(
                                                                                            "text-[9px] px-1.5 py-0.5 rounded font-bold uppercase",
                                                                                            source.outcome === 'WIN' ? "bg-green-100 text-green-700" :
                                                                                                source.outcome === 'LOSE' ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-600"
                                                                                        )}>{source.outcome || 'N/A'}</span>
                                                                                    </div>
                                                                                    <p className="text-[10px] text-muted-foreground line-clamp-4 leading-relaxed font-sans">
                                                                                        {source.snippet || source.content?.substring(0, 200).replace(/\s+/g, ' ') || "ไม่มีเนื้อหาย่อ"}...
                                                                                    </p>
                                                                                    <div className="mt-2 pt-1 flex items-center justify-between border-t border-border/10">
                                                                                        <span className="text-[9px] text-muted-foreground">กดเพื่อดูฉบับเต็ม</span>
                                                                                        <ExternalLink size={10} className="text-indigo-500" />
                                                                                    </div>
                                                                                    {/* Arrow */}
                                                                                    <div className="absolute top-full left-1/2 -translate-x-1/2 border-[6px] border-transparent border-t-white dark:border-t-zinc-900 drop-shadow-sm"></div>
                                                                                </div>
                                                                            )}
                                                                        </span>
                                                                    );
                                                                }

                                                                if (isLaw) {
                                                                    // Extract clean text from children
                                                                    const textContent = Array.isArray(children)
                                                                        ? children.find(c => typeof c === 'string') || children[0]?.toString()
                                                                        : String(children);

                                                                    // Attempt to find matching LAW source in the message sources
                                                                    const source = msg.sources?.find(s =>
                                                                        s.source === 'LAW' &&
                                                                        (
                                                                            s.title?.includes(textContent) ||
                                                                            s.content?.includes(textContent) ||
                                                                            s.snippet?.includes(textContent) ||
                                                                            (s.filename && textContent.includes(s.filename.split('-')[0]))
                                                                        )
                                                                    );
                                                                    const hasSource = !!source;

                                                                    // DEBUG CITATION:
                                                                    if (!hasSource) {
                                                                        console.log(`🔎 [Citation Debug] No local source found for: "${textContent}". Available titles:`, msg.sources?.map(s => s.title));
                                                                    } else {
                                                                        console.log(`✅ [Citation Debug] Match found for: "${textContent}" -> Document URL: ${source.pdf_url}`);
                                                                    }

                                                                    // If no local source, link to Google Search
                                                                    const externalLink = `https://www.google.com/search?q=${encodeURIComponent(textContent + " มาตรา")}`;

                                                                    return (
                                                                        <span className="relative inline-block group align-baseline">
                                                                            <button
                                                                                type="button"
                                                                                onClick={(e) => {
                                                                                    e.preventDefault();
                                                                                    e.stopPropagation();
                                                                                    if (source) {
                                                                                        setSelectedSource(source);
                                                                                    } else {
                                                                                        window.open(externalLink, '_blank');
                                                                                    }
                                                                                }}
                                                                                className={cn(
                                                                                    "inline-flex items-center gap-1 px-1.5 py-0.5 rounded mx-0.5 text-[11px] font-semibold border align-baseline select-none transition-all peer",
                                                                                    hasSource
                                                                                        ? "bg-orange-50 text-orange-700 border-orange-200 hover:bg-orange-100 hover:border-orange-300 cursor-pointer shadow-sm hover:shadow"
                                                                                        : "bg-orange-50/30 text-orange-600/70 border-orange-100/50 hover:bg-orange-50 hover:border-orange-200 cursor-pointer border-dashed"
                                                                                )}
                                                                            >
                                                                                <Scale size={9} className={cn(hasSource ? "text-orange-600" : "text-orange-400")} />
                                                                                {textContent}
                                                                                <ExternalLink size={8} className="ml-1 opacity-50" />
                                                                            </button>

                                                                            {/* Smart Hover Card (Appears on Hover) */}
                                                                            {hasSource && (
                                                                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-80 p-3 bg-white dark:bg-zinc-900 border border-border/50 rounded-xl shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 pointer-events-none origin-bottom scale-95 group-hover:scale-100">
                                                                                    <div className="flex items-center gap-2 mb-2 border-b border-border/30 pb-2">
                                                                                        <div className="p-1 bg-orange-50 rounded-md">
                                                                                            <Scale size={12} className="text-orange-600" />
                                                                                        </div>
                                                                                        <span className="text-xs font-bold text-foreground truncate flex-1 leading-tight">
                                                                                            {source.title}
                                                                                        </span>
                                                                                        <span className="text-[9px] px-1.5 py-0.5 rounded font-bold bg-orange-100 text-orange-700 uppercase">
                                                                                            LAW
                                                                                        </span>
                                                                                    </div>
                                                                                    <div className="text-[10px] text-muted-foreground max-h-[100px] overflow-y-auto leading-relaxed font-mono bg-muted/30 p-2 rounded-md">
                                                                                        {source.content || source.snippet || "กำลังโหลดข้อมูล..."}
                                                                                    </div>
                                                                                    <div className="mt-2 pt-1 flex items-center justify-between border-t border-border/10">
                                                                                        <span className="text-[9px] text-muted-foreground">กดเพื่อดูรายละเอียด</span>
                                                                                        <ExternalLink size={10} className="text-orange-500" />
                                                                                    </div>
                                                                                    {/* Arrow */}
                                                                                    <div className="absolute top-full left-1/2 -translate-x-1/2 border-[6px] border-transparent border-t-white dark:border-t-zinc-900 drop-shadow-sm"></div>
                                                                                </div>
                                                                            )}
                                                                        </span>
                                                                    );
                                                                }

                                                                // Default External Link
                                                                return (
                                                                    <a
                                                                        href={href}
                                                                        className="text-primary hover:text-primary/80 underline decoration-primary/30 underline-offset-4 transition-colors"
                                                                        target="_blank"
                                                                        rel="noopener noreferrer"
                                                                    >
                                                                        {children}
                                                                    </a>
                                                                );
                                                            },
                                                            table: ({ children }: any) => (
                                                                <div className="overflow-x-auto my-4 rounded-lg border border-border/50">
                                                                    <table className="w-full text-sm text-left border-collapse">{children}</table>
                                                                </div>
                                                            ),
                                                            thead: ({ children }: any) => <thead className="bg-muted/50 text-muted-foreground font-medium">{children}</thead>,
                                                            th: ({ children }: any) => <th className="px-4 py-3 border-b border-border/50 font-semibold">{children}</th>,
                                                            td: ({ children }: any) => <td className="px-4 py-3 border-b border-border/50 last:border-0 align-top">{children}</td>,
                                                        }}
                                                    >
                                                        {/* Pre-process text to turn keywords into fake links - Added boundaries to prevent breaking existing links/bold */}
                                                        {typeof contentToRender === 'string' ? contentToRender
                                                            // Linkify 'ฎีกา(ที่) X/Y' -> [text](cite:deka:ID) 
                                                            .replace(/(?<!\[)(ฎีกา(?:ที่)?\s*(\d+\/\d+))(?!\()/g, '[$1](cite:deka:$2)')
                                                            // Linkify 'มาตรา X'
                                                            .replace(/(?<!\[)(มาตรา\s*[0-9๐-๙]+(?:\s*(?:ทวิ|ตรี|จัตวา))?(?:(?:\s*,\s*| และ )[0-9๐-๙]+)*)(?!\()/g, '[$1](cite:law:$1)')
                                                            // Linkify 'ป.อ.' 'ป.พ.พ.' + Section
                                                            .replace(/(?<!\[)((?:ป\.อ\.|ป\.พ\.พ\.|ป\.วิ\.อ\.|ป\.วิ\.พ\.)\s*มาตรา\s*[0-9๐-๙]+)(?!\()/g, '[$1](cite:law:$1)')
                                                            : ''}
                                                    </ReactMarkdown>
                                                </div>
                                            </>
                                        );
                                    })()}

                                    {/* SourceList removed as citations are now inline */}
                                </div >
                            </motion.div>
                        ))}

                        {/* Professional Welcome Screen with Suggestions */}
                        {showWelcome && messages.length === 0 && !isTyping && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="flex flex-col items-center justify-center py-12 px-4"
                            >
                                <div className="text-center mb-8">
                                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/20 mb-4">
                                        <Scale className="h-8 w-8 text-primary" />
                                    </div>
                                    <h2 className="text-2xl font-bold mb-2">Law5 AI</h2>
                                    <p className="text-muted-foreground">ผู้ช่วยอัจฉริยะส่วนตัวของทนายความ (Your AI Legal Assistant)</p>
                                </div>

                                <div className="w-full max-w-2xl space-y-3">
                                    <p className="text-sm font-medium text-muted-foreground mb-3">ลองเริ่มต้นด้วย:</p>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                        {[
                                            { icon: '📚', text: 'สืบค้นฎีกาที่เกี่ยวกับการเลิกจ้างไม่เป็นธรรม' },
                                            { icon: '⚖️', text: 'เทียบเคียงฎีกาความผิดฐานฉ้อโกง vs ชิงทรัพย์' },
                                            { icon: '🔍', text: 'วิเคราะห์รูปคดี: ลูกหนี้ผิดนัดชำระหนี้ตามสัญญากู้' },
                                            { icon: '📋', text: 'สรุปหลักกฎหมายเรื่องการครอบครองปรปักษ์' },
                                        ].map((suggestion, idx) => (
                                            <button
                                                key={idx}
                                                onClick={() => { setInput(suggestion.text); setShowWelcome(false); }}
                                                className="flex items-center gap-3 p-4 text-left rounded-xl border border-border/50 bg-background/50 hover:bg-muted/50 hover:border-primary/30 transition-all group"
                                            >
                                                <span className="text-lg">{suggestion.icon}</span>
                                                <span className="text-sm text-muted-foreground group-hover:text-foreground transition-colors">{suggestion.text}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </motion.div>
                        )}

                        {/* Transparent Mind Loading Indicator */}
                        {isTyping && (
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="flex w-full justify-start py-4"
                            >
                                <div className={cn(
                                    "flex flex-col gap-2 px-5 py-4 rounded-2xl rounded-tl-sm border transition-all duration-500",
                                    agentMode === 'ANSWER'
                                        ? "bg-indigo-50/50 border-indigo-200/50" // Memory Mode Style
                                        : "bg-secondary/50 border-border/30"      // Search Mode Style
                                )}>
                                    <div className="flex items-center gap-4">
                                        <div className="relative flex items-center justify-center h-10 w-10 shrink-0">
                                            {agentMode === 'ANSWER' ? (
                                                <>
                                                    <div className="absolute inset-0 bg-indigo-500/20 rounded-full animate-ping opacity-75"></div>
                                                    <div className="relative bg-white dark:bg-zinc-900 rounded-full p-2 border border-indigo-100 shadow-sm">
                                                        <BrainCircuit className="h-5 w-5 text-indigo-600 animate-pulse" />
                                                    </div>
                                                </>
                                            ) : (
                                                <>
                                                    <div className="absolute inset-0 bg-sky-500/20 rounded-full animate-spin-slow opacity-75" style={{ animationDuration: '3s' }}></div>
                                                    <div className="relative bg-white dark:bg-zinc-900 rounded-full p-2 border border-sky-100 shadow-sm">
                                                        {deepSearch ? (
                                                            <Database className="h-5 w-5 text-sky-600 animate-pulse" />
                                                        ) : (
                                                            <Loader2 className="h-5 w-5 text-sky-600 animate-spin" />
                                                        )}
                                                    </div>
                                                </>
                                            )}
                                        </div>

                                        <div className="flex flex-col gap-0.5">
                                            <span className={cn(
                                                "text-sm font-bold bg-clip-text text-transparent bg-gradient-to-r",
                                                agentMode === 'ANSWER'
                                                    ? "from-indigo-600 to-purple-600"
                                                    : "from-sky-600 to-blue-600"
                                            )}>
                                                {statusText}
                                            </span>

                                            {/* Sub-status with Typewriter effect idea or just fade-in */}
                                            <div className="flex items-center gap-2 text-[10px] text-muted-foreground/80 font-medium">
                                                {agentMode === 'ANSWER' ? (
                                                    <span className="flex items-center gap-1.5 text-indigo-400">
                                                        <Sparkles size={10} />
                                                        Connecting Context & Memory...
                                                    </span>
                                                ) : (
                                                    <span className="flex items-center gap-1.5 text-sky-400">
                                                        <Database size={10} />
                                                        {deepSearch ? "Deep Semantic Analysis..." : "Retrieving Legal Precedents..."}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                </div>
                            </motion.div>
                        )}
                    </div>

                    <div className="p-4 bg-background shrink-0 space-y-2">
                        <div className="max-w-3xl mx-auto flex items-center justify-between px-2">
                            <div className="flex items-center gap-4">
                                <button
                                    type="button"
                                    onClick={() => setDeepSearch(!deepSearch)}
                                    className={cn(
                                        "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all border",
                                        deepSearch
                                            ? "bg-primary/20 text-primary border-primary/30 shadow-sm"
                                            : "bg-secondary text-muted-foreground border-border/50 hover:border-primary/20"
                                    )}
                                >
                                    <Sparkles className={cn("h-3.5 w-3.5", deepSearch && "text-primary")} />
                                    Deep Research
                                </button>

                                {deepSearch && (
                                    <div className="flex items-center gap-2 animate-in fade-in slide-in-from-left-2 transition-all">
                                        <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Doc Limit:</span>
                                        <select
                                            value={docLimit}
                                            onChange={(e) => setDocLimit(parseInt(e.target.value))}
                                            className="bg-secondary border-none text-xs rounded-md px-2 py-1 focus:ring-1 focus:ring-primary/20 outline-none"
                                        >
                                            {[5, 10, 15].map(v => (
                                                <option key={v} value={v}>{v}</option>
                                            ))}
                                        </select>
                                    </div>
                                )}
                            </div>

                            {deepSearch && (
                                <div className="text-[10px] text-primary/70 font-medium animate-pulse">
                                    🚀 High Precision Mode Active
                                </div>
                            )}
                        </div>

                        <InputArea
                            input={input}
                            setInput={setInput}
                            handleSend={handleSend}
                            deepSearch={deepSearch}
                            isTyping={isTyping}
                        />
                    </div>

                </main>
            </div>

            <AnimatePresence>
                {selectedSource && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setSelectedSource(null)}
                            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
                        />
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 20 }}
                            className="relative w-full max-w-5xl bg-background rounded-xl shadow-2xl border border-border/50 overflow-hidden flex flex-col h-[90vh]"
                        >
                            <div className="flex items-center justify-between p-4 border-b bg-muted/30">
                                <div className="flex items-center gap-2">
                                    <Scale className="h-5 w-5 text-primary" />
                                    <div>
                                        <h3 className="font-bold text-lg">
                                            {selectedSource.source === 'LAW' ? selectedSource.title : `คำพิพากษาศาลฎีกาที่ ${selectedSource.id}`}
                                        </h3>
                                        <p className="text-xs text-muted-foreground">
                                            {selectedSource.source === 'LAW'
                                                ? `ไฟล์: ${selectedSource.filename || selectedSource.id}`
                                                : `ปี: ${selectedSource.year} | ผลคดี: ${selectedSource.outcome}`}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    {selectedSource.pdf_url && selectedSource.pdf_url.startsWith('http') && (
                                        <a
                                            href={selectedSource.pdf_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex items-center gap-1.5 px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg text-xs font-medium transition-colors border border-red-200"
                                        >
                                            <BookOpen size={14} />
                                            Open in Tab
                                        </a>
                                    )}
                                    <Button variant="ghost" size="icon" onClick={() => setSelectedSource(null)}>
                                        <X className="h-4 w-4" />
                                    </Button>
                                </div>
                            </div>
                            <div className="flex-1 bg-muted/20 relative w-full h-full min-h-[500px]">
                                {selectedSource.pdf_url ? (
                                    <iframe
                                        src={selectedSource.pdf_url}
                                        className="w-full h-full absolute inset-0 rounded-b-xl border-none"
                                        title={`Document Preview ${selectedSource.id}`}
                                    />
                                ) : (
                                    <div className="p-6 overflow-y-auto h-full leading-loose text-sm whitespace-pre-wrap flex flex-col items-center justify-center text-muted-foreground text-center">
                                        <div className="bg-muted p-4 rounded-full mb-4">
                                            <Sparkles className="h-8 w-8 opacity-50" />
                                        </div>
                                        <p className="text-lg font-medium">Document Preview Unavailable</p>
                                        <p className="text-sm opacity-70 mb-6">ขณะนี้ระบบกำลังประมวลผลไฟล์ต้นฉบับ ท่านสามารถค้นหาตัวบทเต็มได้ที่ปุ่มด้านล่าง</p>

                                        <a
                                            href={`https://www.google.com/search?q=${encodeURIComponent(selectedSource.title + " ตัวบทเต็ม")}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="px-6 py-2 bg-primary text-primary-foreground rounded-full text-sm font-bold hover:shadow-lg transition-all flex items-center gap-2"
                                        >
                                            <ExternalLink size={16} />
                                            ค้นหาจากแหล่งข้อมูลภายนอก (Google)
                                        </a>

                                        <div className="mt-8 text-left w-full max-w-2xl bg-background p-6 rounded-xl border border-border/50 shadow-sm">
                                            <h4 className="font-bold mb-2 text-foreground">เนื้อหาโดยสังเขป:</h4>
                                            {selectedSource.snippet || selectedSource.text || "ไม่มีข้อมูลเนื้อหา"}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    )
}

// Export wrapper with Suspense
export default function ChatPage() {
    return (
        <React.Suspense fallback={<div className="flex items-center justify-center h-screen">Loading Sue.Ai...</div>}>
            <ChatContent />
        </React.Suspense>
    )
}
