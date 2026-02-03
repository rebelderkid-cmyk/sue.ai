"use client";

import * as React from 'react';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Loader2, ArrowLeft, BookOpen, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ChatHistorySidebar } from '@/components/ChatHistorySidebar';
import { useChatStore } from '@/store/chatStore';

interface ComparisonResult {
    case_id: string;
    year: string;
    facts: string;
    legal_issue: string;
    ruling: string;
    reasoning: string;
    lawyer_opinion: string;
    pdf_url?: string;
}

export default function ResearchPage() {
    const router = useRouter();
    const { isMobileOpen, isDesktopOpen, setMobileOpen, toggleDesktop } = useChatStore();

    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<ComparisonResult[]>([]);
    const [error, setError] = useState<string | null>(null);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setError(null);
        setResults([]);

        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
            const res = await fetch(`${apiUrl}/api/research`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            });

            if (!res.ok) {
                throw new Error('Research failed. Please try again.');
            }

            const data = await res.json();
            if (data.results) {
                setResults(data.results);
            }
        } catch (err: any) {
            setError(err.message || 'Something went wrong');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex h-screen bg-background overflow-hidden font-sans">
            {/* Reuse Sidebar Logic for consistency */}
            <ChatHistorySidebar
                className="border-r border-border/40"
                onSelectConversation={(id) => {
                    if (id) router.push(`/chat?cid=${id}`);
                }}
                isMobileOpen={isMobileOpen}
                onMobileClose={() => setMobileOpen(false)}
                isDesktopOpen={isDesktopOpen}
                toggleDesktop={toggleDesktop}
            />

            {/* Main Content */}
            <main className="flex-1 flex flex-col h-full relative w-full max-w-[100vw] overflow-hidden">
                {/* Header */}
                <header className="h-14 border-b flex items-center px-4 bg-muted/30 shrink-0 gap-2">
                    <Button variant="ghost" size="icon" onClick={() => router.push('/chat')}>
                        <ArrowLeft className="h-5 w-5" />
                    </Button>
                    <h1 className="font-semibold text-lg flex items-center gap-2">
                        <BookOpen className="h-5 w-5 text-purple-600" />
                        Research Mode (Beta)
                    </h1>
                </header>

                {/* Content Area */}
                <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">

                    {/* Search Section */}
                    <div className="max-w-3xl mx-auto space-y-4">
                        <div className="text-center space-y-2 mb-8">
                            <h2 className="text-3xl font-bold tracking-tight">ค้นหาและเปรียบเทียบฎีกา</h2>
                            <p className="text-muted-foreground">
                                พิมพ์ประเด็นกฎหมายของคุณ ระบบจะดึงฎีกาที่เกี่ยวข้องที่สุด 5 คดีมาสร้างตารางเปรียบเทียบให้ทันที
                            </p>
                        </div>

                        <form onSubmit={handleSearch} className="relative group">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <Search className="h-5 w-5 text-muted-foreground group-focus-within:text-purple-600 transition-colors" />
                            </div>
                            <Input
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="เช่น การเลิกจ้างเพราะมาสาย ผิดไหมต้องจ่ายค่าชดเชยไหม?"
                                className="pl-10 h-12 text-lg shadow-sm border-muted-foreground/20 focus-visible:ring-purple-500 rounded-xl"
                            />
                            <div className="absolute inset-y-0 right-0 pr-2 flex items-center">
                                <Button
                                    type="submit"
                                    disabled={loading || !query.trim()}
                                    className="h-8 rounded-lg bg-purple-600 hover:bg-purple-700 text-white"
                                >
                                    {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Analyze'}
                                </Button>
                            </div>
                        </form>

                        {error && (
                            <div className="p-4 rounded-lg bg-red-50 text-red-600 border border-red-200 flex items-center gap-2 text-sm">
                                <AlertCircle className="h-4 w-4" />
                                {error}
                            </div>
                        )}
                    </div>

                    {/* Result Table */}
                    {results.length > 0 && (
                        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <Card className="border-none shadow-md bg-card/50 backdrop-blur-sm">
                                <CardHeader className="pb-4 border-b">
                                    <div className="flex items-center justify-between">
                                        <CardTitle className="text-xl text-purple-800">Top 5 Selected Cases</CardTitle>
                                        <span className="text-xs text-muted-foreground bg-secondary px-2 py-1 rounded-full">Sorted by Relevance & Recency</span>
                                    </div>
                                    <CardDescription>
                                        ข้อมูลจากการวิเคราะห์ฎีกาโดย AI พร้อมความเห็นสำหรับทนายความ
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="p-0 overflow-x-auto">
                                    <Table>
                                        <TableHeader className="bg-muted/50">
                                            <TableRow>
                                                <TableHead className="w-[120px] font-bold">เลขฎีกา/ปี</TableHead>
                                                <TableHead className="min-w-[200px] font-bold">ข้อเท็จจริง (Facts)</TableHead>
                                                <TableHead className="min-w-[200px] font-bold">ประเด็นกฎหมาย & เหตุผล</TableHead>
                                                <TableHead className="min-w-[250px] font-bold text-purple-700">คำวินิจฉัย & ความเห็นทนาย</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {results.map((item, index) => (
                                                <TableRow key={index} className="hover:bg-muted/30 align-top group transition-colors">
                                                    <TableCell className="font-medium align-top">
                                                        {item.pdf_url ? (
                                                            <a 
                                                                href={item.pdf_url} 
                                                                target="_blank" 
                                                                rel="noopener noreferrer" 
                                                                className="text-purple-600 hover:text-purple-800 hover:underline text-base font-bold whitespace-nowrap flex items-center gap-1"
                                                            >
                                                                {item.case_id}
                                                                <BookOpen className="h-3 w-3 inline" />
                                                            </a>
                                                        ) : (
                                                            <div className="text-purple-600 text-base font-bold whitespace-nowrap">{item.case_id}</div>
                                                        )}
                                                        <div className="text-muted-foreground text-xs mt-1 bg-muted px-1.5 py-0.5 rounded w-fit">{item.year}</div>
                                                    </TableCell>
                                                    <TableCell className="align-top leading-relaxed text-sm text-foreground/90">
                                                        {item.facts}
                                                    </TableCell>
                                                    <TableCell className="align-top leading-relaxed text-sm">
                                                        <div className="font-medium mb-2 text-foreground">{item.legal_issue}</div>
                                                        <div className="text-xs text-muted-foreground bg-secondary/30 p-2 rounded border border-border/50">
                                                            <span className="font-semibold text-foreground/70">💡 เหตุผล:</span> {item.reasoning}
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="align-top text-sm">
                                                        <div className="font-medium text-foreground/90 bg-purple-50/50 p-2 rounded-t border-t border-x border-purple-100/50">
                                                            {item.ruling}
                                                        </div>
                                                        {item.lawyer_opinion && (
                                                            <div className="bg-purple-100/40 p-2 rounded-b border border-purple-100 text-purple-900 text-xs">
                                                                <div className="flex gap-1 mb-1 font-bold items-center text-purple-700 uppercase tracking-wider text-[10px]">
                                                                    <span>👨‍⚖️ Lawyer's Note</span>
                                                                </div>
                                                                <span className="italic">"{item.lawyer_opinion}"</span>
                                                            </div>
                                                        )}
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                </CardContent>
                            </Card>
                        </div>
                    )}

                    {loading && (
                        <div className="flex flex-col items-center justify-center py-20 space-y-4 text-muted-foreground animate-pulse">
                            <Loader2 className="h-10 w-10 animate-spin text-purple-600" />
                            <p className="text-lg font-medium text-foreground/80">กำลังวิเคราะห์ฎีกา...</p>
                            <p className="text-sm">คัดเลือก 5 คดีที่น่าสนใจที่สุดจากฐานข้อมูล</p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
