import type { ReactNode } from "react";
import { Calendar, Pencil, Trash2 } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatAppDate } from "@/lib/date";

interface LogEntryCardProps {
    primary: ReactNode;
    date: string;
    onEdit: () => void;
    onDelete: () => void;
    editLabel: string;
    deleteLabel: string;
    headerExtra?: ReactNode;
    children: ReactNode;
}

/**
 * Shared chrome for fuel/service log cards: primary metric column + actions.
 */
export default function LogEntryCard({
    primary,
    date,
    onEdit,
    onDelete,
    editLabel,
    deleteLabel,
    headerExtra,
    children,
}: LogEntryCardProps) {
    return (
        <Card className="border-white/10 bg-card/90 transition-colors hover:border-brand/40">
            <CardContent className="pt-4">
                <div className="flex items-stretch gap-4">
                    <div className="flex min-w-[6.5rem] flex-col justify-center border-r border-white/10 pr-4 sm:min-w-[7.5rem]">
                        {primary}
                    </div>

                    <div className="min-w-0 flex-1 space-y-2.5">
                        <div className="flex items-start justify-between gap-2">
                            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
                                <div className="flex items-center gap-1.5">
                                    <Calendar className="h-3.5 w-3.5 shrink-0 text-brand" />
                                    <span>{formatAppDate(date)}</span>
                                </div>
                                {headerExtra}
                            </div>

                            <div className="flex shrink-0 gap-1">
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8"
                                    onClick={onEdit}
                                >
                                    <Pencil className="h-3.5 w-3.5" />
                                    <span className="sr-only">{editLabel}</span>
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8 text-destructive hover:text-destructive"
                                    onClick={onDelete}
                                >
                                    <Trash2 className="h-3.5 w-3.5" />
                                    <span className="sr-only">{deleteLabel}</span>
                                </Button>
                            </div>
                        </div>

                        {children}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
