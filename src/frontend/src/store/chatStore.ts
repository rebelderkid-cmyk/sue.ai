import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export interface Source {
    id: string;
    year: string;
    outcome: string;
    text: string;
    pdf_url?: string;
    source?: string;
    title?: string;
    snippet?: string;
    filename?: string;
    content?: string;
}

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    sources?: Source[];
    createdAt: number;
}

export interface ChatSession {
    id: string;
    title: string;
    messages: Message[];
    updatedAt: number;
}

interface ChatState {
    sessions: Record<string, ChatSession>;
    activeSessionId: string | null;

    // UI State
    isMobileOpen: boolean;
    isDesktopOpen: boolean;

    // Actions
    setMobileOpen: (open: boolean) => void;
    toggleDesktop: () => void;
    createSession: () => string;
    setActiveSession: (id: string | null) => void;
    addMessage: (sessionId: string, message: Omit<Message, 'id' | 'createdAt'>) => void;
    updateSessionTitle: (sessionId: string, title: string) => void;
    deleteSession: (sessionId: string) => void;
    clearHistory: () => void;
}

export const useChatStore = create<ChatState>()(
    persist(
        (set, get) => ({
            sessions: {},
            activeSessionId: null,


            // UI State Defaults (Updated for Cloud Build)
            isMobileOpen: false,
            isDesktopOpen: true,

            setMobileOpen: (open) => set({ isMobileOpen: open }),
            toggleDesktop: () => set((state) => ({ isDesktopOpen: !state.isDesktopOpen })),

            createSession: () => {
                const id = crypto.randomUUID();
                const newSession: ChatSession = {
                    id,
                    title: 'New Chat',
                    messages: [],
                    updatedAt: Date.now(),
                };
                set((state) => ({
                    sessions: { [id]: newSession, ...state.sessions },
                    activeSessionId: id
                }));
                return id;
            },

            setActiveSession: (id) => {
                set({ activeSessionId: id });
            },

            addMessage: (sessionId, msg) => {
                set((state) => {
                    const session = state.sessions[sessionId];
                    if (!session) return state;

                    // OPTIMIZATION: Reduce payload size for LocalStorage efficiency
                    // 1. If sources exist, strip heavy 'content' fields
                    let optimizedSources = msg.sources;
                    if (optimizedSources && optimizedSources.length > 0) {
                        optimizedSources = optimizedSources.map(s => ({
                            ...s,
                            content: undefined, // Don't save full content text
                            snippet: s.snippet ? s.snippet.slice(0, 200) + '...' : undefined, // Truncate snippet
                            text: s.text ? s.text.slice(0, 100) + '...' : '' // Truncate raw text match
                        }));
                    }

                    const newMessage: Message = {
                        ...msg,
                        sources: optimizedSources,
                        id: crypto.randomUUID(),
                        createdAt: Date.now(),
                    };

                    const updatedSession = {
                        ...session,
                        messages: [...session.messages, newMessage],
                        updatedAt: Date.now(),
                        // Auto-generate title from first user message if user hasn't set custom title
                        // (Simple logic: use first 30 chars)
                        title: session.messages.length === 0 && msg.role === 'user'
                            ? (msg.content.slice(0, 30) + (msg.content.length > 30 ? '...' : ''))
                            : session.title
                    };

                    // Re-sort sessions by updatedAt is tricky in an object, but we'll handle sorting in UI
                    return {
                        sessions: {
                            ...state.sessions,
                            [sessionId]: updatedSession
                        }
                    };
                });
            },

            updateSessionTitle: (sessionId, title) => {
                set((state) => {
                    const session = state.sessions[sessionId];
                    if (!session) return state;
                    return {
                        sessions: {
                            ...state.sessions,
                            [sessionId]: { ...session, title }
                        }
                    };
                });
            },

            deleteSession: (sessionId) => {
                set((state) => {
                    const newSessions = { ...state.sessions };
                    delete newSessions[sessionId];
                    return {
                        sessions: newSessions,
                        activeSessionId: state.activeSessionId === sessionId ? null : state.activeSessionId
                    };
                });
            },

            clearHistory: () => set({ sessions: {}, activeSessionId: null }),
        }),
        {
            name: 'sue-ai-chat-history',
            storage: createJSONStorage(() => {
                // Custom Safe Storage Wrapper with Auto-Cleanup
                return {
                    getItem: (name) => {
                        const str = localStorage.getItem(name);
                        return str ? JSON.parse(str) : null;
                    },
                    setItem: (name, value) => {
                        try {
                            localStorage.setItem(name, JSON.stringify(value));
                        } catch (e) {
                            if (e instanceof DOMException && (e.name === 'QuotaExceededError' || e.name === 'NS_ERROR_DOM_QUOTA_REACHED')) {
                                console.warn('⚠️ LocalStorage Full! Attempting Auto-Cleanup...');

                                // Clean up Logic:
                                // 1. Try to parse current value state to identify old sessions
                                try {
                                    const state = value as any;
                                    if (state && state.state && state.state.sessions) {
                                        const sessions = state.state.sessions;
                                        const sortedIds = Object.keys(sessions).sort((a, b) =>
                                            sessions[a].updatedAt - sessions[b].updatedAt
                                        );

                                        // Delete oldest 20% of sessions
                                        const deleteCount = Math.max(1, Math.floor(sortedIds.length * 0.2));

                                        console.log(`🧹 Deleting ${deleteCount} old sessions to free up space.`);
                                        for (let i = 0; i < deleteCount; i++) {
                                            delete sessions[sortedIds[i]];
                                        }

                                        // Retry saving
                                        try {
                                            localStorage.setItem(name, JSON.stringify(state));
                                            console.log('✅ Auto-Cleanup Successful. Data saved.');
                                        } catch (retryErr) {
                                            console.error('❌ Auto-Cleanup failed to free enough space.', retryErr);
                                            // Last Resort: Clear everything if critical (or handle gracefully)
                                            // For now, prevent crash by doing nothing (data loss warning)
                                        }
                                    }
                                } catch (cleanupErr) {
                                    console.error('Failed to perform cleanup logic', cleanupErr);
                                }
                            } else {
                                console.error('LocalStorage Save Error:', e);
                            }
                        }
                    },
                    removeItem: (name) => localStorage.removeItem(name),
                };
            }),
        }
    )
);
