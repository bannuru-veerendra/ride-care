import { useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { authApi } from "@/api/auth.api";
import useAuthStore from "@/store/auth.store";

/**
 * Clears the local session and returns the user to login.
 * Best-effort revoke of the refresh token on the backend.
 */
export const useLogout = () => {
    const navigate = useNavigate();
    const clearToken = useAuthStore((state) => state.clearToken);
    const queryClient = useQueryClient();

    return useCallback(async () => {
        const refreshToken = localStorage.getItem("refresh_token");
        if (refreshToken) {
            try {
                await authApi.logout(refreshToken);
            } catch {
                // Still clear local session if revoke fails
            }
        }
        queryClient.clear();
        clearToken();
        toast.success("Logged out successfully");
        navigate("/login");
    }, [clearToken, navigate, queryClient]);
};
