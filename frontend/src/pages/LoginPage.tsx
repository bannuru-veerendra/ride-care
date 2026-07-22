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
import RideCareLogo from "@/components/common/RideCareLogo";

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
        <div className="relative flex min-h-dvh">
            {/* Full-bleed road visual */}
            <div className="absolute inset-0 -z-10">
                <img
                    src="/rider-hero.jpg"
                    alt=""
                    className="h-full w-full object-cover"
                />
                <div className="absolute inset-0 bg-background/80 backdrop-blur-[2px]" />
                <div
                    aria-hidden
                    className="absolute bottom-12 left-1/2 h-px w-48 -translate-x-1/2 bg-gradient-to-r from-transparent via-brand/50 to-transparent"
                />
            </div>

            <div className="flex w-full flex-col items-center justify-center px-4 py-12">
                <div className="animate-speed-in mb-8">
                    <RideCareLogo to="/login" compact={false} inverted />
                </div>

                <div className="animate-fade-up surface-panel w-full max-w-md px-6 py-8 sm:px-8">
                    <h1 className="font-heading text-3xl font-bold uppercase tracking-wide">
                        Kickstand up
                    </h1>
                    <p className="mt-1 text-sm text-muted-foreground">
                        Sign in and get back on the road
                    </p>

                    <form
                        onSubmit={handleSubmit(onSubmit)}
                        className="mt-6 space-y-5"
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
                </div>
            </div>
        </div>
    );
}
