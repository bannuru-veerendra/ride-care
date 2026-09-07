import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { authApi } from "@/api/auth.api";
import { getApiErrorMessage } from "@/lib/api-error";

/** Request a password-reset email (generic success message). */
export const useForgotPassword = () => {
    return useMutation({
        mutationFn: (email: string) => authApi.forgotPassword(email),
        onSuccess: (data) => {
            toast.success(data.message, { id: "forgot-password" });
        },
        onError: (error) => {
            toast.error(
                getApiErrorMessage(error, "Could not send reset email."),
                { id: "forgot-password-error" }
            );
        },
    });
};
