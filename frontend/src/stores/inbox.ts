/** Inbox store — unprocessed document count. */
import { create } from 'zustand';

interface InboxState {
  count: number;
  setCount: (count: number) => void;
}

export const useInboxStore = create<InboxState>((set) => ({
  count: 0,
  setCount: (count) => set({ count }),
}));
