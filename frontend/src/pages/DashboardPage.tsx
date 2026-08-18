import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
    AlertTriangle,
    ArrowRight,
    ChevronRight,
    FileText,
    Fuel,
    Gauge,
    TrendingDown,
    TrendingUp,
    Wrench,
} from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import RideCareLogo from "@/components/common/RideCareLogo";
import {
    useVehicles,
    useVehicleSummary,
} from "@/features/vehicles/hooks/useVehicles";
import { DOCUMENT_LABELS } from "@/features/documents/schemas";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { formatAppDate } from "@/lib/date";
import type { Vehicle } from "@/features/vehicles/types";

const SELECTED_VEHICLE_KEY = "ridecare-dashboard-vehicle";

/** Friendly remaining time: "12d", or "1 month 10 days" when over a month. */
function formatServiceCountdown(days: number): string {
    if (days <= 30) {
        return `${days}d`;
    }
    const months = Math.floor(days / 30);
    const remDays = days % 30;
    const monthPart = `${months} month${months === 1 ? "" : "s"}`;
    if (remDays === 0) {
        return monthPart;
    }
    return `${monthPart} ${remDays} day${remDays === 1 ? "" : "s"}`;
}

/**
 * Dashboard home — actionable hub for returning riders.
 */
export default function DashboardPage() {
    const { data: vehiclesPage, isLoading: vehiclesLoading } = useVehicles();
    const vehicles = vehiclesPage?.items ?? [];
    const count = vehiclesPage?.total ?? 0;

    const [selectedVehicleId, setSelectedVehicleId] = useState(
        () => localStorage.getItem(SELECTED_VEHICLE_KEY) ?? ""
    );

    useEffect(() => {
        if (!vehicles.length) {
            if (!vehiclesLoading) {
                setSelectedVehicleId("");
            }
            return;
        }

        const match = vehicles.find((vehicle) => vehicle.id === selectedVehicleId);
        if (!match) {
            setSelectedVehicleId(vehicles[0].id);
        }
    }, [vehicles, vehiclesLoading, selectedVehicleId]);

    const handleSelectVehicle = (id: string) => {
        setSelectedVehicleId(id);
        localStorage.setItem(SELECTED_VEHICLE_KEY, id);
    };

    const selectedVehicle: Vehicle | undefined =
        vehicles.find((vehicle) => vehicle.id === selectedVehicleId) ??
        vehicles[0];

    const { data: summary, isLoading: summaryLoading } = useVehicleSummary(
        selectedVehicleId
    );

    const recentFuelLogs = summary?.recent_fuel_logs ?? [];
    const hasFuelLogs = (summary?.fuel_log_count ?? 0) > 0;
    const averageMileage = summary?.average_mileage ?? null;
    const thisMonthSpend = summary?.this_month_spend ?? 0;
    const lastMonthSpend = summary?.last_month_spend ?? 0;
    const recentFilledMileage = summary?.recent_filled_month_mileage ?? null;
    const priorFilledMileage = summary?.prior_filled_month_mileage ?? null;
    const recentFilledLabel = summary?.recent_filled_month_label ?? null;
    const priorFilledLabel = summary?.prior_filled_month_label ?? null;
    // Urgency comes from the API — do not re-derive thresholds on the client.
    const serviceReminder = summary?.service_reminder;
    const documentReminders = summary?.document_reminders ?? [];
    const mileageDelta =
        recentFilledMileage !== null && priorFilledMileage !== null
            ? Math.round((recentFilledMileage - priorFilledMileage) * 10) / 10
            : null;

    const hasNextService =
        serviceReminder != null &&
        serviceReminder.status !== "none" &&
        (serviceReminder.next_service_date != null ||
            serviceReminder.next_service_odometer != null);

    const daysUntilNextService = serviceReminder?.days_until ?? null;
    const kmUntilNextService = serviceReminder?.km_until ?? null;
    const nextServiceDate = serviceReminder?.next_service_date ?? null;
    const serviceOverdue = serviceReminder?.status === "overdue";
    const serviceSoon = serviceReminder?.status === "soon";

    const showReminders =
        !!selectedVehicleId &&
        (serviceOverdue || serviceSoon || documentReminders.length > 0);

    const fuelHref = selectedVehicleId
        ? `/vehicles/${selectedVehicleId}?action=fuel`
        : "/vehicles";
    const serviceHref = selectedVehicleId
        ? `/vehicles/${selectedVehicleId}?action=service`
        : "/vehicles";
    const serviceTabHref = selectedVehicleId
        ? `/vehicles/${selectedVehicleId}?tab=service`
        : "/vehicles";
    const documentsTabHref = selectedVehicleId
        ? `/vehicles/${selectedVehicleId}?tab=documents`
        : "/vehicles";
    const vehicleHref = selectedVehicleId
        ? `/vehicles/${selectedVehicleId}`
        : "/vehicles";

    let statusLine = "Ready when you are.";
    if (selectedVehicleId) {
        if (serviceOverdue) {
            statusLine = "Service overdue — book it soon.";
        } else if (serviceSoon && daysUntilNextService !== null && daysUntilNextService >= 0) {
            statusLine = `Service in ${daysUntilNextService} day${daysUntilNextService === 1 ? "" : "s"}.`;
        } else if (serviceSoon && kmUntilNextService !== null) {
            statusLine = `Service in ${kmUntilNextService.toLocaleString("en-IN")} km.`;
        } else if (documentReminders.some((doc) => doc.status === "expired")) {
            statusLine = "A document has expired — renew it.";
        } else if (documentReminders.some((doc) => doc.status === "soon")) {
            statusLine = "A document expires soon.";
        } else if (!hasFuelLogs) {
            statusLine = "Add a fill-up to unlock mileage insights.";
        } else {
            statusLine = "Good to ride.";
        }
    }

    // First visit (no saved bike): wait for the list. Returning riders already
    // have an id in localStorage, so summary can load in parallel with the list.
    if (vehiclesLoading && !selectedVehicleId) {
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
    if (!vehiclesLoading && count === 0) {
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

                <div className="relative z-10 flex flex-col justify-end gap-3 px-6 py-5 sm:flex-row sm:items-end sm:justify-between sm:px-10 sm:py-6">
                    <div className="animate-speed-in max-w-lg space-y-1.5">
                        <RideCareLogo to="/dashboard" compact={false} inverted />
                        <p className="text-sm text-white/80 sm:text-base">{statusLine}</p>
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

            {/* In-app reminders — service due + document expiry */}
            {showReminders && (
                <section
                    className="animate-fade-up space-y-2"
                    style={{ animationDelay: "40ms" }}
                >
                    <p className="text-xs font-bold uppercase tracking-[0.18em] text-muted-foreground">
                        Reminders
                    </p>
                    <div className="space-y-2">
                        {(serviceOverdue || serviceSoon) && (
                            <Link
                                to={serviceTabHref}
                                className={cn(
                                    "flex items-center gap-3 rounded-2xl border px-4 py-3 transition-colors",
                                    serviceOverdue
                                        ? "border-destructive/40 bg-destructive/10 hover:border-destructive/60"
                                        : "border-brand/30 bg-brand/10 hover:border-brand/50"
                                )}
                            >
                                <AlertTriangle
                                    className={cn(
                                        "h-4 w-4 shrink-0",
                                        serviceOverdue
                                            ? "text-destructive"
                                            : "text-brand"
                                    )}
                                />
                                <div className="min-w-0 flex-1">
                                    <p className="text-sm font-medium">
                                        {serviceOverdue
                                            ? "Service overdue"
                                            : "Service due soon"}
                                    </p>
                                    <p className="truncate text-xs text-muted-foreground">
                                        {daysUntilNextService !== null
                                            ? serviceOverdue
                                                ? `${Math.abs(daysUntilNextService)} day${Math.abs(daysUntilNextService) === 1 ? "" : "s"} past due`
                                                : `${daysUntilNextService} day${daysUntilNextService === 1 ? "" : "s"} left`
                                            : kmUntilNextService !== null
                                                ? serviceOverdue
                                                    ? `${Math.abs(kmUntilNextService).toLocaleString("en-IN")} km past due`
                                                    : `${kmUntilNextService.toLocaleString("en-IN")} km left`
                                                : "Check service schedule"}
                                    </p>
                                </div>
                                <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
                            </Link>
                        )}
                        {documentReminders.map((doc) => (
                            <Link
                                key={doc.id}
                                to={documentsTabHref}
                                className={cn(
                                    "flex items-center gap-3 rounded-2xl border px-4 py-3 transition-colors",
                                    doc.status === "expired"
                                        ? "border-destructive/40 bg-destructive/10 hover:border-destructive/60"
                                        : "border-brand/30 bg-brand/10 hover:border-brand/50"
                                )}
                            >
                                <FileText
                                    className={cn(
                                        "h-4 w-4 shrink-0",
                                        doc.status === "expired"
                                            ? "text-destructive"
                                            : "text-brand"
                                    )}
                                />
                                <div className="min-w-0 flex-1">
                                    <p className="text-sm font-medium">
                                        {(DOCUMENT_LABELS as Record<string, string>)[
                                            doc.document_type
                                        ] ?? doc.document_type}
                                        {doc.status === "expired"
                                            ? " expired"
                                            : " expires soon"}
                                    </p>
                                    <p className="truncate text-xs text-muted-foreground">
                                        {doc.status === "expired"
                                            ? `${Math.abs(doc.days_until)} day${Math.abs(doc.days_until) === 1 ? "" : "s"} ago`
                                            : `${doc.days_until} day${doc.days_until === 1 ? "" : "s"} left`}
                                        {" · "}
                                        {formatAppDate(doc.expiry_date)}
                                    </p>
                                </div>
                                <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
                            </Link>
                        ))}
                    </div>
                </section>
            )}

            {/* Quick actions */}
            {selectedVehicleId && (
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
                                    : "Track next due date & km"}
                            </p>
                        </div>
                    </Link>
                </section>
            )}

            {/* Quick stats */}
            {selectedVehicleId && (
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

                    {count === 1 && selectedVehicle && (
                        <p className="mb-3 text-sm text-muted-foreground">
                            {selectedVehicle.brand} {selectedVehicle.vehicle_name}
                        </p>
                    )}

                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                        <Card className="surface-panel h-full border-0">
                            <CardContent className="px-5 py-5">
                                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-muted-foreground">
                                    <Gauge className="h-3.5 w-3.5 text-brand" />
                                    Odometer
                                </div>
                                <p className="font-heading mt-2 text-3xl font-extrabold tracking-wide">
                                    {selectedVehicle
                                        ? selectedVehicle.current_odometer.toLocaleString(
                                              "en-IN"
                                          )
                                        : "—"}
                                </p>
                                <p className="text-xs text-muted-foreground">km</p>
                            </CardContent>
                        </Card>

                        <Card className="surface-panel h-full border-0">
                            <CardContent className="px-5 py-5">
                                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-muted-foreground">
                                    <Fuel className="h-3.5 w-3.5 text-brand" />
                                    Avg mileage
                                </div>
                                {summaryLoading ? (
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

                        <Card className="surface-panel col-span-2 h-full border-0 sm:col-span-1">
                            <CardContent className="px-5 py-5">
                                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-muted-foreground">
                                    <Wrench className="h-3.5 w-3.5 text-brand" />
                                    Next service
                                </div>
                                {summaryLoading ? (
                                    <Skeleton className="mt-2 h-9 w-32" />
                                ) : hasNextService ? (
                                    <>
                                        <p
                                            className={cn(
                                                "font-heading mt-2 font-extrabold tracking-wide",
                                                daysUntilNextService !== null &&
                                                    daysUntilNextService > 30
                                                    ? "text-xl leading-snug"
                                                    : "text-3xl"
                                            )}
                                        >
                                            {serviceOverdue
                                                ? "Overdue"
                                                : daysUntilNextService !== null &&
                                                    daysUntilNextService >= 0
                                                    ? formatServiceCountdown(
                                                        daysUntilNextService
                                                    )
                                                    : kmUntilNextService !== null
                                                        ? `${kmUntilNextService.toLocaleString("en-IN")} km left`
                                                        : "—"}
                                        </p>
                                        <div className="mt-1 flex flex-wrap items-center gap-1.5">
                                            <p className="text-xs text-muted-foreground">
                                                {[
                                                    nextServiceDate
                                                        ? formatAppDate(nextServiceDate)
                                                        : null,
                                                    // Show remaining km in the subtitle when the
                                                    // headline is already the date countdown.
                                                    kmUntilNextService != null &&
                                                    !serviceOverdue &&
                                                    daysUntilNextService !== null &&
                                                    daysUntilNextService >= 0
                                                        ? kmUntilNextService > 0
                                                            ? `${kmUntilNextService.toLocaleString("en-IN")} km left`
                                                            : "due now"
                                                        : serviceOverdue &&
                                                            kmUntilNextService != null &&
                                                            kmUntilNextService < 0
                                                            ? `${Math.abs(kmUntilNextService).toLocaleString("en-IN")} km past`
                                                            : null,
                                                ]
                                                    .filter(Boolean)
                                                    .join(" · ")}
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
                                            Not set
                                        </p>
                                    </>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </section>
            )}

            {/* Monthly spend + mileage trend */}
            {selectedVehicleId && hasFuelLogs && (
                <section
                    className="animate-fade-up grid grid-cols-2 gap-3"
                    style={{ animationDelay: "200ms" }}
                >
                    <div className="surface-panel px-5 py-5">
                        <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                            This month
                        </p>
                        {summaryLoading ? (
                            <Skeleton className="mt-2 h-9 w-24" />
                        ) : thisMonthSpend > 0 ? (
                            <>
                                <p className="font-heading mt-2 text-3xl font-extrabold tracking-wide">
                                    ₹{thisMonthSpend.toLocaleString("en-IN")}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    {lastMonthSpend > 0
                                        ? `vs ₹${lastMonthSpend.toLocaleString("en-IN")} last month`
                                        : "Fuel spend so far"}
                                </p>
                            </>
                        ) : (
                            <>
                                <p className="font-heading mt-2 text-3xl font-extrabold tracking-wide">
                                    ₹0
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    {lastMonthSpend > 0
                                        ? `No fill-ups yet · ₹${lastMonthSpend.toLocaleString("en-IN")} last month`
                                        : "No fill-ups logged this month"}
                                </p>
                            </>
                        )}
                    </div>

                    <div className="surface-panel px-5 py-5">
                        <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                            Mileage trend
                        </p>
                        {summaryLoading ? (
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
                                    km/l {recentFilledLabel} vs {priorFilledLabel}
                                    {recentFilledMileage !== null &&
                                        ` · ${recentFilledMileage} now`}
                                </p>
                            </>
                        ) : (
                            <>
                                <p className="font-heading mt-2 text-3xl font-extrabold tracking-wide text-muted-foreground">
                                    —
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    {recentFilledMileage !== null && recentFilledLabel
                                        ? `${recentFilledMileage} km/l in ${recentFilledLabel} · need another month to compare`
                                        : "Log fill-ups across 2 months to compare"}
                                </p>
                            </>
                        )}
                    </div>
                </section>
            )}

            {/* Empty fuel state */}
            {selectedVehicleId && !summaryLoading && !hasFuelLogs && (
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
            {selectedVehicleId &&
                !summaryLoading &&
                !hasNextService && (
                    <section
                        className="animate-fade-up surface-panel flex flex-col gap-4 px-6 py-6 sm:flex-row sm:items-center sm:justify-between sm:px-8"
                        style={{ animationDelay: "240ms" }}
                    >
                        <div>
                            <p className="text-xs font-bold uppercase tracking-[0.22em] text-brand">
                                Service
                            </p>
                            <p className="font-heading mt-1 text-xl font-bold uppercase tracking-wide">
                                No next service set
                            </p>
                            <p className="mt-1 text-sm text-muted-foreground">
                                Log a service with a due date or odometer so we can
                                remind you before it&apos;s due.
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
            {selectedVehicleId && recentFuelLogs.length > 0 && (
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
                                            {formatAppDate(log.date)}{" "}
                                            · {log.odometer.toLocaleString("en-IN")} km
                                        </p>
                                    </div>
                                </div>
                                {log.mileage !== null && (
                                    <Badge className="shrink-0 border-0 bg-brand/15 text-xs font-semibold text-brand">
                                        {log.mileage.toFixed(1)} km/l
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
