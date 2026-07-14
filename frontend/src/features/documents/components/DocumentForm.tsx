import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ChevronDown, FileText, Loader2, Upload } from "lucide-react";
import { isAxiosError } from "axios";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import {
    documentSchema,
    type DocumentSchema,
    DOCUMENT_TYPES,
    DOCUMENT_LABELS,
} from "../schemas";
import type { Document } from "../types";

interface DocumentFormProps {
    /** Pass a document to pre-fill the form for editing */
    defaultValues?: Document;
    onSubmit: (values: DocumentSchema & { file?: File }) => void;
    isPending: boolean;
    error: Error | null;
}

/**
 * Reusable document form used for both upload and edit.
 * File is optional when editing (replace); required when uploading.
 */
export default function DocumentForm({
    defaultValues,
    onSubmit,
    isPending,
    error,
}: DocumentFormProps) {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [fileError, setFileError] = useState<string | null>(null);
    const [typeMenuOpen, setTypeMenuOpen] = useState(false);
    const fileRef = useRef<HTMLInputElement>(null);
    const typeMenuRef = useRef<HTMLDivElement>(null);
    const isEditing = !!defaultValues;

    const {
        register,
        handleSubmit,
        reset,
        setValue,
        watch,
        formState: { errors },
    } = useForm<DocumentSchema>({
        resolver: zodResolver(documentSchema),
        defaultValues: {
            document_type: defaultValues?.document_type,
            expiry_date: defaultValues?.expiry_date ?? "",
            notes: defaultValues?.notes ?? "",
        },
    });

    const documentType = watch("document_type");

    useEffect(() => {
        if (!defaultValues) return;
        setSelectedFile(null);
        setFileError(null);
        setTypeMenuOpen(false);
        reset({
            document_type: defaultValues.document_type,
            expiry_date: defaultValues.expiry_date ?? "",
            notes: defaultValues.notes ?? "",
        });
    }, [defaultValues, reset]);

    useEffect(() => {
        if (!typeMenuOpen) return;

        const handlePointerDown = (event: MouseEvent) => {
            if (
                typeMenuRef.current &&
                !typeMenuRef.current.contains(event.target as Node)
            ) {
                setTypeMenuOpen(false);
            }
        };

        document.addEventListener("mousedown", handlePointerDown);
        return () => document.removeEventListener("mousedown", handlePointerDown);
    }, [typeMenuOpen]);

    const apiError = isAxiosError(error)
        ? (error.response?.data?.detail ?? "Something went wrong. Please try again.")
        : null;

    const inputClass = "border-white/15 bg-white/5";

    const handleFormSubmit = (values: DocumentSchema) => {
        if (!isEditing && !selectedFile) {
            setFileError("Please select a file to upload");
            return;
        }
        setFileError(null);
        onSubmit({
            ...values,
            file: selectedFile ?? undefined,
        });
    };

    return (
        <form
            onSubmit={handleSubmit(handleFormSubmit)}
            className="flex flex-col gap-6"
        >
            {apiError && (
                <div className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                    {typeof apiError === "string" ? apiError : "Something went wrong."}
                </div>
            )}

            <div className="relative overflow-hidden rounded-2xl border border-brand/30 bg-brand/10 px-5 py-5">
                <div
                    aria-hidden
                    className="absolute inset-y-0 left-0 w-1 bg-brand"
                />
                <p className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-[0.16em] text-brand/80">
                    <FileText className="h-3.5 w-3.5" />
                    Vault
                </p>
                <p className="font-heading mt-1 text-2xl font-extrabold tracking-wide">
                    {isEditing ? "Update document" : "Upload document"}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                    PDF, JPEG, or PNG · max 10 MB
                </p>
            </div>

            <div className="space-y-4">
                <div className="space-y-1.5">
                    <Label id="document_type_label">Document type</Label>
                    <div ref={typeMenuRef} className="relative">
                        <button
                            type="button"
                            id="document_type"
                            aria-haspopup="listbox"
                            aria-expanded={typeMenuOpen}
                            aria-labelledby="document_type_label"
                            className={cn(
                                "flex h-9 w-full items-center justify-between rounded-md border px-3 text-sm outline-none transition-colors",
                                inputClass,
                                "text-foreground hover:border-brand/40 focus-visible:border-brand"
                            )}
                            onClick={() => setTypeMenuOpen((open) => !open)}
                        >
                            <span
                                className={cn(
                                    !documentType && "text-muted-foreground"
                                )}
                            >
                                {documentType
                                    ? DOCUMENT_LABELS[documentType]
                                    : "Select document type"}
                            </span>
                            <ChevronDown
                                className={cn(
                                    "h-4 w-4 shrink-0 text-muted-foreground transition-transform",
                                    typeMenuOpen && "rotate-180"
                                )}
                            />
                        </button>

                        {typeMenuOpen && (
                            <ul
                                role="listbox"
                                aria-labelledby="document_type_label"
                                className="absolute z-20 mt-1 w-full overflow-hidden rounded-md border border-white/10 bg-popover py-1 shadow-lg"
                            >
                                {DOCUMENT_TYPES.map((type) => {
                                    const selected = documentType === type;
                                    return (
                                        <li key={type} role="option" aria-selected={selected}>
                                            <button
                                                type="button"
                                                className={cn(
                                                    "flex w-full px-3 py-2 text-left text-sm transition-colors",
                                                    selected
                                                        ? "bg-brand/20 font-medium text-brand"
                                                        : "text-foreground hover:bg-white/10"
                                                )}
                                                onClick={() => {
                                                    setValue("document_type", type, {
                                                        shouldValidate: true,
                                                    });
                                                    setTypeMenuOpen(false);
                                                }}
                                            >
                                                {DOCUMENT_LABELS[type]}
                                            </button>
                                        </li>
                                    );
                                })}
                            </ul>
                        )}
                    </div>
                    <input type="hidden" {...register("document_type")} />
                    {errors.document_type && (
                        <p className="text-xs text-destructive">
                            {errors.document_type.message}
                        </p>
                    )}
                </div>

                <div className="space-y-1.5">
                    <Label htmlFor="expiry_date">
                        Expiry date{" "}
                        <span className="text-xs text-muted-foreground">(optional)</span>
                    </Label>
                    <Input
                        id="expiry_date"
                        type="date"
                        className={inputClass}
                        {...register("expiry_date")}
                    />
                </div>

                <div className="space-y-1.5">
                    <Label htmlFor="notes">
                        Notes{" "}
                        <span className="text-xs text-muted-foreground">(optional)</span>
                    </Label>
                    <Input
                        id="notes"
                        type="text"
                        placeholder="e.g. Comprehensive insurance, Policy #123"
                        className={inputClass}
                        {...register("notes")}
                    />
                </div>

                <div className="space-y-1.5">
                    <Label>
                        {isEditing ? "Replace file" : "File"}{" "}
                        {isEditing && (
                            <span className="text-xs text-muted-foreground">
                                (optional)
                            </span>
                        )}
                    </Label>
                    <button
                        type="button"
                        className="w-full cursor-pointer rounded-lg border-2 border-dashed border-white/15 bg-white/5 p-6 text-center transition-colors hover:border-brand/50"
                        onClick={() => fileRef.current?.click()}
                    >
                        <Upload className="mx-auto mb-2 h-6 w-6 text-brand" />
                        {selectedFile ? (
                            <p className="text-sm font-medium">{selectedFile.name}</p>
                        ) : (
                            <>
                                <p className="text-sm text-muted-foreground">
                                    {isEditing
                                        ? `Current: ${defaultValues?.original_filename}`
                                        : "Click to upload PDF, JPEG, or PNG"}
                                </p>
                                <p className="mt-1 text-xs text-muted-foreground">
                                    Max 10MB
                                </p>
                            </>
                        )}
                    </button>
                    <input
                        ref={fileRef}
                        type="file"
                        accept=".pdf,.jpg,.jpeg,.png"
                        className="hidden"
                        onChange={(e) => {
                            setSelectedFile(e.target.files?.[0] ?? null);
                            setFileError(null);
                        }}
                    />
                    {fileError && (
                        <p className="text-xs text-destructive">{fileError}</p>
                    )}
                </div>
            </div>

            <Button
                type="submit"
                className="w-full bg-brand text-brand-foreground hover:bg-brand/90"
                disabled={isPending}
            >
                {isPending ? (
                    <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        {isEditing ? "Saving..." : "Uploading..."}
                    </>
                ) : isEditing ? (
                    "Save changes"
                ) : (
                    "Upload document"
                )}
            </Button>
        </form>
    );
}
