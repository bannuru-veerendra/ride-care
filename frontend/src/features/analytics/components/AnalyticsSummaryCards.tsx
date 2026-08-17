import { Fuel, TrendingDown, Award, IndianRupee } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface Props {
    combinedSpend: number;
    fuelSpend: number;
    serviceSpend: number;
    kmDriven: number;
    costPerKm: number | null;
    bestMileage: number | null;
    worstMileage: number | null;
}

/**
 * Summary stat cards shown at the top of the analytics tab.
 * Avg mileage lives on the dashboard + trend chart baseline — not repeated here.
 */
export default function AnalyticsSummaryCards({
    combinedSpend,
    fuelSpend,
    serviceSpend,
    kmDriven,
    costPerKm,
    bestMileage,
    worstMileage,
}: Props) {
    const stats = [
        {
            label: "Cost per km",
            value:
                costPerKm != null
                    ? `₹${costPerKm.toLocaleString("en-IN")}`
                    : "—",
            icon: IndianRupee,
            sub:
                kmDriven > 0
                    ? `${kmDriven.toLocaleString("en-IN")} km · fuel + service`
                    : "needs km past baseline",
        },
        {
            label: "Total spent",
            value: `₹${combinedSpend.toLocaleString("en-IN")}`,
            icon: Fuel,
            sub: `Fuel ₹${fuelSpend.toLocaleString("en-IN")} · Service ₹${serviceSpend.toLocaleString("en-IN")}`,
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
