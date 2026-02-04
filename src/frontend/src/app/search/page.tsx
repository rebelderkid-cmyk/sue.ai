'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ChatHistorySidebar } from '@/components/ChatHistorySidebar';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Search, Loader2, ArrowLeft, BookOpen, AlertCircle, Sparkles, BrainCircuit, FileText, Gavel, Scale, PanelLeft } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface ComparisonResult {
    case_id: string;
    year: string;
    facts: string;
    legal_issue: string;
    ruling: string;
    reasoning: string;
    lawyer_opinion: string;
    pdf_url?: string;
    original_id?: string;
}

// Loading/Thinking Component
const ThinkingIndicator = ({ message }: { message: string }) => (
    <div className="flex items-center gap-3 text-sm text-purple-600 font-medium animate-pulse bg-purple-50 px-4 py-2 rounded-full w-fit">
        <BrainCircuit className="h-4 w-4 animate-spin-slow" />
        <span>{message}</span>
    </div>
);

// Card Component for Each Case
const CaseCard = ({ item, onOpenPdf }: { item: ComparisonResult, onOpenPdf: (url: string, title: string) => void }) => {
    const isGenerating = item.lawyer_opinion === "Generating..." || !item.lawyer_opinion;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="group relative bg-white border border-zinc-200 rounded-2xl shadow-sm hover:shadow-md transition-all overflow-hidden mb-6"
        >
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-start md:justify-between p-4 md:p-5 border-b border-zinc-100 bg-zinc-50/50 gap-3 md:gap-0">
                <div className="flex flex-col gap-1 w-full">
                    <div className="flex flex-wrap items-center gap-2">
                        <span className="bg-zinc-100 text-zinc-500 text-xs px-2 py-0.5 rounded-md font-mono border border-zinc-200 whitespace-nowrap">
                            {item.year || 'N/A'}
                        </span>
                        <button
                            onClick={() => item.pdf_url && onOpenPdf(item.pdf_url, item.case_id)}
                            className="text-base md:text-lg font-bold text-zinc-800 hover:text-purple-600 transition-colors flex items-center gap-2 text-left cursor-pointer flex-1"
                        >
                            <span className="break-words">คำพิพากษาศาลฎีกาที่ {item.case_id}</span>
                            <BookOpen className="h-4 w-4 opacity-0 group-hover:opacity-50 transition-opacity hidden md:block" />
                        </button>
                    </div>
                </div>
                <Button
                    variant="ghost"
                    size="sm"
                    className="text-purple-600 hover:text-purple-700 hover:bg-purple-50 w-full md:w-auto justify-center md:justify-start bg-white md:bg-transparent border md:border-transparent border-purple-100 shadow-sm md:shadow-none"
                    onClick={() => item.pdf_url && onOpenPdf(item.pdf_url, item.case_id)}
                    disabled={!item.pdf_url}
                >
                    <BookOpen className="h-4 w-4 mr-2" />
                    {item.pdf_url ? "อ่านฉบับเต็ม" : "ไม่มีไฟล์ PDF"}
                </Button>
            </div>

            {/* Body Content */}
            <div className="p-4 md:p-6 grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
                {/* Left Column: Facts & Issue */}
                <div className="space-y-6">
                    <div>
                        <h4 className="flex items-center gap-2 text-sm font-semibold text-zinc-400 mb-2 uppercase tracking-wide">
                            <FileText className="h-4 w-4" /> ข้อเท็จจริง (Facts)
                        </h4>
                        <p className="text-zinc-700 leading-relaxed text-sm">
                            {item.facts}
                        </p>
                    </div>
                    <div>
                        <h4 className="flex items-center gap-2 text-sm font-semibold text-zinc-400 mb-2 uppercase tracking-wide">
                            <Scale className="h-4 w-4" /> ประเด็นข้อกฎหมาย
                        </h4>
                        <p className="text-zinc-700 leading-relaxed text-sm font-medium">
                            {item.legal_issue}
                        </p>
                    </div>
                </div>

                {/* Right Column: Ruling & AI Opinion */}
                <div className="space-y-6">
                    <div>
                        <h4 className="flex items-center gap-2 text-sm font-semibold text-zinc-400 mb-2 uppercase tracking-wide">
                            <Gavel className="h-4 w-4" /> คำวินิจฉัย (Ruling)
                        </h4>
                        <p className="text-zinc-700 leading-relaxed text-sm bg-zinc-50 p-3 rounded-lg border border-zinc-100 italic">
                            "{item.ruling}"
                        </p>
                        <p className="text-zinc-500 text-xs mt-2 pl-1">
                            เหตุผล: {item.reasoning}
                        </p>
                    </div>

                    {/* Unique AI Insight Box */}
                    <div className="bg-purple-50/50 rounded-xl p-5 border border-purple-100 relative overflow-hidden">
                        {isGenerating ? (
                            <div className="space-y-3">
                                <ThinkingIndicator message="AI กำลังวิเคราะห์แนวทางต่อสู้คดี..." />
                                <div className="h-2 w-3/4 bg-purple-200/50 rounded animate-pulse" />
                                <div className="h-2 w-1/2 bg-purple-200/50 rounded animate-pulse delay-75" />
                            </div>
                        ) : (
                            <>
                                <div className="absolute top-0 right-0 p-2 opacity-10">
                                    <Sparkles className="h-24 w-24 text-purple-600 rotate-12" />
                                </div>
                                <h4 className="flex items-center gap-2 text-sm font-bold text-purple-700 mb-2 uppercase tracking-wide relative z-10">
                                    <Sparkles className="h-4 w-4" /> ความเห็นทนาย (AI Strategy)
                                </h4>
                                <p className="text-purple-900 leading-relaxed text-sm relative z-10 font-medium">
                                    {item.lawyer_opinion}
                                </p>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </motion.div>
    );
};

export default function ResearchPage() {
    const router = useRouter();

    // UI State
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<ComparisonResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [statusMessage, setStatusMessage] = useState(''); // New: Real-time status
    const [error, setError] = useState<string | null>(null);
    const [page, setPage] = useState(0);
    const [hasMore, setHasMore] = useState(true);

    // PDF Viewer State
    const [selectedPdf, setSelectedPdf] = useState<string | null>(null);
    const [selectedCaseTitle, setSelectedCaseTitle] = useState<string>('');

    // Sidebar State
    const [isMobileOpen, setMobileOpen] = useState(false);
    const [isDesktopOpen, toggleDesktop] = useState(true);

    const performSearch = async (reset: boolean = true) => {
        if (!query.trim()) return;

        setLoading(true);
        setError(null);
        if (reset) setStatusMessage("กำลังเชื่อมต่อ Law5 Neural Network...");

        const targetPage = reset ? 0 : page + 1;
        if (reset) {
            setResults([]);
            setPage(0);
            setHasMore(true);
        } else {
            setPage(targetPage);
        }

        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
            const response = await fetch(`${apiUrl}/api/research`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query,
                    page: targetPage
                })
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.error || 'Research connection failed.');
            }

            if (!response.body) return;
            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n\n");
                buffer = lines.pop() || "";

                for (const line of lines) {
                    const eventMatch = line.match(/^event: (.*)$/m);
                    const dataMatch = line.match(/^data: (.*)$/m);

                    if (eventMatch && dataMatch) {
                        const eventType = eventMatch[1].trim();
                        const dataStr = dataMatch[1].trim();

                        if (eventType === "status") {
                            // Show server status update
                            const data = JSON.parse(dataStr);
                            setStatusMessage(data.message);
                        } else if (eventType === "result_item") {
                            const newItem = JSON.parse(dataStr);
                            setResults(prev => {
                                if (prev.some(p => p.case_id === newItem.case_id)) return prev;
                                return [...prev, newItem];
                            });
                            setStatusMessage(""); // Clear status when items arrive
                        } else if (eventType === "done") {
                            const data = JSON.parse(dataStr);
                            if (data.message === "No more results") {
                                setHasMore(false);
                            }
                            setLoading(false);
                        } else if (eventType === "error") {
                            console.error("Stream Error:", dataStr);
                        }
                    }
                }
            }
        } catch (err: any) {
            setError(err.message || 'Something went wrong');
        } finally {
            setLoading(false);
        }
    };

    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        performSearch(true);
    };

    return (
        <div className="flex h-screen bg-zinc-50/50 overflow-hidden font-sans">
            <ChatHistorySidebar
                className="border-r border-border/40 bg-white"
                onSelectConversation={(id) => { if (id) router.push(`/chat?cid=${id}`); }}
                isMobileOpen={isMobileOpen}
                onMobileClose={() => setMobileOpen(false)}
                isDesktopOpen={isDesktopOpen}
                toggleDesktop={() => toggleDesktop(!isDesktopOpen)}
            />

            <main className="flex-1 flex flex-col h-full relative w-full max-w-[100vw] overflow-hidden">
                <header className="h-16 border-b bg-white/80 backdrop-blur-sm sticky top-0 z-10 flex items-center px-4 md:px-6 justify-between shrink-0">
                    <div className="flex items-center gap-4">
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => toggleDesktop(!isDesktopOpen)}
                            className="hidden md:flex hover:bg-zinc-100 rounded-lg text-zinc-500"
                            title={isDesktopOpen ? "ซ่อนเมนู" : "แสดงเมนู"}
                        >
                            <PanelLeft className="h-5 w-5" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => router.push('/')} className="hover:bg-zinc-100 rounded-full">
                            <ArrowLeft className="h-5 w-5 text-zinc-600" />
                        </Button>
                        <h1 className="font-bold text-xl flex items-center gap-2 text-zinc-800">
                            Law5 <span className="text-purple-600 font-extrabold">Research</span>
                        </h1>
                    </div>
                </header>

                <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-8 scroll-smooth">
                    {/* Search Section */}
                    <div className="max-w-4xl mx-auto space-y-6">
                        <div className="text-center space-y-3 mb-10 mt-8">
                            <h2 className="text-4xl font-extrabold tracking-tight text-zinc-900">
                                ค้นหาฎีกาด้วย <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-indigo-600">AI Wisdom</span>
                            </h2>
                            <p className="text-lg text-zinc-500 max-w-2xl mx-auto">
                                เจาะลึกประเด็นกฎหมาย เปรียบเทียบคำพิพากษา และถอดบทเรียนกลยุทธ์คดี
                            </p>
                        </div>

                        <form onSubmit={handleSearchSubmit} className="relative group shadow-purple-500/5 rounded-2xl">
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                <Search className="h-6 w-6 text-zinc-400 group-focus-within:text-purple-600 transition-colors" />
                            </div>
                            <Input
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="ถามประเด็นกฎหมายของคุณที่นี่..."
                                className="pl-12 h-16 text-lg bg-white shadow-xl shadow-zinc-200/50 border-zinc-200 focus-visible:ring-purple-500 rounded-2xl transition-all"
                            />
                            <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                                <Button
                                    type="submit"
                                    disabled={loading || !query.trim()}
                                    className="h-10 rounded-xl bg-gray-900 hover:bg-black text-white px-6 font-medium shadow-lg hover:shadow-xl transition-all"
                                >
                                    {loading && page === 0 ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Sparkles className="h-4 w-4 mr-2" />}
                                    {loading && page === 0 ? 'Analyzing...' : 'Research'}
                                </Button>
                            </div>
                        </form>

                        {/* Real-time Status / Thinking Process */}
                        <AnimatePresence>
                            {statusMessage && (
                                <motion.div
                                    initial={{ opacity: 0, y: -10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0 }}
                                    className="flex items-center justify-center gap-3 text-purple-600 pt-2"
                                >
                                    <div className="h-1.5 w-1.5 rounded-full bg-purple-600 animate-bounce" />
                                    <div className="h-1.5 w-1.5 rounded-full bg-purple-600 animate-bounce delay-75" />
                                    <div className="h-1.5 w-1.5 rounded-full bg-purple-600 animate-bounce delay-150" />
                                    <span className="font-medium text-sm">{statusMessage}</span>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {error && (
                            <div className="p-4 rounded-xl bg-red-50 text-red-600 border border-red-200 flex items-center gap-3 text-sm">
                                <AlertCircle className="h-5 w-5" />
                                {error}
                            </div>
                        )}
                    </div>

                    {/* Results Feed */}
                    {results.length > 0 && (
                        <div className="max-w-5xl mx-auto pb-20">
                            <div className="flex items-center justify-between mb-4 px-2">
                                <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest">
                                    Research Results ({results.length})
                                </h3>
                            </div>

                            {/* Cards List */}
                            <div className="space-y-6">
                                {results.map((item, i) => (
                                    <CaseCard
                                        key={`${item.case_id}-${i}`}
                                        item={item}
                                        onOpenPdf={(url, id) => {
                                            setSelectedPdf(url);
                                            setSelectedCaseTitle(`คำพิพากษาศาลฎีกาที่ ${id}`);
                                        }}
                                    />
                                ))}
                            </div>

                            {/* Load More Button */}
                            {hasMore && (
                                <div className="mt-12 flex justify-center">
                                    <Button
                                        variant="outline"
                                        size="lg"
                                        onClick={() => performSearch(false)}
                                        disabled={loading}
                                        className="gap-2 min-w-[240px] h-12 rounded-full border-zinc-300 text-zinc-600 hover:text-purple-600 hover:border-purple-300 hover:bg-purple-50 transition-all shadow-sm"
                                    >
                                        {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                                        โหลดข้อมูลเพิ่มเติม (Load More)
                                    </Button>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* PDF Viewer Dialog */}
                <Dialog open={!!selectedPdf} onOpenChange={(open) => !open && setSelectedPdf(null)}>
                    <DialogContent className="max-w-6xl h-[95vh] flex flex-col p-0 gap-0 overflow-hidden rounded-2xl">
                        <DialogHeader className="px-6 py-4 border-b bg-zinc-50/80 backdrop-blur shrink-0 flex flex-row items-center justify-between">
                            <DialogTitle className="flex items-center gap-3 text-zinc-800">
                                <span className="bg-purple-100 p-2 rounded-lg">
                                    <BookOpen className="h-5 w-5 text-purple-600" />
                                </span>
                                {selectedCaseTitle}
                            </DialogTitle>
                        </DialogHeader>
                        <div className="flex-1 bg-zinc-100 relative">
                            {selectedPdf && (
                                <iframe
                                    src={`${selectedPdf}#toolbar=0`}
                                    className="w-full h-full border-none"
                                    title="PDF Viewer"
                                />
                            )}
                        </div>
                    </DialogContent>
                </Dialog>
            </main>
        </div>
    );
}
