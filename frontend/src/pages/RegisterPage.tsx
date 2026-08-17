import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link } from "react-router-dom";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/common/PasswordInput";
import AuthPageShell from "@/components/common/AuthPageShell";

import { useRegister } from "@/features/auth/hooks/useRegister";
import { registerSchema, type RegisterSchema } from "@/features/auth/schemas";

/**
 * Register page — immersive rider onboarding.
 * Auth rules (password strength, email normalization) are enforced by the API.
 */
export default function RegisterPage() {
    const { mutate: registerUser, isPending } = useRegister();
    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<RegisterSchema>({
        resolver: zodResolver(registerSchema),
        reValidateMode: "onBlur",
    });

    const onSubmit = (data: RegisterSchema) => {
        registerUser(data);
    };

    return (
        <AuthPageShell
            logoTo="/register"
            title="Join the ride"
            subtitle="Set up your garage in under a minute"
        >
            <form
                onSubmit={handleSubmit(onSubmit)}
                className="mt-6 space-y-5"
                noValidate
            >
                <div className="space-y-1.5">
                    <Label htmlFor="full_name">Full Name</Label>
                    <Input
                        id="full_name"
                        type="text"
                        placeholder="Your full name"
                        autoComplete="name"
                        className="border-white/15 bg-white/5"
                        {...register("full_name")}
                    />
                    {errors.full_name && (
                        <p className="text-sm text-destructive">
                            {errors.full_name.message}
                        </p>
                    )}
                </div>

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

                <div className="space-y-1.5">
                    <Label htmlFor="password">Password</Label>
                    <PasswordInput
                        id="password"
                        placeholder="Password"
                        autoComplete="new-password"
                        className="border-white/15 bg-white/5"
                        {...register("password")}
                    />
                    <p className="text-xs text-muted-foreground">
                        At least 8 characters, with one uppercase letter, one
                        number, and one special character.
                    </p>
                    {errors.password && (
                        <p className="text-sm text-destructive">
                            {errors.password.message}
                        </p>
                    )}
                </div>

                <div className="space-y-1.5">
                    <Label htmlFor="confirm_password">Confirm Password</Label>
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
                        "Start riding"
                    )}
                </Button>
            </form>

            <p className="mt-6 text-sm text-muted-foreground">
                Already have an account?{" "}
                <Link
                    to="/login"
                    className="font-semibold text-brand hover:text-brand/80"
                >
                    Login
                </Link>
            </p>
        </AuthPageShell>
    );
}
