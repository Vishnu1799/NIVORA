import { create } from 'zustand';

export const useCartStore = create((set, get) => ({
  items: [],
  addItem: (product) => {
    const existing = get().items.find((i) => i.id === product.id);
    if (existing) {
      set({ items: get().items.map((i) => i.id === product.id ? { ...i, qty: i.qty + 1 } : i) });
    } else {
      set({ items: [...get().items, { ...product, qty: 1 }] });
    }
  },
  updateQty: (id, qty) => {
    if (qty <= 0) set({ items: get().items.filter((i) => i.id !== id) });
    else set({ items: get().items.map((i) => i.id === id ? { ...i, qty } : i) });
  },
  removeItem: (id) => set({ items: get().items.filter((i) => i.id !== id) }),
  clearCart: () => set({ items: [] }),
  getTotal: () => get().items.reduce((s, i) => s + i.price * i.qty, 0),
  getCount: () => get().items.reduce((s, i) => s + i.qty, 0),
}));
