import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import type { VehicleCompareItem } from "@/features/vehicles/types";
import { cn } from "@/lib/utils";
import { bestIds } from "../utils";

interface Props {
    items: VehicleCompareItem[];
}

interface Stat {
    label: string;
    value: string;
    emphasize?: boolean;
    highlight?: boolean;
    badge?: "Best" | "Lowest";
}

function inr(amount: number) {
    return `₹${amount.toLocaleString("en-IN")}`;
}

function statsFor(
    item: VehicleCompareItem,
    isBestMileage: boolean,
    isLowestCost: boolean
): Stat[] {
    return [
        {
            label: "km driven",
            value: item.km_driven.toLocaleString("en-IN"),
        },
        {
            label: "Avg km/L",
            value: item.avg_mileage != null ? item.avg_mileage.toFixed(2) : "—",
            badge: isBestMileage && item.avg_mileage != null ? "Best" : undefined,
        },
        { label: "Fuel", value: inr(item.fuel_spend) },
        { label: "Service", value: inr(item.service_spend) },
        { label: "Total", value: inr(item.combined_spend), emphasize: true },
        {
            label: "₹/km",
            value: item.cost_per_km != null ? inr(item.cost_per_km) : "—",
            emphasize: true,
            highlight: isLowestCost && item.cost_per_km != null,
            badge: isLowestCost && item.cost_per_km != null ? "Lowest" : undefined,
        },
    ];
}

/**
 * Bikes as columns, metrics as rows, so the fleet sits side by side.
 * Highlights best km/L and lowest ₹/km.
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

    const columns = items.map((item) => ({
        item,
        stats: statsFor(
            item,
            bestMileageIds.has(item.vehicle_id),
            bestCostIds.has(item.vehicle_id)
        ),
    }));
    const rows = columns[0].stats;

    return (
        <div className="surface-panel overflow-x-auto">
            <table className="w-full text-left text-sm">
                <thead>
                    <tr className="border-b border-white/10">
                        <th className="w-28 px-3 py-3 sm:px-4" scope="col">
                            <span className="sr-only">Metric</span>
                        </th>
                        {columns.map(({ item }) => (
                            <th
                                key={item.vehicle_id}
                                scope="col"
                                className="min-w-[8.5rem] px-3 py-4 align-bottom font-normal sm:px-4"
                            >
                                <Link
                                    to={`/vehicles/${item.vehicle_id}?tab=analytics`}
                                    className="font-heading text-base font-bold uppercase tracking-wide hover:text-brand sm:text-lg"
                                >
                                    {item.vehicle_name}
                                </Link>
                                <p className="text-xs text-muted-foreground">
                                    {item.brand} · {item.year}
                                </p>
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {rows.map((row, rowIndex) => (
                        <tr
                            key={row.label}
                            className="border-b border-white/5 last:border-0"
                        >
                            <th
                                scope="row"
                                className="whitespace-nowrap px-3 py-3 text-xs font-semibold uppercase tracking-widest text-muted-foreground sm:px-4 sm:py-4"
                            >
                                {row.label}
                            </th>
                            {columns.map(({ item, stats }) => {
                                const stat = stats[rowIndex];
                                return (
                                    <td
                                        key={item.vehicle_id}
                                        className="px-3 py-3 sm:px-4 sm:py-4"
                                    >
                                        <span className="inline-flex items-center gap-2">
                                            <span
                                                className={cn(
                                                    "tabular-nums whitespace-nowrap",
                                                    stat.emphasize && "font-semibold",
                                                    stat.highlight && "text-brand"
                                                )}
                                            >
                                                {stat.value}
                                            </span>
                                            {stat.badge === "Best" && (
                                                <Badge className="border-0 bg-emerald-500/15 text-[10px] text-emerald-400">
                                                    Best
                                                </Badge>
                                            )}
                                            {stat.badge === "Lowest" && (
                                                <Badge className="border-0 bg-brand/15 text-[10px] text-brand">
                                                    Lowest
                                                </Badge>
                                            )}
                                        </span>
                                    </td>
                                );
                            })}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
