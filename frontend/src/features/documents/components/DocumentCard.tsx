import { useEffect, useRef, useState } from "react";
import {
    FileText,
    Calendar,
    ExternalLink,
    Download,
    Trash2,
    Pencil,
    AlertTriangle,
    MoreHorizontal,
} from "lucide-react";
import { format } from "date-fns";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DOCUMENT_LABELS } from "../schemas";
import type { Document } from "../types";
import { cn } from "@/lib/utils";

interface DocumentCardProps {
    document: Document;
    onEdit: (document: Document) => void;
    onDelete: (id: string) => void;
}

async function downloadSignedFile(url: string, filename: string) {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error("Download failed");
        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);
        const link = window.document.createElement("a");
        link.href = objectUrl;
        link.download = filename;
        link.click();
        URL.revokeObjectURL(objectUrl);
    } catch {
        window.open(url, "_blank", "noopener,noreferrer");
    }
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
    const [menuOpen, setMenuOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);

    // Urgency fields come from the API (DOCUMENT_SOON_DAYS lives on the backend).
    const daysUntilExpiry = document.days_until;
    const isExpired = document.expiry_status === "expired";
    const isExpiringSoon = document.expiry_status === "soon";

    useEffect(() => {
        if (!menuOpen) return;

        const onPointerDown = (event: MouseEvent) => {
            if (!menuRef.current?.contains(event.target as Node)) {
                setMenuOpen(false);
            }
        };
        const onKeyDown = (event: KeyboardEvent) => {
            if (event.key === "Escape") setMenuOpen(false);
        };

        window.document.addEventListener("mousedown", onPointerDown);
        window.document.addEventListener("keydown", onKeyDown);
        return () => {
            window.document.removeEventListener("mousedown", onPointerDown);
            window.document.removeEventListener("keydown", onKeyDown);
        };
    }, [menuOpen]);

    return (
        <Card className="overflow-visible border-white/10 bg-card/90 transition-colors hover:border-brand/40">
            <CardContent className="pt-4">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-stretch">
                    <div className="flex items-center gap-3 border-b border-white/10 pb-3 sm:min-w-[7.5rem] sm:flex-col sm:items-start sm:justify-center sm:border-b-0 sm:border-r sm:pb-0 sm:pr-4">
                        <FileText className="h-5 w-5 shrink-0 text-brand" />
                        <p className="font-heading text-lg font-extrabold leading-tight tracking-wide text-brand sm:text-xl">
                            {DOCUMENT_LABELS[document.document_type]}
                        </p>
                    </div>

                    <div className="min-w-0 flex-1 space-y-2.5">
                        <div className="flex items-start justify-between gap-2">
                            <Badge className="max-w-[min(100%,12rem)] truncate rounded-md border-0 bg-brand/15 text-xs font-medium text-brand sm:max-w-full">
                                {document.original_filename}
                            </Badge>

                            <div className="flex shrink-0 items-center gap-0.5">
                                {document.signed_url && (
                                    <>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-9 w-9 sm:h-8 sm:w-8"
                                            onClick={() =>
                                                window.open(
                                                    document.signed_url,
                                                    "_blank",
                                                    "noopener,noreferrer"
                                                )
                                            }
                                        >
                                            <ExternalLink className="h-4 w-4 sm:h-3.5 sm:w-3.5" />
                                            <span className="sr-only">View document</span>
                                        </Button>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-9 w-9 sm:h-8 sm:w-8"
                                            onClick={() =>
                                                void downloadSignedFile(
                                                    document.signed_url!,
                                                    document.original_filename
                                                )
                                            }
                                        >
                                            <Download className="h-4 w-4 sm:h-3.5 sm:w-3.5" />
                                            <span className="sr-only">
                                                Download document
                                            </span>
                                        </Button>
                                    </>
                                )}

                                <div ref={menuRef} className="relative">
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="h-9 w-9 sm:h-8 sm:w-8"
                                        aria-expanded={menuOpen}
                                        aria-haspopup="menu"
                                        onClick={() => setMenuOpen((open) => !open)}
                                    >
                                        <MoreHorizontal className="h-4 w-4 sm:h-3.5 sm:w-3.5" />
                                        <span className="sr-only">More actions</span>
                                    </Button>

                                    {menuOpen ? (
                                        <div
                                            role="menu"
                                            className={cn(
                                                "absolute right-0 top-full z-50 mt-1 min-w-40",
                                                "rounded-lg border border-white/10 bg-background p-1",
                                                "shadow-lg"
                                            )}
                                        >
                                            <button
                                                type="button"
                                                role="menuitem"
                                                onClick={() => {
                                                    setMenuOpen(false);
                                                    onEdit(document);
                                                }}
                                                className="flex w-full cursor-pointer items-center gap-2 rounded-md px-3 py-2.5 text-sm text-muted-foreground transition-colors hover:bg-white/5 hover:text-foreground"
                                            >
                                                <Pencil className="size-3.5" />
                                                Edit
                                            </button>
                                            <button
                                                type="button"
                                                role="menuitem"
                                                onClick={() => {
                                                    setMenuOpen(false);
                                                    onDelete(document.id);
                                                }}
                                                className="flex w-full cursor-pointer items-center gap-2 rounded-md px-3 py-2.5 text-sm text-destructive transition-colors hover:bg-destructive/10"
                                            >
                                                <Trash2 className="size-3.5" />
                                                Delete
                                            </button>
                                        </div>
                                    ) : null}
                                </div>
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
                                {isExpiringSoon && !isExpired && daysUntilExpiry != null && (
                                    <Badge className="gap-1 border-0 bg-brand/15 text-xs text-brand">
                                        <AlertTriangle className="h-3 w-3" />
                                        Expires in {daysUntilExpiry} day
                                        {daysUntilExpiry === 1 ? "" : "s"}
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
