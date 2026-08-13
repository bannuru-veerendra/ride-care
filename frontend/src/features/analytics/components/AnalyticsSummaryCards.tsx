import { Fuel, TrendingDown, Award, Hash } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface Props {
    totalSpend: number;
    totalLiters: number;
    bestMileage: number | null;
    worstMileage: number | null;
    totalFillUps: number;
}

/**
 * Summary stat cards shown at the top of the analytics tab.
 * Avg mileage lives on the dashboard + trend chart baseline — not repeated here.
 */
export default function AnalyticsSummaryCards({
    totalSpend,
    totalLiters,
    bestMileage,
    worstMileage,
    totalFillUps,
}: Props) {
    const stats = [
        {
            label: "Total spent",
            value: `₹${totalSpend.toLocaleString("en-IN")}`,
            icon: Fuel,
            sub: `${totalLiters}L total`,
        },
        {
            label: "Best fill-up",
            value: bestMileage ? `${bestMileage} km/l` : "—",
            icon: Award,
            sub: "highest km/l",
        },
        {
            label: "Worst fill-up",
            value: worstMileage ? `${worstMileage} km/l` : "—",
            icon: TrendingDown,
            sub: "lowest km/l",
        },
        {
            label: "Total fill-ups",
            value: totalFillUps.toString(),
            icon: Hash,
            sub: "logged",
        },
    ];

    return (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {stats.map((stat) => (
                <Card key={stat.label} className="surface-panel border-0">
                    <CardContent className="px-4 py-4">
                        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-muted-foreground">
                            <stat.icon className="h-3.5 w-3.5 text-brand" />
                            {stat.label}
                        </div>
                        <p className="font-heading mt-2 text-2xl font-extrabold tracking-wide">
                            {stat.value}
                        </p>
                        <p className="mt-0.5 text-xs text-muted-foreground">{stat.sub}</p>
                    </CardContent>
                </Card>
            ))}
        </div>
    );
}
