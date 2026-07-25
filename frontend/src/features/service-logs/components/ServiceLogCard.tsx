import { Calendar, Gauge, Wrench, Trash2, Pencil, ArrowRight } from "lucide-react";
import { format } from "date-fns";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
        <Card className="border-white/10 bg-card/90 transition-colors hover:border-brand/40">
            <CardContent className="pt-4">
                <div className="flex items-stretch gap-4">
                    {/* Primary — cost */}
                    <div className="flex min-w-[6.5rem] flex-col justify-center border-r border-white/10 pr-4 sm:min-w-[7.5rem]">
                        <p className="font-heading text-3xl font-extrabold leading-none tracking-wide text-brand sm:text-4xl">
                            ₹{log.total_cost.toLocaleString("en-IN")}
                        </p>
                        <p className="mt-1 text-[11px] font-bold uppercase tracking-[0.16em] text-brand/80">
                            spent
                        </p>
                    </div>

                    {/* Secondary details */}
                    <div className="min-w-0 flex-1 space-y-2.5">
                        <div className="flex items-start justify-between gap-2">
                            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
                                <div className="flex items-center gap-1.5">
                                    <Calendar className="h-3.5 w-3.5 shrink-0 text-brand" />
                                    <span>
                                        {format(new Date(log.date), "dd MMM yyyy")}
                                    </span>
                                </div>
                                <div className="flex items-center gap-1.5">
                                    <Gauge className="h-3.5 w-3.5 shrink-0 text-brand" />
                                    <span>
                                        {log.odometer.toLocaleString("en-IN")} km
                                    </span>
                                </div>
                            </div>

                            <div className="flex shrink-0 gap-1">
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8"
                                    onClick={() => onEdit(log)}
                                >
                                    <Pencil className="h-3.5 w-3.5" />
                                    <span className="sr-only">Edit service log</span>
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8 text-destructive hover:text-destructive"
                                    onClick={() => onDelete(log.id)}
                                >
                                    <Trash2 className="h-3.5 w-3.5" />
                                    <span className="sr-only">Delete service log</span>
                                </Button>
                            </div>
                        </div>

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
                                    <span>
                                        {format(
                                            new Date(log.next_service_date),
                                            "dd MMM yyyy"
                                        )}
                                    </span>
                                )}
                                {log.next_service_odometer && (
                                    <span>
                                        ·{" "}
                                        {log.next_service_odometer.toLocaleString(
                                            "en-IN"
                                        )}{" "}
                                        km
                                    </span>
                                )}
                            </div>
                        )}

                        {log.notes && (
                            <p className="truncate text-xs text-muted-foreground">
                                {log.notes}
                            </p>
                        )}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
