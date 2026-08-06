import { useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { authApi } from "@/api/auth.api";
import useAuthStore from "@/store/auth.store";

/**
 * Clears the local session and returns the user to login.
 * Best-effort revoke of the refresh token cookie on the backend.
 */
export const useLogout = () => {
    const navigate = useNavigate();
    const clearSession = useAuthStore((state) => state.clearSession);
    const queryClient = useQueryClient();

    return useCallback(async () => {
        try {
            await authApi.logout();
        } catch {
            // Still clear local session if revoke fails
        }
        queryClient.clear();
        clearSession();
        toast.success("Logged out successfully");
        navigate("/login");
    }, [clearSession, navigate, queryClient]);
};
