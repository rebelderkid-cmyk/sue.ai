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

    // Actions
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

                    const newMessage: Message = {
                        ...msg,
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
            name: 'sue-ai-chat-history', // key in local storage
            storage: createJSONStorage(() => localStorage),
        }
    )
);
