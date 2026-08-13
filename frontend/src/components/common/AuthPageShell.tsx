import type { ReactNode } from "react";

import RideCareLogo from "@/components/common/RideCareLogo";

interface AuthPageShellProps {
    logoTo: "/login" | "/register";
    title: string;
    subtitle: string;
    children: ReactNode;
}

/** Shared full-bleed auth chrome for login and register. */
export default function AuthPageShell({
    logoTo,
    title,
    subtitle,
    children,
}: AuthPageShellProps) {
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
                    <RideCareLogo to={logoTo} compact={false} inverted />
                </div>

                <div className="animate-fade-up surface-panel w-full max-w-md px-6 py-8 sm:px-8">
                    <h1 className="font-heading text-3xl font-bold uppercase tracking-wide">
                        {title}
                    </h1>
                    <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
                    {children}
                </div>
            </div>
        </div>
    );
}
