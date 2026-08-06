import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { authApi } from "@/api/auth.api";
import { getApiErrorMessage } from "@/lib/api-error";
import useAuthStore from "@/store/auth.store";
import type { LoginFormValues } from "../types";

/**
 * Handles user login.
 * Server sets httpOnly cookies; we only mark the UI session as authenticated.
 */
export const useLogin = () => {
    const navigate = useNavigate();
    const setAuthenticated = useAuthStore((state) => state.setAuthenticated);

    return useMutation({
        mutationFn: (values: LoginFormValues) => authApi.login(values),
        onSuccess: () => {
            setAuthenticated();
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
