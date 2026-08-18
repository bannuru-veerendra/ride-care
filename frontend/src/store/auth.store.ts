import { create } from "zustand";

import type { User } from "@/types";

/**
 * Auth UI state. Real credentials live in httpOnly cookies set by the API.
 * `ridecare_session` is only a client hint for routing (cleared on 401/logout).
 * Name/email are a display hint so the navbar is not "Account" until /users/me runs.
 */
const SESSION_KEY = "ridecare_session";
const PROFILE_HINT_KEY = "ridecare_profile";

export type ProfileHint = Pick<User, "full_name" | "email">;

interface AuthState {
    isAuthenticated: boolean;
    profile: ProfileHint | null;
    setAuthenticated: () => void;
    setProfileHint: (profile: ProfileHint) => void;
    clearSession: () => void;
}

function hasSessionHint(): boolean {
    return localStorage.getItem(SESSION_KEY) === "1";
}

function readProfileHint(): ProfileHint | null {
    try {
        const raw = localStorage.getItem(PROFILE_HINT_KEY);
        if (!raw) return null;
        const parsed = JSON.parse(raw) as Partial<ProfileHint>;
        if (
            typeof parsed.full_name === "string" &&
            parsed.full_name.trim() &&
            typeof parsed.email === "string"
        ) {
            return { full_name: parsed.full_name, email: parsed.email };
        }
    } catch {
        // Ignore bad JSON from older sessions
    }
    return null;
}

function clearLegacyTokenKeys() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("ridecare-auth");
}

const useAuthStore = create<AuthState>((set) => ({
    isAuthenticated: hasSessionHint(),
    profile: readProfileHint(),

    setAuthenticated: () => {
        clearLegacyTokenKeys();
        localStorage.setItem(SESSION_KEY, "1");
        set({ isAuthenticated: true });
    },

    setProfileHint: (profile) => {
        localStorage.setItem(PROFILE_HINT_KEY, JSON.stringify(profile));
        set({ profile });
    },

    clearSession: () => {
        clearLegacyTokenKeys();
        localStorage.removeItem(SESSION_KEY);
        localStorage.removeItem(PROFILE_HINT_KEY);
        set({ isAuthenticated: false, profile: null });
    },
}));

export default useAuthStore;
