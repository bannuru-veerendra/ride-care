import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
    AlertTriangle,
    ArrowRight,
    ChevronRight,
    Fuel,
    Gauge,
    TrendingDown,
    TrendingUp,
    Wrench,
} from "lucide-react";
import {
    format,
    differenceInDays,
    isSameMonth,
    isSameYear,
    subMonths,
    parseISO,
} from "date-fns";

import { buttonVariants } from "@/components/ui/button";
import RideCareLogo from "@/components/common/RideCareLogo";
import { useVehicles } from "@/features/vehicles/hooks/useVehicles";
import { useNextService } from "@/features/service-logs/hooks/useServiceLogs";
import { useFuelLogs } from "@/features/fuel-logs/hooks/useFuelLogs";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { FuelLog } from "@/features/fuel-logs/types";
import type { Vehicle } from "@/features/vehicles/types";

const SELECTED_VEHICLE_KEY = "ridecare-dashboard-vehicle";

/** Average km/l across fuel logs that have mileage */
function getAverageMileage(logs: FuelLog[]): number | null {
    const mileages = logs
        .map((log) => log.mileage)
        .filter((mileage): mileage is number => mileage !== null);
    if (mileages.length === 0) return null;

    const sum = mileages.reduce((total, mileage) => total + mileage, 0);
    return Math.round((sum / mileages.length) * 10) / 10;
}

function getMonthSpend(logs: FuelLog[], month: Date): number {
    return logs
        .filter((log) => {
            const date = parseISO(log.date);
            return isSameMonth(date, month) && isSameYear(date, month);
        })
        .reduce((sum, log) => sum + log.total_cost, 0);
}

function getMonthMileage(logs: FuelLog[], month: Date): number | null {
    return getAverageMileage(
        logs.filter((log) => {
            const date = parseISO(log.date);
            return isSameMonth(date, month) && isSameYear(date, month);
        })
    );
}

/**
 * Dashboard home — actionable hub for returning riders.
 */
export default function DashboardPage() {
    const { data: vehiclesPage, isLoading: vehiclesLoading } = useVehicles();
    const vehicles = vehiclesPage?.items ?? [];
    const count = vehiclesPage?.total ?? 0;

    const [selectedVehicleId, setSelectedVehicleId] = useState("");

    useEffect(() => {
        if (!vehicles.length) {
            setSelectedVehicleId("");
            return;
        }

        const saved = localStorage.getItem(SELECTED_VEHICLE_KEY);
        const match = vehicles.find((vehicle) => vehicle.id === saved);
        setSelectedVehicleId(match?.id ?? vehicles[0].id);
    }, [vehicles]);

    const handleSelectVehicle = (id: string) => {
        setSelectedVehicleId(id);
        localStorage.setItem(SELECTED_VEHICLE_KEY, id);
    };

    const selectedVehicle: Vehicle | undefined =
        vehicles.find((vehicle) => vehicle.id === selectedVehicleId) ??
        vehicles[0];

    const { data: fuelLogsPage, isLoading: fuelLogsLoading } = useFuelLogs(
        selectedVehicle?.id ?? ""
    );
    const { data: nextService, isLoading: nextServiceLoading } = useNextService(
        selectedVehicle?.id ?? ""
    );

    const fuelLogs = fuelLogsPage?.items ?? [];
    const recentFuelLogs = fuelLogs.slice(0, 3);
    const hasFuelLogs = (fuelLogsPage?.total ?? 0) > 0;
    const averageMileage = fuelLogs.length
        ? getAverageMileage(fuelLogs)
        : null;

    const now = new Date();
    const thisMonthSpend = fuelLogs.length ? getMonthSpend(fuelLogs, now) : 0;
    const lastMonthSpend = fuelLogs.length
        ? getMonthSpend(fuelLogs, subMonths(now, 1))
        : 0;
    const thisMonthMileage = fuelLogs.length
        ? getMonthMileage(fuelLogs, now)
        : null;
    const lastMonthMileage = fuelLogs.length
        ? getMonthMileage(fuelLogs, subMonths(now, 1))
        : null;
    const mileageDelta =
        thisMonthMileage !== null && lastMonthMileage !== null
            ? thisMonthMileage - lastMonthMileage
            : null;

    const daysUntilNextService = nextService?.next_service_date
        ? differenceInDays(new Date(nextService.next_service_date), new Date())
        : null;
    const serviceOverdue =
        daysUntilNextService !== null && daysUntilNextService < 0;
    const serviceSoon =
        daysUntilNextService !== null &&
        daysUntilNextService >= 0 &&
        daysUntilNextService <= 14;

    const fuelHref = selectedVehicle
        ? `/vehicles/${selectedVehicle.id}?action=fuel`
        : "/vehicles";
    const serviceHref = selectedVehicle
        ? `/vehicles/${selectedVehicle.id}?action=service`
        : "/vehicles";
    const vehicleHref = selectedVehicle
        ? `/vehicles/${selectedVehicle.id}`
        : "/vehicles";

    let statusLine = "Ready when you are.";
    if (selectedVehicle) {
        if (serviceOverdue) {
            statusLine = "Service overdue — book it soon.";
        } else if (serviceSoon) {
            statusLine = `Service in ${daysUntilNextService} day${daysUntilNextService === 1 ? "" : "s"}.`;
        } else if (!hasFuelLogs) {
            statusLine = "Add a fill-up to unlock mileage insights.";
        } else {
            statusLine = "Good to ride.";
        }
    }

    if (vehiclesLoading) {
        return (
            <div className="space-y-6">
                <Skeleton className="h-36 w-full rounded-3xl" />
                <div className="grid grid-cols-2 gap-3">
                    <Skeleton className="h-20 rounded-2xl" />
                    <Skeleton className="h-20 rounded-2xl" />
                </div>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                    <Skeleton className="h-28 rounded-2xl" />
                    <Skeleton className="h-28 rounded-2xl" />
                    <Skeleton className="col-span-2 h-28 rounded-2xl sm:col-span-1" />
                </div>
            </div>
        );
    }

    // Empty garage — full branded hero
    if (count === 0) {
        return (
            <div className="space-y-8">
                <section className="relative -mx-4 min-h-[min(78dvh,640px)] overflow-hidden sm:-mx-6 sm:rounded-3xl sm:border sm:border-white/10">
                    <img
                        src="/rider-hero.jpg"
                        alt=""
                        className="absolute inset-0 h-full w-full scale-105 object-cover animate-fade-in"
                    />
                    <div className="rider-hero-mask absolute inset-0" />
                    <div
                        aria-hidden
                        className="absolute bottom-10 left-6 right-6 z-10 h-px bg-gradient-to-r from-transparent via-brand/70 to-transparent sm:left-10 sm:right-10"
                    />

                    <div className="relative z-10 flex h-full min-h-[min(78dvh,640px)] flex-col justify-end px-6 pb-14 pt-10 sm:px-10 sm:pb-16">
                        <div className="animate-speed-in max-w-xl space-y-5">
                            <RideCareLogo to="/dashboard" compact={false} inverted />
                            <p className="max-w-md text-base text-white/75 sm:text-lg">
                                Fuel, mileage, and service — built for riders who live
                                on the road.
                            </p>
                            <Link
                                to="/vehicles"
                                className={cn(
                                    buttonVariants({ size: "lg" }),
                                    "bg-brand text-brand-foreground hover:bg-brand/90"
                                )}
                            >
                                Add your first bike
                                <ArrowRight className="ml-1 h-4 w-4" />
                            </Link>
                        </div>
                    </div>
                </section>

                <section
                    className="animate-fade-up surface-panel px-6 py-8 sm:px-8"
                    style={{ animationDelay: "120ms" }}
                >
                    <p className="text-xs font-bold uppercase tracking-[0.22em] text-brand">
                        Garage status
                    </p>
                    <h2 className="font-heading mt-2 text-3xl font-bold uppercase tracking-wide sm:text-4xl">
                        Your garage is empty
                    </h2>
                    <p className="mt-2 max-w-lg text-muted-foreground">
                        Register your machine and start logging every fill-up.
                    </p>
                    <Link
                        to="/vehicles"
                        className={cn(
                            buttonVariants(),
                            "mt-6 inline-flex bg-white text-background hover:bg-white/90"
                        )}
                    >
                        Add your first bike
                        <ArrowRight className="ml-1 h-4 w-4" />
                    </Link>
                </section>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* Compact status strip for returning riders */}
            <section className="relative -mx-4 overflow-hidden sm:-mx-6 sm:rounded-3xl sm:border sm:border-white/10">
                <img
                    src="/rider-hero.jpg"
                    alt=""
                    className="absolute inset-0 h-full w-full scale-105 object-cover"
                />
                <div className="rider-hero-mask absolute inset-0" />

                <div className="relative z-10 flex flex-col justify-end gap-4 px-6 py-8 sm:flex-row sm:items-end sm:justify-between sm:px-10 sm:py-10">
                    <div className="animate-speed-in max-w-lg space-y-2">
                        <RideCareLogo to="/dashboard" compact={false} inverted />
                        <p className="text-base text-white/80 sm:text-lg">{statusLine}</p>
                    </div>
                    <Link
                        to="/vehicles"
                        className={cn(
                            buttonVariants({ size: "sm" }),
                            "w-fit shrink-0 border border-white/20 bg-white/10 text-white backdrop-blur-sm hover:bg-white/20"
                        )}
                    >
                        Open garage
                        <ArrowRight className="ml-1 h-4 w-4" />
                    </Link>
                </div>
            </section>

            {/* Quick actions */}
            {selectedVehicle && (
                <section
                    className="animate-fade-up grid grid-cols-2 gap-3"
                    style={{ animationDelay: "80ms" }}
                >
                    <Link
                        to={fuelHref}
                        className="surface-panel flex items-center gap-3 px-5 py-4 transition-colors hover:border-brand/40 hover:bg-card"
                    >
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand/15">
                            <Fuel className="h-5 w-5 text-brand" />
                        </div>
                        <div className="min-w-0">
                            <p className="font-heading text-lg font-bold uppercase tracking-wide">
                                Log fill-up
                            </p>
                            <p className="truncate text-xs text-muted-foreground">
                                Record fuel & mileage
                            </p>
                        </div>
                    </Link>
                    <Link
                        to={serviceHref}
                        className="surface-panel flex items-center gap-3 px-5 py-4 transition-colors hover:border-brand/40 hover:bg-card"
                    >
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand/15">
                            <Wrench className="h-5 w-5 text-brand" />
                        </div>
                        <div className="min-w-0">
                            <p className="font-heading text-lg font-bold uppercase tracking-wide">
                                Log service
                            </p>
                            <p className="truncate text-xs text-muted-foreground">
                                {serviceOverdue
                                    ? "Overdue — add now"
                                    : "Track next due date"}
                            </p>
                        </div>
                    </Link>
                </section>
            )}

            {/* Quick stats */}
            {selectedVehicle && (
                <section
                    className="animate-fade-up"
                    style={{ animationDelay: "140ms" }}
                >
                    <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                        <p className="text-xs font-bold uppercase tracking-[0.22em] text-brand">
                            Quick stats
                        </p>
                        {count > 1 && (
                            <div className="flex flex-wrap gap-2">
                                {vehicles.map((vehicle) => (
                                    <button
                                        key={vehicle.id}
                                        type="button"
                                        onClick={() =>
                                            handleSelectVehicle(vehicle.id)
                                        }
                                        className={cn(
                                            "rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors",
                                            vehicle.id === selectedVehicle.id
                                                ? "border-brand/50 bg-brand/15 text-brand"
                                                : "border-white/10 text-muted-foreground hover:border-white/25 hover:text-foreground"
                                        )}
                                    >
                                        {vehicle.brand} {vehicle.vehicle_name}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    {count === 1 && (
                        <p className="mb-3 text-sm text-muted-foreground">
                            {selectedVehicle.brand} {selectedVehicle.vehicle_name}
                        </p>
                    )}

                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                        <Link to={vehicleHref} className="block">
                            <Card className="surface-panel h-full border-0 transition-colors hover:border-brand/40">
                                <CardContent className="px-5 py-5">
                                    <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-muted-foreground">
                                        <Gauge className="h-3.5 w-3.5 text-brand" />
                                        Odometer
                                    </div>
                                    <p className="font-heading mt-2 text-3xl font-extrabold tracking-wide">
                                        {selectedVehicle.current_odometer.toLocaleString(
                                            "en-IN"
                                        )}
                                    </p>
                                    <p className="text-xs text-muted-foreground">km</p>
                                </CardContent>
                            </Card>
                        </Link>

                        <Link to={fuelHref} className="block">
                            <Card className="surface-panel h-full border-0 transition-colors hover:border-brand/40">
                                <CardContent className="px-5 py-5">
                                    <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-muted-foreground">
                                        <Fuel className="h-3.5 w-3.5 text-brand" />
                                        Avg mileage
                                    </div>
                                    {fuelLogsLoading ? (
                                        <Skeleton className="mt-2 h-9 w-20" />
                                    ) : (
                                        <>
                                            <p className="font-heading mt-2 text-3xl font-extrabold tracking-wide">
                                                {averageMileage ?? "—"}
                                            </p>
                                            <p className="text-xs text-muted-foreground">
                                                km / litre
                                            </p>
                                        </>
                                    )}
                                </CardContent>
                            </Card>
                        </Link>

                        <Link
                            to={serviceHref}
                            className="col-span-2 block sm:col-span-1"
                        >
                            <Card className="surface-panel h-full border-0 transition-colors hover:border-brand/40">
                                <CardContent className="px-5 py-5">
                                    <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-muted-foreground">
                                        <Wrench className="h-3.5 w-3.5 text-brand" />
                                        Next service
                                    </div>
                                    {nextServiceLoading ? (
                                        <Skeleton className="mt-2 h-9 w-32" />
                                    ) : nextService?.next_service_date ? (
                                        <>
                                            <p className="font-heading mt-2 text-3xl font-extrabold tracking-wide">
                                                {daysUntilNextService !== null &&
                                                daysUntilNextService >= 0
                                                    ? `${daysUntilNextService}d`
                                                    : "Overdue"}
                                            </p>
                                            <div className="mt-1 flex items-center gap-1.5">
                                                <p className="text-xs text-muted-foreground">
                                                    {format(
                                                        new Date(
                                                            nextService.next_service_date
                                                        ),
                                                        "dd MMM yyyy"
                                                    )}
                                                </p>
                                                {(serviceSoon || serviceOverdue) && (
                                                    <Badge
                                                        variant={
                                                            serviceOverdue
                                                                ? "destructive"
                                                                : "outline"
                                                        }
                                                        className={
                                                            !serviceOverdue
                                                                ? "border-0 bg-brand/15 text-xs text-brand"
                                                                : "text-xs"
                                                        }
                                                    >
                                                        <AlertTriangle className="mr-1 h-3 w-3" />
                                                        {serviceOverdue
                                                            ? "Overdue"
                                                            : "Soon"}
                                                    </Badge>
                                                )}
                                            </div>
                                        </>
                                    ) : (
                                        <>
                                            <p className="font-heading mt-2 text-3xl font-extrabold tracking-wide">
                                                —
                                            </p>
                                            <p className="text-xs text-muted-foreground">
                                                Tap to schedule
                                            </p>
                                        </>
                                    )}
                                </CardContent>
                            </Card>
                        </Link>
                    </div>
                </section>
            )}

            {/* Monthly spend + mileage trend */}
            {selectedVehicle && hasFuelLogs && (
                <section
                    className="animate-fade-up grid grid-cols-2 gap-3"
                    style={{ animationDelay: "200ms" }}
                >
                    <div className="surface-panel px-5 py-5">
                        <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                            This month
                        </p>
                        {fuelLogsLoading ? (
                            <Skeleton className="mt-2 h-9 w-24" />
                        ) : (
                            <>
                                <p className="font-heading mt-2 text-3xl font-extrabold tracking-wide">
                                    ₹{thisMonthSpend.toLocaleString("en-IN")}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    {lastMonthSpend > 0
                                        ? `vs ₹${lastMonthSpend.toLocaleString("en-IN")} last month`
                                        : "Fuel spend"}
                                </p>
                            </>
                        )}
                    </div>

                    <div className="surface-panel px-5 py-5">
                        <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                            Mileage trend
                        </p>
                        {fuelLogsLoading ? (
                            <Skeleton className="mt-2 h-9 w-24" />
                        ) : mileageDelta !== null ? (
                            <>
                                <p className="font-heading mt-2 flex items-center gap-2 text-3xl font-extrabold tracking-wide">
                                    {mileageDelta > 0 ? (
                                        <TrendingUp className="h-6 w-6 text-emerald-400" />
                                    ) : mileageDelta < 0 ? (
                                        <TrendingDown className="h-6 w-6 text-brand" />
                                    ) : null}
                                    {mileageDelta > 0 ? "+" : ""}
                                    {mileageDelta}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    km/l vs last month
                                    {thisMonthMileage !== null &&
                                        ` · ${thisMonthMileage} now`}
                                </p>
                            </>
                        ) : (
                            <>
                                <p className="font-heading mt-2 text-3xl font-extrabold tracking-wide">
                                    {thisMonthMileage ?? averageMileage ?? "—"}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    {thisMonthMileage !== null
                                        ? "km/l this month"
                                        : "Need more months of data"}
                                </p>
                            </>
                        )}
                    </div>
                </section>
            )}

            {/* Empty fuel state */}
            {selectedVehicle && !fuelLogsLoading && !hasFuelLogs && (
                <section
                    className="animate-fade-up surface-panel px-6 py-8 text-center sm:px-8"
                    style={{ animationDelay: "200ms" }}
                >
                    <Fuel className="mx-auto h-8 w-8 text-brand" />
                    <h2 className="font-heading mt-3 text-2xl font-bold uppercase tracking-wide">
                        Log your first fill-up
                    </h2>
                    <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
                        Mileage averages and monthly spend unlock after a couple of
                        tanks.
                    </p>
                    <Link
                        to={fuelHref}
                        className={cn(
                            buttonVariants(),
                            "mt-5 inline-flex bg-brand text-brand-foreground hover:bg-brand/90"
                        )}
                    >
                        Log fill-up
                        <ArrowRight className="ml-1 h-4 w-4" />
                    </Link>
                </section>
            )}

            {/* Empty service state */}
            {selectedVehicle &&
                !nextServiceLoading &&
                !nextService?.next_service_date && (
                    <section
                        className="animate-fade-up surface-panel flex flex-col gap-4 px-6 py-6 sm:flex-row sm:items-center sm:justify-between sm:px-8"
                        style={{ animationDelay: "240ms" }}
                    >
                        <div>
                            <p className="text-xs font-bold uppercase tracking-[0.22em] text-brand">
                                Service
                            </p>
                            <p className="font-heading mt-1 text-xl font-bold uppercase tracking-wide">
                                No service date set
                            </p>
                            <p className="mt-1 text-sm text-muted-foreground">
                                Log a service so we can remind you before it&apos;s
                                due.
                            </p>
                        </div>
                        <Link
                            to={serviceHref}
                            className={cn(
                                buttonVariants({ size: "sm" }),
                                "shrink-0 bg-brand text-brand-foreground hover:bg-brand/90"
                            )}
                        >
                            Log service
                            <ArrowRight className="ml-1 h-4 w-4" />
                        </Link>
                    </section>
                )}

            {/* Recent fill-ups */}
            {selectedVehicle && recentFuelLogs.length > 0 && (
                <section
                    className="animate-fade-up"
                    style={{ animationDelay: "260ms" }}
                >
                    <div className="mb-4 flex items-center justify-between">
                        <p className="text-xs font-bold uppercase tracking-[0.22em] text-brand">
                            Recent fill-ups
                        </p>
                        <Link
                            to={vehicleHref}
                            className="flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
                        >
                            View all
                            <ChevronRight className="h-3.5 w-3.5" />
                        </Link>
                    </div>

                    <div className="space-y-2">
                        {recentFuelLogs.map((log) => (
                            <Link
                                key={log.id}
                                to={vehicleHref}
                                className="surface-panel flex items-center justify-between gap-4 px-5 py-4 transition-colors hover:border-brand/40"
                            >
                                <div className="flex min-w-0 items-center gap-3">
                                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand/15">
                                        <Fuel className="h-4 w-4 text-brand" />
                                    </div>
                                    <div className="min-w-0">
                                        <p className="text-sm font-medium">
                                            ₹
                                            {log.total_cost.toLocaleString("en-IN")}
                                        </p>
                                        <p className="text-xs text-muted-foreground">
                                            {format(new Date(log.date), "dd MMM yyyy")}{" "}
                                            · {log.odometer.toLocaleString("en-IN")} km
                                        </p>
                                    </div>
                                </div>
                                {log.mileage !== null && (
                                    <Badge className="shrink-0 border-0 bg-brand/15 text-xs font-semibold text-brand">
                                        {log.mileage} km/l
                                    </Badge>
                                )}
                            </Link>
                        ))}
                    </div>
                </section>
            )}
        </div>
    );
}
