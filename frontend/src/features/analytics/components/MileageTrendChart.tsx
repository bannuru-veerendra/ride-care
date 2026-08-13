import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
} from "recharts";
import type { MileageTrendPoint } from "../utils";

interface Props {
    data: MileageTrendPoint[];
    avgMileage: number | null;
}

/**
 * Line chart showing mileage (km/l) trend over last 10 fill-ups.
 * Reference line shows the overall average.
 */
export default function MileageTrendChart({ data, avgMileage }: Props) {
    if (data.length < 2) {
        return (
            <div className="flex h-48 items-center justify-center text-sm text-muted-foreground">
                Need at least 2 fill-ups with mileage data to show trend
            </div>
        );
    }

    return (
        <ResponsiveContainer width="100%" height={220}>
            <LineChart
                data={data}
                margin={{ top: 12, right: 12, left: 4, bottom: 0 }}
            >
                <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(255,255,255,0.06)"
                    vertical={false}
                />
                <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                    axisLine={false}
                    tickLine={false}
                />
                <YAxis
                    tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                    axisLine={false}
                    tickLine={false}
                    width={40}
                    tickFormatter={(value: number) => `${value}`}
                />
                <Tooltip
                    contentStyle={{
                        background: "var(--card)",
                        border: "1px solid rgba(255,255,255,0.1)",
                        borderRadius: "8px",
                        fontSize: "12px",
                    }}
                    formatter={(value) => [`${value} km/l`, "Mileage"]}
                    labelFormatter={(label) => `Date: ${label}`}
                />
                {avgMileage != null && avgMileage > 0 && (
                    <ReferenceLine
                        y={avgMileage}
                        stroke="rgba(255,255,255,0.2)"
                        strokeDasharray="4 4"
                        label={{
                            value: `Avg ${avgMileage}`,
                            position: "insideTopRight",
                            fontSize: 10,
                            fill: "var(--muted-foreground)",
                        }}
                    />
                )}
                <Line
                    type="monotone"
                    dataKey="mileage"
                    stroke="var(--brand)"
                    strokeWidth={2}
                    dot={{
                        fill: "var(--brand)",
                        strokeWidth: 0,
                        r: 3,
                    }}
                    activeDot={{
                        r: 5,
                        fill: "var(--brand)",
                        strokeWidth: 0,
                    }}
                />
            </LineChart>
        </ResponsiveContainer>
    );
}
