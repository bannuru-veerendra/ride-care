import {
    FileText,
    Calendar,
    ExternalLink,
    Trash2,
    Pencil,
    AlertTriangle,
} from "lucide-react";
import { format, differenceInDays } from "date-fns";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DOCUMENT_LABELS } from "../schemas";
import type { Document } from "../types";

interface DocumentCardProps {
    document: Document;
    onEdit: (document: Document) => void;
    onDelete: (id: string) => void;
}

/**
 * Displays a single document entry.
 * Document type is the primary signal; expiry warnings call out renewals.
 */
export default function DocumentCard({
    document,
    onEdit,
    onDelete,
}: DocumentCardProps) {
    const daysUntilExpiry = document.expiry_date
        ? differenceInDays(new Date(document.expiry_date), new Date())
        : null;

    const isExpiringSoon =
        daysUntilExpiry !== null && daysUntilExpiry <= 30 && daysUntilExpiry >= 0;
    const isExpired = daysUntilExpiry !== null && daysUntilExpiry < 0;

    return (
        <Card className="border-white/10 bg-card/90 transition-colors hover:border-brand/40">
            <CardContent className="pt-4">
                <div className="flex items-stretch gap-4">
                    {/* Primary — document type */}
                    <div className="flex min-w-[6.5rem] flex-col justify-center border-r border-white/10 pr-4 sm:min-w-[7.5rem]">
                        <FileText className="mb-2 h-5 w-5 text-brand" />
                        <p className="font-heading text-lg font-extrabold leading-tight tracking-wide text-brand sm:text-xl">
                            {DOCUMENT_LABELS[document.document_type]}
                        </p>
                    </div>

                    {/* Secondary details */}
                    <div className="min-w-0 flex-1 space-y-2.5">
                        <div className="flex items-start justify-between gap-2">
                            <Badge className="max-w-full truncate rounded-md border-0 bg-brand/15 text-xs font-medium text-brand">
                                {document.original_filename}
                            </Badge>

                            <div className="flex shrink-0 gap-1">
                                {document.signed_url && (
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-8 w-8"
                                        onClick={() =>
                                            window.open(document.signed_url, "_blank")
                                        }
                                    >
                                        <ExternalLink className="h-3.5 w-3.5" />
                                        <span className="sr-only">View document</span>
                                    </Button>
                                )}
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8"
                                    onClick={() => onEdit(document)}
                                >
                                    <Pencil className="h-3.5 w-3.5" />
                                    <span className="sr-only">Edit document</span>
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8 text-destructive hover:text-destructive"
                                    onClick={() => onDelete(document.id)}
                                >
                                    <Trash2 className="h-3.5 w-3.5" />
                                    <span className="sr-only">Delete document</span>
                                </Button>
                            </div>
                        </div>

                        {document.expiry_date && (
                            <div className="flex flex-wrap items-center gap-1.5 text-sm text-muted-foreground">
                                <Calendar className="h-3.5 w-3.5 shrink-0 text-brand" />
                                <span>
                                    Expires{" "}
                                    {format(
                                        new Date(document.expiry_date),
                                        "dd MMM yyyy"
                                    )}
                                </span>
                                {isExpired && (
                                    <Badge
                                        variant="destructive"
                                        className="gap-1 text-xs"
                                    >
                                        <AlertTriangle className="h-3 w-3" />
                                        Expired
                                    </Badge>
                                )}
                                {isExpiringSoon && !isExpired && (
                                    <Badge className="gap-1 border-0 bg-brand/15 text-xs text-brand">
                                        <AlertTriangle className="h-3 w-3" />
                                        Expires in {daysUntilExpiry} days
                                    </Badge>
                                )}
                            </div>
                        )}

                        {document.notes && (
                            <p className="truncate text-xs text-muted-foreground">
                                {document.notes}
                            </p>
                        )}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
