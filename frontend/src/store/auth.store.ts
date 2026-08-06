import { create } from "zustand";

/**
 * Auth UI state. Real credentials live in httpOnly cookies set by the API.
 * `ridecare_session` is only a client hint for routing (cleared on 401/logout).
 */
const SESSION_KEY = "ridecare_session";

interface AuthState {
    isAuthenticated: boolean;
    setAuthenticated: () => void;
    clearSession: () => void;
}

function hasSessionHint(): boolean {
    return localStorage.getItem(SESSION_KEY) === "1";
}

function clearLegacyTokenKeys() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("ridecare-auth");
}

const useAuthStore = create<AuthState>((set) => ({
    isAuthenticated: hasSessionHint(),

    setAuthenticated: () => {
        clearLegacyTokenKeys();
        localStorage.setItem(SESSION_KEY, "1");
        set({ isAuthenticated: true });
    },

    clearSession: () => {
        clearLegacyTokenKeys();
        localStorage.removeItem(SESSION_KEY);
        set({ isAuthenticated: false });
    },
}));

export default useAuthStore;
