import { create } from 'zustand';

interface UserState {
  userId: number;
  soundEnabled: boolean;
  setUserId: (id: number) => void;
  toggleSound: () => void;
}

export const useUserStore = create<UserState>((set) => ({
  userId: 1,
  soundEnabled: true,
  setUserId: (id: number) => set({ userId: id }),
  toggleSound: () => set((state) => ({ soundEnabled: !state.soundEnabled })),
}));
