import type { Severity } from "@/api/maintenance-guidelines.api";

/**
 * Display config for each severity level.
 * Used consistently across guideline cards and badges.
 */
export const SEVERITY_CONFIG: Record<
  Severity,
  { label: string; className: string }
> = {
  critical: {
    label: "Critical",
    className: "border-0 bg-destructive/15 text-destructive",
  },
  high: {
    label: "High",
    className: "border-0 bg-orange-500/15 text-orange-500",
  },
  medium: {
    label: "Medium",
    className: "border-0 bg-brand/15 text-brand",
  },
  low: {
    label: "Low",
    className: "border-0 bg-muted text-muted-foreground",
  },
};

/**
 * Format interval into a human-readable string.
 * Examples:
 *   interval_km=3000, interval_months=3 → "Every 3,000 km or 3 months"
 *   interval_km=500, interval_months=null → "Every 500 km"
 *   interval_km=null, interval_months=24 → "Every 24 months"
 */
export function formatInterval(
  interval_km: number | null,
  interval_months: number | null
): string {
  const parts: string[] = [];
  if (interval_km) {
    parts.push(`Every ${interval_km.toLocaleString("en-IN")} km`);
  }
  if (interval_months) {
    parts.push(
      `${interval_km ? "or " : "Every "}${interval_months} month${interval_months === 1 ? "" : "s"}`
    );
  }
  return parts.join(" ") || "As needed";
}
