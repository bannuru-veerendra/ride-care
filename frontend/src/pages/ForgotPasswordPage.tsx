import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link } from "react-router-dom";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import AuthPageShell from "@/components/common/AuthPageShell";
import { useForgotPassword } from "@/features/auth/hooks/useForgotPassword";
import {
    forgotPasswordSchema,
    type ForgotPasswordSchema,
} from "@/features/auth/schemas";

/**
 * Request a password-reset email (generic success — no enumeration).
 */
export default function ForgotPasswordPage() {
    const { mutate: forgotPassword, isPending } = useForgotPassword();
    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<ForgotPasswordSchema>({
        resolver: zodResolver(forgotPasswordSchema),
        reValidateMode: "onBlur",
    });

    return (
        <AuthPageShell
            logoTo="/login"
            title="Forgot password"
            subtitle="We'll email you a link to choose a new one"
        >
            <form
                onSubmit={handleSubmit((data) => forgotPassword(data.email))}
                className="mt-4 space-y-3"
                noValidate
            >
                <div className="space-y-1.5">
                    <Label htmlFor="email">Email</Label>
                    <Input
                        id="email"
                        type="email"
                        placeholder="your@email.com"
                        autoComplete="email"
                        autoCapitalize="none"
                        autoCorrect="off"
                        spellCheck={false}
                        className="border-white/15 bg-white/5 lowercase"
                        {...register("email")}
                    />
                    {errors.email && (
                        <p className="text-sm text-destructive">
                            {errors.email.message}
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
                        "Send reset link"
                    )}
                </Button>
            </form>

            <p className="mt-4 text-sm text-muted-foreground">
                Remembered it?{" "}
                <Link
                    to="/login"
                    className="font-semibold text-brand hover:text-brand/80"
                >
                    Sign in
                </Link>
            </p>
        </AuthPageShell>
    );
}
