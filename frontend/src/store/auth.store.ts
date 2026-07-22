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
    setTokens: (accessToken: string, refreshToken: string) => void;
    clearToken: () => void;
}

const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            token: null,
            isAuthenticated: false,

            setTokens: (accessToken: string, refreshToken: string) => {
                localStorage.setItem("access_token", accessToken);
                localStorage.setItem("refresh_token", refreshToken);
                set({ token: accessToken, isAuthenticated: true });
            },

            clearToken: () => {
                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
                set({ token: null, isAuthenticated: false });
            },
        }),
        {
            name: "ridecare-auth", // localStorage key
        }
    )
);

export default useAuthStore;
