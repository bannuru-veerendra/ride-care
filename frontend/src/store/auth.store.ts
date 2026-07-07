import { create } from "zustand";
import { persist } from "zustand/middleware";

/**
 * Global authentication state.
 * Persisted to localStorage so the user stays logged in
 * across page refreshes.
 */
interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  setToken: (token: string) => void;
  clearToken: () => void;
}

const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      isAuthenticated: false,

      setToken: (token: string) => {
        localStorage.setItem("access_token", token);
        set({ token, isAuthenticated: true });
      },

      clearToken: () => {
        localStorage.removeItem("access_token");
        set({ token: null, isAuthenticated: false });
      },
    }),
    {
      name: "ridecare-auth", // localStorage key
    }
  )
);

export default useAuthStore;
