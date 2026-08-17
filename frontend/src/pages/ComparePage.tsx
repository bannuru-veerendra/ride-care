import { Link } from "react-router-dom";

import { Skeleton } from "@/components/ui/skeleton";
import CompareTable from "@/features/analytics/components/CompareTable";
import { useVehicleCompare } from "@/features/vehicles/hooks/useVehicles";

/**
 * Garage compare — running cost and mileage across bikes.
 */
export default function ComparePage() {
    const { data, isLoading } = useVehicleCompare();
    const items = data?.items ?? [];

    return (
        <div className="animate-fade-up space-y-8">
            <div>
                <p className="text-xs font-bold uppercase tracking-[0.22em] text-brand">
                    Across the fleet
                </p>
                <h1 className="font-heading mt-1 text-5xl font-extrabold uppercase italic tracking-wide sm:text-6xl">
                    Compare
                </h1>
                <p className="mt-2 text-sm text-muted-foreground">
                    Fuel + service cost per kilometre, side by side
                </p>
            </div>

            {isLoading && (
                <div className="space-y-3">
                    {[1, 2].map((i) => (
                        <Skeleton key={i} className="h-24 rounded-2xl bg-white/5" />
                    ))}
                </div>
            )}

            {!isLoading && items.length === 0 && (
                <div className="surface-panel px-6 py-16 text-center">
                    <p className="font-heading text-3xl font-bold uppercase italic tracking-wide">
                        Empty bay
                    </p>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Add a bike in the garage to start comparing
                    </p>
                    <Link
                        to="/vehicles"
                        className="mt-4 inline-block text-sm font-semibold text-brand hover:underline"
                    >
                        Open garage
                    </Link>
                </div>
            )}

            {!isLoading && items.length > 0 && <CompareTable items={items} />}
        </div>
    );
}
