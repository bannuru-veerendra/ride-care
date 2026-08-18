import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { usersApi } from "@/api/users.api";
import { getApiErrorMessage } from "@/lib/api-error";
import useAuthStore from "@/store/auth.store";
import type {
    UpdatePasswordPayload,
    UpdateProfilePayload,
} from "../types";

export const usersKeys = {
    me: ["users", "me"] as const,
};

/** Fetch the current authenticated user's profile */
export const useCurrentUser = (options?: { enabled?: boolean }) => {
    return useQuery({
        queryKey: usersKeys.me,
        queryFn: usersApi.getMe,
        enabled: options?.enabled ?? true,
    });
};

/** Update name and/or email */
export const useUpdateProfile = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (payload: UpdateProfilePayload) => usersApi.updateMe(payload),
        onSuccess: (data) => {
            queryClient.setQueryData(usersKeys.me, data);
        },
    });
};

/**
 * Change password and revoke all sessions.
 * User must log in again afterward.
 */
export const useUpdatePassword = () => {
    const navigate = useNavigate();
    const clearSession = useAuthStore((state) => state.clearSession);
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (payload: UpdatePasswordPayload) =>
            usersApi.updatePassword(payload),
        onSuccess: () => {
            queryClient.clear();
            clearSession();
            navigate("/login");
        },
        onError: (error) => {
            toast.error(
                getApiErrorMessage(error, "Failed to change password"),
                { id: "password-update-error" }
            );
        },
    });
};
