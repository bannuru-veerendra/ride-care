import { Fuel, Gauge } from "lucide-react";

import LogEntryCard from "@/components/common/LogEntryCard";
import type { FuelLog } from "../types";

interface FuelLogCardProps {
    log: FuelLog;
    onDelete: (id: string) => void;
    onEdit: (log: FuelLog) => void;
}

/**
 * Displays a single fuel log entry.
 * Mileage (km/l) is the primary metric — that's why riders log fuel.
 * First fill-up has null mileage until a second log exists.
 */
export default function FuelLogCard({ log, onDelete, onEdit }: FuelLogCardProps) {
    const primary =
        log.mileage !== null ? (
            <>
                <p className="font-heading text-4xl font-extrabold leading-none tracking-wide text-brand sm:text-5xl">
                    {log.mileage.toFixed(1)}
                </p>
                <p className="mt-1 text-[11px] font-bold uppercase tracking-[0.16em] text-brand/80">
                    km/l
                </p>
            </>
        ) : (
            <>
                <p className="font-heading text-2xl font-bold uppercase tracking-wide text-muted-foreground">
                    —
                </p>
                <p className="mt-1 text-[11px] font-bold uppercase tracking-[0.16em] text-muted-foreground">
                    First fill
                </p>
            </>
        );

    return (
        <LogEntryCard
            primary={primary}
            date={log.date}
            onEdit={() => onEdit(log)}
            onDelete={() => onDelete(log.id)}
            editLabel="Edit fuel log"
            deleteLabel="Delete fuel log"
        >
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-sm text-muted-foreground">
                <div className="flex items-center gap-1.5">
                    <Gauge className="h-3.5 w-3.5 shrink-0 text-brand" />
                    <span>{log.odometer.toLocaleString("en-IN")} km</span>
                </div>
                <div className="flex items-center gap-1.5">
                    <Fuel className="h-3.5 w-3.5 shrink-0 text-brand" />
                    <span>{log.liters.toFixed(2)} L</span>
                </div>
                <span className="font-heading text-base font-bold tracking-wide text-foreground">
                    ₹{log.total_cost.toLocaleString("en-IN")}
                </span>
            </div>

            {log.notes && (
                <p className="truncate text-xs text-muted-foreground">{log.notes}</p>
            )}
        </LogEntryCard>
    );
}
