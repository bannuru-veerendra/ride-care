import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import type { VehicleCompareItem } from "@/features/vehicles/types";
import { cn } from "@/lib/utils";
import { bestIds } from "../utils";

interface Props {
    items: VehicleCompareItem[];
}

/**
 * Side-by-side garage table. Highlights best km/L and lowest ₹/km.
 */
export default function CompareTable({ items }: Props) {
    const bestMileageIds = bestIds(
        items,
        (item) => item.vehicle_id,
        (item) => item.avg_mileage,
        "max"
    );
    const bestCostIds = bestIds(
        items,
        (item) => item.vehicle_id,
        (item) => item.cost_per_km,
        "min"
    );

    return (
        <div className="surface-panel overflow-x-auto">
            <table className="w-full min-w-[44rem] text-left text-sm">
                <thead>
                    <tr className="border-b border-white/10 text-xs uppercase tracking-widest text-muted-foreground">
                        <th className="px-4 py-3 font-semibold">Bike</th>
                        <th className="px-4 py-3 font-semibold">km driven</th>
                        <th className="px-4 py-3 font-semibold">Avg km/L</th>
                        <th className="px-4 py-3 font-semibold">Fuel</th>
                        <th className="px-4 py-3 font-semibold">Service</th>
                        <th className="px-4 py-3 font-semibold">Total</th>
                        <th className="px-4 py-3 font-semibold">₹/km</th>
                    </tr>
                </thead>
                <tbody>
                    {items.map((item) => {
                        const isBestMileage = bestMileageIds.has(item.vehicle_id);
                        const isLowestCost = bestCostIds.has(item.vehicle_id);
                        return (
                            <tr
                                key={item.vehicle_id}
                                className="border-b border-white/5 last:border-0"
                            >
                                <td className="px-4 py-4">
                                    <Link
                                        to={`/vehicles/${item.vehicle_id}?tab=analytics`}
                                        className="font-heading text-lg font-bold uppercase tracking-wide hover:text-brand"
                                    >
                                        {item.vehicle_name}
                                    </Link>
                                    <p className="text-xs text-muted-foreground">
                                        {item.brand} · {item.year}
                                    </p>
                                </td>
                                <td className="px-4 py-4 tabular-nums">
                                    {item.km_driven.toLocaleString("en-IN")}
                                </td>
                                <td className="px-4 py-4">
                                    <span className="tabular-nums">
                                        {item.avg_mileage != null
                                            ? item.avg_mileage.toFixed(1)
                                            : "—"}
                                    </span>
                                    {isBestMileage && item.avg_mileage != null && (
                                        <Badge className="ml-2 border-0 bg-emerald-500/15 text-[10px] text-emerald-400">
                                            Best
                                        </Badge>
                                    )}
                                </td>
                                <td className="px-4 py-4 tabular-nums">
                                    ₹{item.fuel_spend.toLocaleString("en-IN")}
                                </td>
                                <td className="px-4 py-4 tabular-nums">
                                    ₹{item.service_spend.toLocaleString("en-IN")}
                                </td>
                                <td className="px-4 py-4 tabular-nums font-semibold">
                                    ₹{item.combined_spend.toLocaleString("en-IN")}
                                </td>
                                <td className="px-4 py-4">
                                    <span
                                        className={cn(
                                            "tabular-nums font-semibold",
                                            isLowestCost &&
                                                item.cost_per_km != null &&
                                                "text-brand"
                                        )}
                                    >
                                        {item.cost_per_km != null
                                            ? `₹${item.cost_per_km.toLocaleString("en-IN")}`
                                            : "—"}
                                    </span>
                                    {isLowestCost && item.cost_per_km != null && (
                                        <Badge className="ml-2 border-0 bg-brand/15 text-[10px] text-brand">
                                            Lowest
                                        </Badge>
                                    )}
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}
