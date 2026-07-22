import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { authApi } from "@/api/auth.api";
import { getApiErrorMessage } from "@/lib/api-error";
import useAuthStore from "@/store/auth.store";
import type { LoginFormValues } from "../types";

/**
 * Handles user login.
 * Stores tokens from the backend and redirects on success.
 */
export const useLogin = () => {
    const navigate = useNavigate();
    const setTokens = useAuthStore((state) => state.setTokens);

    return useMutation({
        mutationFn: (values: LoginFormValues) => authApi.login(values),
        onSuccess: (data) => {
            setTokens(data.access_token, data.refresh_token);
            navigate("/dashboard");
        },
        onError: (error) => {
            toast.error(
                getApiErrorMessage(error, "Login failed. Please try again."),
                { id: "login-error" }
            );
        },
    });
};
