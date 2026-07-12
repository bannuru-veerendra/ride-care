import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { isAxiosError } from "axios";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/common/PasswordInput";
import RideCareLogo from "@/components/common/RideCareLogo";

import { useRegister } from "@/features/auth/hooks/useRegister";
import { registerSchema, type RegisterSchema } from "@/features/auth/schemas";

/**
 * Register page — immersive rider onboarding.
 */
export default function RegisterPage() {
    const { mutate: registerUser, isPending, error } = useRegister();
    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<RegisterSchema>({
        resolver: zodResolver(registerSchema),
    });

    const onSubmit = (data: RegisterSchema) => {
        registerUser(data);
    };

    const apiError = isAxiosError(error)
        ? error.response?.data?.detail ?? "Registration failed. Please try again."
        : null;

    return (
        <div className="relative flex min-h-dvh">
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
                    <RideCareLogo to="/register" compact={false} inverted />
                </div>

                <div className="animate-fade-up surface-panel w-full max-w-md px-6 py-8 sm:px-8">
                    <h1 className="font-heading text-3xl font-bold uppercase tracking-wide">
                        Join the ride
                    </h1>
                    <p className="mt-1 text-sm text-muted-foreground">
                        Set up your garage in under a minute
                    </p>

                    <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-5">
                        {apiError && (
                            <div className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                                {apiError}
                            </div>
                        )}

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
                                className="border-white/15 bg-white/5"
                                {...register("email")}
                            />
                            {errors.email && (
                                <p className="text-sm text-destructive">{errors.email.message}</p>
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
                </div>
            </div>
        </div>
    );
}
