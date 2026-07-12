import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import RideCareLogo from "@/components/common/RideCareLogo";
import { useVehicles } from "@/features/vehicles/hooks/useVehicles";
import { cn } from "@/lib/utils";

/**
 * Dashboard home — rider-first brand composition.
 * Full-bleed road hero with a single clear path into the garage.
 */
export default function DashboardPage() {
    const { data: vehicles } = useVehicles();
    const count = vehicles?.length ?? 0;

    return (
        <div className="space-y-8">
            {/* Full-bleed rider hero — brand + one line + CTA */}
            <section className="relative -mx-4 min-h-[min(78dvh,640px)] overflow-hidden sm:-mx-6 sm:rounded-3xl sm:border sm:border-white/10">
                <img
                    src="/rider-hero.jpg"
                    alt=""
                    className="absolute inset-0 h-full w-full scale-105 object-cover animate-fade-in"
                />
                <div className="rider-hero-mask absolute inset-0" />
                <div
                    aria-hidden
                    className="absolute bottom-10 left-6 right-6 z-10 h-px bg-gradient-to-r from-transparent via-brand/70 to-transparent sm:left-10 sm:right-10"
                />

                <div className="relative z-10 flex h-full min-h-[min(78dvh,640px)] flex-col justify-end px-6 pb-14 pt-10 sm:px-10 sm:pb-16">
                    <div className="animate-speed-in max-w-xl space-y-5">
                        <RideCareLogo to="/dashboard" compact={false} inverted />
                        <p className="max-w-md text-base text-white/75 sm:text-lg">
                            Fuel, mileage, and service — built for riders who live on the road.
                        </p>
                        <Link
                            to="/vehicles"
                            className={cn(
                                buttonVariants({ size: "lg" }),
                                "bg-brand text-brand-foreground hover:bg-brand/90"
                            )}
                        >
                            {count > 0 ? "Open your garage" : "Add your first bike"}
                            <ArrowRight className="ml-1 h-4 w-4" />
                        </Link>
                    </div>
                </div>
            </section>

            <section
                className="animate-fade-up surface-panel px-6 py-8 sm:px-8"
                style={{ animationDelay: "120ms" }}
            >
                <p className="text-xs font-bold uppercase tracking-[0.22em] text-brand">
                    Garage status
                </p>
                <h2 className="font-heading mt-2 text-3xl font-bold uppercase tracking-wide sm:text-4xl">
                    {count > 0
                        ? `${count} bike${count === 1 ? "" : "s"} ready to ride`
                        : "Your garage is empty"}
                </h2>
                <p className="mt-2 max-w-lg text-muted-foreground">
                    {count > 0
                        ? "Open a bike to log fuel, track km/l, and keep every ride documented."
                        : "Register your machine and start logging every fill-up."}
                </p>
                <Link
                    to="/vehicles"
                    className={cn(buttonVariants(), "mt-6 inline-flex bg-white text-background hover:bg-white/90")}
                >
                    Go to vehicles
                    <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
            </section>
        </div>
    );
}
