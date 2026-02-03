// Last Updated: 2026-01-29 (Force Deploy)
import * as React from 'react';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Plus, MessageSquare, Trash2, Clock, X, PanelLeftClose } from 'lucide-react';
import { useChatStore } from '@/store/chatStore';

export function ChatHistorySidebar({
    className,
    onSelectConversation,
    isMobileOpen,
    onMobileClose,
    isDesktopOpen,
    toggleDesktop
}: {
    className?: string;
    onSelectConversation: (id: string | null) => void;
    isMobileOpen: boolean;
    onMobileClose: () => void;
    isDesktopOpen: boolean;
    toggleDesktop: () => void;
}) {
    const router = useRouter();
    const { sessions, activeSessionId, createSession, setActiveSession, deleteSession } = useChatStore();

    // Sort sessions by updatedAt (descending)
    const sortedSessions = React.useMemo(() => {
        return Object.values(sessions).sort((a, b) => b.updatedAt - a.updatedAt);
    }, [sessions]);

    const handleNewChat = () => {
        const newId = createSession();
        router.push(`/chat?cid=${newId}`);
    };

    const handleSelect = (id: string) => {
        setActiveSession(id);
        onSelectConversation(id);
        router.push(`/chat?cid=${id}`);
    }

    const handleDelete = (e: React.MouseEvent, id: string) => {
        e.stopPropagation();
        if (confirm('คุณต้องการลบประวัติการสนทนานี้ใช่หรือไม่?')) {
            deleteSession(id);
            if (activeSessionId === id) {
                router.push('/chat');
            }
        }
    }

    return (
        <>
            {/* Mobile Backdrop */}
            <div
                className={cn(
                    "fixed inset-0 bg-black/50 z-40 md:hidden backdrop-blur-sm transition-opacity duration-300",
                    isMobileOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
                )}
                onClick={onMobileClose}
            />

            {/* Sidebar Container */}
            <div className={cn(
                "fixed inset-y-0 left-0 z-50 bg-muted/95 backdrop-blur-xl border-r transition-all duration-300 ease-in-out flex flex-col md:relative md:z-auto shrink-0",
                // Mobile: Slide in/out
                isMobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0",
                // Desktop: Collapse width
                isDesktopOpen ? "w-72 lg:w-80" : "md:w-0 md:border-none md:overflow-hidden",
                // Mobile width fixed
                "w-72",
                className
            )}>
                {/* Header: Logo & Collapse Action */}
                <div className="flex items-center justify-between p-4 pb-2">
                    <div className="flex items-center gap-2">
                        <div className="h-8 w-8 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold shadow-md">
                            L5
                        </div>
                        <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-800 to-purple-800">
                            Law5.ai
                        </span>
                    </div>

                    <div className="flex items-center gap-1">
                        {/* Mobile Close */}
                        <Button
                            variant="ghost"
                            size="icon"
                            className="md:hidden text-zinc-400"
                            onClick={onMobileClose}
                        >
                            <X className="h-5 w-5" />
                        </Button>

                        {/* Desktop Collapse */}
                        <Button
                            variant="ghost"
                            size="icon"
                            className="hidden md:flex text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100 rounded-lg"
                            onClick={toggleDesktop}
                            title="ซ่อนเมนู"
                        >
                            <PanelLeftClose className="h-5 w-5" />
                        </Button>
                    </div>
                </div>

                <div className="space-y-4 px-3 pb-4 flex-1 overflow-y-auto overflow-x-hidden no-scrollbar mt-2">

                    <Button onClick={handleNewChat} className="w-full justify-start gap-2 mb-2 shadow-sm bg-indigo-600 hover:bg-indigo-700 text-white border-transparent hover:border-indigo-500 rounded-xl py-6">
                        <Plus size={18} /> New Chat
                    </Button>

                    <Button onClick={() => router.push('/search')} variant="outline" className="w-full justify-start gap-2 mb-6 shadow-none border-dashed border-zinc-300 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 rounded-xl py-6 text-zinc-600 dark:text-zinc-300">
                        <span className="text-xl">⚖️</span> Research Tools
                    </Button>

                    <h2 className="mb-2 px-2 text-[10px] font-semibold tracking-widest text-muted-foreground uppercase flex items-center gap-2 opacity-70">
                        <Clock size={12} /> ประวัติการค้นคว้า
                    </h2>

                    <div className="space-y-1.5 ml-1">
                        {sortedSessions.length === 0 ? (
                            <div className="px-4 py-8 text-center text-sm text-muted-foreground bg-muted/30 rounded-lg border border-dashed border-border/50">
                                ยังไม่มีประวัติการใช้งาน
                                <br />
                                <span className="text-xs opacity-70">เริ่มถามคำถามแรกได้เลย!</span>
                            </div>
                        ) : (
                            sortedSessions.map((conv) => (
                                <div
                                    key={conv.id}
                                    className={cn(
                                        "group relative flex items-center w-full rounded-lg transition-all duration-200",
                                        activeSessionId === conv.id
                                            ? "bg-zinc-100 dark:bg-zinc-800/80 shadow-sm border border-zinc-200/50 dark:border-zinc-700/50"
                                            : "hover:bg-zinc-50 dark:hover:bg-zinc-800/40"
                                    )}
                                >
                                    <Button
                                        variant="ghost"
                                        className={cn(
                                            "w-full justify-start font-normal h-auto py-3 pl-3 pr-7 hover:bg-transparent relative text-left rounded-lg truncate",
                                            activeSessionId === conv.id
                                                ? "text-zinc-900 dark:text-zinc-100 font-medium"
                                                : "text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-200 transition-colors"
                                        )}
                                        onClick={() => handleSelect(conv.id)}
                                        title={conv.title || "บทสนทนาใหม่"}
                                    >
                                        <MessageSquare
                                            className={cn(
                                                "mr-3 h-4 w-4 shrink-0 transition-colors duration-200",
                                                activeSessionId === conv.id
                                                    ? "text-indigo-600 dark:text-indigo-400"
                                                    : "text-zinc-400 group-hover:text-zinc-600 dark:text-zinc-500 dark:group-hover:text-zinc-300"
                                            )}
                                        />
                                        <span className="truncate block max-w-[180px]">
                                            {conv.title || "บทสนทนาใหม่"}
                                        </span>
                                    </Button>

                                    <button
                                        onClick={(e) => handleDelete(e, conv.id)}
                                        className={cn(
                                            "absolute right-2 p-1.5 rounded-md transition-all duration-200 z-10",
                                            "opacity-0 group-hover:opacity-100 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:text-red-400",
                                            activeSessionId === conv.id && "group-hover:opacity-100"
                                        )}
                                        title="ลบ"
                                    >
                                        <Trash2 size={13} />
                                    </button>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Footer / Privacy Note */}
                <div className={cn(
                    "p-4 text-[10px] text-center text-muted-foreground opacity-50 border-t transition-opacity duration-200",
                    !isDesktopOpen && "md:opacity-0"
                )}>
                    ข้อมูลถูกเก็บใน Browser ของคุณ
                    <br />(Local Storage)
                </div>
            </div>
        </>
    );
}
