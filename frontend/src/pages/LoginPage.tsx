import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/common/PasswordInput";
import AuthPageShell from "@/components/common/AuthPageShell";

import { useLogin } from "@/features/auth/hooks/useLogin";
import { loginSchema, type LoginSchema } from "@/features/auth/schemas";

/**
 * Login page — immersive rider entry.
 */
export default function LoginPage() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const { mutate: login, isPending } = useLogin();
    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<LoginSchema>({
        resolver: zodResolver(loginSchema),
        reValidateMode: "onBlur",
    });

    useEffect(() => {
        if (searchParams.get("registered") !== "true") {
            return;
        }
        // Stable id prevents Strict Mode double-mount from stacking two toasts
        toast.success("Registration successful! Please login.", {
            id: "registration-success",
        });
        navigate("/login", { replace: true });
    }, [searchParams, navigate]);

    const onSubmit = (data: LoginSchema) => {
        login(data);
    };

    return (
        <AuthPageShell
            logoTo="/login"
            title="Kickstand up"
            subtitle="Sign in and get back on the road"
        >
            <form
                onSubmit={handleSubmit(onSubmit)}
                className="mt-6 space-y-5"
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

                <div className="space-y-1.5">
                    <Label htmlFor="password">Password</Label>
                    <PasswordInput
                        id="password"
                        placeholder="Password"
                        autoComplete="current-password"
                        className="border-white/15 bg-white/5"
                        {...register("password")}
                    />
                    {errors.password && (
                        <p className="text-sm text-destructive">
                            {errors.password.message}
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
                        "Login"
                    )}
                </Button>
            </form>

            <p className="mt-6 text-sm text-muted-foreground">
                New rider?{" "}
                <Link
                    to="/register"
                    className="font-semibold text-brand hover:text-brand/80"
                >
                    Create account
                </Link>
            </p>
        </AuthPageShell>
    );
}
