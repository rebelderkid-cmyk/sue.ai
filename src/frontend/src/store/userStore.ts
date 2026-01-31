import { create } from 'zustand';
import { User } from 'firebase/auth';

interface UserState {
    user: User | null;
    isLoading: boolean;
    setUser: (user: User | null) => void;
    setLoading: (loading: boolean) => void;
    logout: () => void;
}

export const useUserStore = create<UserState>((set) => ({
    user: null,
    isLoading: true,
    setUser: (user) => set({ user, isLoading: false }),
    setLoading: (loading) => set({ isLoading: loading }),
    logout: () => set({ user: null, isLoading: false }),
}));
