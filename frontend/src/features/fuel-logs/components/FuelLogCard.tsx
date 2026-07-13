import { Fuel, Gauge, Calendar, Trash2, Pencil } from "lucide-react";
import { format } from "date-fns";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
    return (
        <Card className="border-white/10 bg-card/90 transition-colors hover:border-brand/40">
            <CardContent className="pt-4">
                <div className="flex items-stretch gap-4">
                    {/* Primary — mileage */}
                    <div className="flex min-w-[6.5rem] flex-col justify-center border-r border-white/10 pr-4 sm:min-w-[7.5rem]">
                        {log.mileage !== null ? (
                            <>
                                <p className="font-heading text-4xl font-extrabold leading-none tracking-wide text-brand sm:text-5xl">
                                    {log.mileage}
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
                        )}
                    </div>

                    {/* Secondary details */}
                    <div className="min-w-0 flex-1 space-y-2.5">
                        <div className="flex items-start justify-between gap-2">
                            <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                                <Calendar className="h-3.5 w-3.5 shrink-0 text-brand" />
                                <span>{format(new Date(log.date), "dd MMM yyyy")}</span>
                            </div>

                            <div className="flex shrink-0 gap-1">
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8"
                                    onClick={() => onEdit(log)}
                                >
                                    <Pencil className="h-3.5 w-3.5" />
                                    <span className="sr-only">Edit fuel log</span>
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8 text-destructive hover:text-destructive"
                                    onClick={() => onDelete(log.id)}
                                >
                                    <Trash2 className="h-3.5 w-3.5" />
                                    <span className="sr-only">Delete fuel log</span>
                                </Button>
                            </div>
                        </div>

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
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
