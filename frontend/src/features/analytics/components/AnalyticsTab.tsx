import AnalyticsSummaryCards from "./AnalyticsSummaryCards";
import MileageTrendChart from "./MileageTrendChart";
import MonthlySpendChart from "./MonthlySpendChart";
import { useVehicleAnalytics } from "@/features/vehicles/hooks/useVehicles";

interface Props {
  vehicleId: string;
}

/**
 * Analytics tab for the vehicle detail page.
 * Aggregations come from GET /vehicles/{id}/analytics —
 * the tab only renders charts and insight copy.
 */
export default function AnalyticsTab({ vehicleId }: Props) {
  const { data, isLoading } = useVehicleAnalytics(vehicleId);

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-24 rounded-xl bg-white/5" />
          ))}
        </div>
        <div className="h-56 rounded-xl bg-white/5" />
        <div className="h-56 rounded-xl bg-white/5" />
      </div>
    );
  }

  if (!data || data.total_fill_ups === 0) {
    return (
      <div className="surface-panel px-6 py-14 text-center">
        <p className="font-heading text-2xl font-bold uppercase tracking-wide">
          No data yet
        </p>
        <p className="mt-2 text-sm text-muted-foreground">
          Log at least one fuel fill-up to see analytics
        </p>
      </div>
    );
  }

  const mileageTrend = data.mileage_trend.map((point) => ({
    date: point.date_label,
    mileage: point.mileage,
    odometer: point.odometer,
  }));

  return (
    <div className="space-y-6">
      <AnalyticsSummaryCards
        totalSpend={data.total_spend}
        totalLiters={data.total_liters}
        avgMileage={data.avg_mileage}
        bestMileage={data.best_mileage}
        worstMileage={data.worst_mileage}
        totalFillUps={data.total_fill_ups}
      />

      <div className="surface-panel px-5 py-5">
        <div className="mb-4">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-brand">
            Mileage trend
          </p>
          <p className="mt-0.5 text-sm text-muted-foreground">
            km/l over last 10 fill-ups
          </p>
        </div>
        <MileageTrendChart
          data={mileageTrend}
          avgMileage={data.avg_mileage}
        />
      </div>

      <div className="surface-panel px-5 py-5">
        <div className="mb-4">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-brand">
            Monthly fuel spend
          </p>
          <p className="mt-0.5 text-sm text-muted-foreground">
            ₹ spent per month · last 6 months
          </p>
        </div>
        <MonthlySpendChart data={data.monthly_spend} />
      </div>

      {data.best_mileage != null &&
        data.worst_mileage != null &&
        data.best_mileage - data.worst_mileage > 5 && (
          <div className="surface-panel border-brand/30 px-5 py-4">
            <p className="mb-1 text-xs font-bold uppercase tracking-[0.18em] text-brand">
              Insight
            </p>
            <p className="text-sm text-muted-foreground">
              Your mileage varies by{" "}
              <span className="font-semibold text-foreground">
                {(data.best_mileage - data.worst_mileage).toFixed(1)} km/l
              </span>{" "}
              between best and worst fill-ups. Check tyre pressure and riding
              speed for consistent efficiency.
            </p>
          </div>
        )}
    </div>
  );
}
