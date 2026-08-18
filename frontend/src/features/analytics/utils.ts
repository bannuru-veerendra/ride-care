/**
 * Chart prop types after mapping GET /vehicles/{id}/analytics series.
 * API points use date_label; charts plot the display label as `date`.
 */

export interface MileageTrendPoint {
    date: string;
    mileage: number;
    odometer: number;
}

export interface MonthlySpendPoint {
    month: string;
    year_month?: string;
    spend: number;
    liters: number;
}

/** Vehicle ids that share the best (max) or lowest (min) numeric metric. */
export function bestIds<T>(
    items: T[],
    id: (item: T) => string,
    pick: (item: T) => number | null,
    prefer: "max" | "min"
): Set<string> {
    const scored = items
        .map((item) => ({ id: id(item), value: pick(item) }))
        .filter((row): row is { id: string; value: number } => row.value != null);
    if (scored.length === 0) return new Set();
    const target =
        prefer === "max"
            ? Math.max(...scored.map((row) => row.value))
            : Math.min(...scored.map((row) => row.value));
    return new Set(
        scored.filter((row) => row.value === target).map((row) => row.id)
    );
}
