import { Gauge, Wrench, ArrowRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import LogEntryCard from "@/components/common/LogEntryCard";
import { formatAppDate } from "@/lib/date";
import type { ServiceLog } from "../types";

interface ServiceLogCardProps {
    log: ServiceLog;
    onEdit: (log: ServiceLog) => void;
    onDelete: (id: string) => void;
}

/**
 * Displays a single service log entry.
 * Cost is the primary metric; services done shown as badges.
 */
export default function ServiceLogCard({
    log,
    onEdit,
    onDelete,
}: ServiceLogCardProps) {
    return (
        <LogEntryCard
            primary={
                <>
                    <p className="font-heading text-3xl font-extrabold leading-none tracking-wide text-brand sm:text-4xl">
                        ₹{log.total_cost.toLocaleString("en-IN")}
                    </p>
                    <p className="mt-1 text-[11px] font-bold uppercase tracking-[0.16em] text-brand/80">
                        spent
                    </p>
                </>
            }
            date={log.date}
            headerExtra={
                <div className="flex items-center gap-1.5">
                    <Gauge className="h-3.5 w-3.5 shrink-0 text-brand" />
                    <span>{log.odometer.toLocaleString("en-IN")} km</span>
                </div>
            }
            onEdit={() => onEdit(log)}
            onDelete={() => onDelete(log.id)}
            editLabel="Edit service log"
            deleteLabel="Delete service log"
        >
            {log.service_center && (
                <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                    <Wrench className="h-3.5 w-3.5 shrink-0 text-brand" />
                    <span className="truncate">{log.service_center}</span>
                </div>
            )}

            <div className="flex flex-wrap gap-1.5">
                {log.services_done.map((service) => (
                    <Badge
                        key={service}
                        variant="secondary"
                        className="border-0 bg-white/10 text-xs font-medium text-foreground"
                    >
                        {service}
                    </Badge>
                ))}
            </div>

            {(log.next_service_date || log.next_service_odometer) && (
                <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
                    <ArrowRight className="h-3 w-3 shrink-0 text-brand" />
                    <span>Next service:</span>
                    {log.next_service_date && (
                        <span>{formatAppDate(log.next_service_date)}</span>
                    )}
                    {log.next_service_odometer && (
                        <span>
                            · {log.next_service_odometer.toLocaleString("en-IN")} km
                        </span>
                    )}
                </div>
            )}

            {log.notes && (
                <p className="truncate text-xs text-muted-foreground">{log.notes}</p>
            )}
        </LogEntryCard>
    );
}
