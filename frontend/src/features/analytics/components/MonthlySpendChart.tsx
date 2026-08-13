import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell,
} from "recharts";
import type { MonthlySpendPoint } from "../utils";
import { appTodayISO } from "@/lib/date";

interface Props {
    data: MonthlySpendPoint[];
}

/**
 * Bar chart showing monthly fuel spend for last 6 months.
 * Current month bar is highlighted in brand color (Asia/Kolkata).
 */
export default function MonthlySpendChart({ data }: Props) {
    const currentYearMonth = appTodayISO().slice(0, 7);

    const hasData = data.some((d) => d.spend > 0);

    if (!hasData) {
        return (
            <div className="flex h-48 items-center justify-center text-sm text-muted-foreground">
                No fuel logs in the last 6 months
            </div>
        );
    }

    return (
        <ResponsiveContainer width="100%" height={220}>
            <BarChart
                data={data}
                margin={{ top: 8, right: 12, left: 4, bottom: 0 }}
            >
                <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(255,255,255,0.06)"
                    vertical={false}
                />
                <XAxis
                    dataKey="month"
                    tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                    axisLine={false}
                    tickLine={false}
                />
                <YAxis
                    tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(value) =>
                        value >= 1000 ? `₹${(value / 1000).toFixed(1)}k` : `₹${value}`
                    }
                    width={55}
                />
                <Tooltip
                    contentStyle={{
                        background: "var(--card)",
                        border: "1px solid rgba(255,255,255,0.1)",
                        borderRadius: "8px",
                        fontSize: "12px",
                    }}
                    formatter={(value, _name, item) => {
                        const liters =
                            item &&
                            typeof item === "object" &&
                            "payload" in item &&
                            item.payload &&
                            typeof item.payload === "object" &&
                            "liters" in item.payload
                                ? Number(item.payload.liters)
                                : 0;
                        return [
                            `₹${Number(value).toLocaleString("en-IN")} · ${liters}L`,
                            "Spent",
                        ];
                    }}
                />
                <Bar dataKey="spend" radius={[4, 4, 0, 0]} maxBarSize={48}>
                    {data.map((entry) => (
                        <Cell
                            key={entry.year_month ?? entry.month}
                            fill={
                                entry.year_month === currentYearMonth
                                    ? "var(--brand)"
                                    : "rgba(255,255,255,0.12)"
                            }
                        />
                    ))}
                </Bar>
            </BarChart>
        </ResponsiveContainer>
    );
}
