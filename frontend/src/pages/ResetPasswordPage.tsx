import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/common/PasswordInput";
import AuthPageShell from "@/components/common/AuthPageShell";
import { useResetPassword } from "@/features/auth/hooks/useResetPassword";
import {
    resetPasswordSchema,
    type ResetPasswordSchema,
} from "@/features/auth/schemas";

/**
 * Public route opened from the password-reset email link.
 */
export default function ResetPasswordPage() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const token = searchParams.get("token") ?? "";
    const { mutate: resetPassword, isPending } = useResetPassword();
    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<ResetPasswordSchema>({
        resolver: zodResolver(resetPasswordSchema),
        reValidateMode: "onBlur",
    });

    if (!token) {
        return (
            <AuthPageShell
                logoTo="/login"
                title="Reset password"
                subtitle="This link is missing a reset token"
            >
                <p className="mt-4 text-sm text-destructive">
                    Missing reset token. Request a new link from the login page.
                </p>
                <Link
                    to="/forgot-password"
                    className="mt-4 inline-flex h-8 w-full items-center justify-center rounded-lg bg-brand px-2.5 text-sm font-medium text-brand-foreground hover:bg-brand/90"
                >
                    Request reset link
                </Link>
            </AuthPageShell>
        );
    }

    return (
        <AuthPageShell
            logoTo="/login"
            title="Choose a new password"
            subtitle="Pick something strong you have not used here before"
        >
            <form
                onSubmit={handleSubmit((data) =>
                    resetPassword(
                        {
                            token,
                            new_password: data.new_password,
                            confirm_password: data.confirm_password,
                        },
                        {
                            onSuccess: () => {
                                navigate("/login?reset=true", { replace: true });
                            },
                        }
                    )
                )}
                className="mt-4 space-y-3"
                noValidate
            >
                <div className="space-y-1.5">
                    <Label htmlFor="new_password">New password</Label>
                    <PasswordInput
                        id="new_password"
                        placeholder="New password"
                        autoComplete="new-password"
                        className="border-white/15 bg-white/5"
                        {...register("new_password")}
                    />
                    {errors.new_password && (
                        <p className="text-sm text-destructive">
                            {errors.new_password.message}
                        </p>
                    )}
                </div>

                <div className="space-y-1.5">
                    <Label htmlFor="confirm_password">Confirm password</Label>
                    <PasswordInput
                        id="confirm_password"
                        placeholder="Confirm password"
                        autoComplete="new-password"
                        className="border-white/15 bg-white/5"
                        {...register("confirm_password")}
                    />
                    {errors.confirm_password && (
                        <p className="text-sm text-destructive">
                            {errors.confirm_password.message}
                        </p>
                    )}
                </div>

                <Button
                    type="submit"
                    className="w-full bg-brand text-brand-foreground hover:bg-brand/90"
                    disabled={isPending}
                >
                    {isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                        "Update password"
                    )}
                </Button>
            </form>

            <p className="mt-4 text-sm text-muted-foreground">
                <Link
                    to="/login"
                    className="font-semibold text-brand hover:text-brand/80"
                >
                    Back to sign in
                </Link>
            </p>
        </AuthPageShell>
    );
}
