import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { authApi } from "@/api/auth.api";
import { getApiErrorMessage } from "@/lib/api-error";

type ResetPasswordPayload = {
    token: string;
    new_password: string;
    confirm_password: string;
};

/** Consume a reset token and set a new password.
 * Success toast lives on LoginPage (?reset=true) to avoid double toasts.
 */
export const useResetPassword = () => {
    return useMutation({
        mutationFn: (payload: ResetPasswordPayload) =>
            authApi.resetPassword(payload),
        onError: (error) => {
            toast.error(
                getApiErrorMessage(
                    error,
                    "Reset link is invalid or expired."
                ),
                { id: "reset-password-error" }
            );
        },
    });
};
