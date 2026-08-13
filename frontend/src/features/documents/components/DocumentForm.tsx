import { useEffect, useRef, useState, useCallback } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ChevronDown, FileText, Upload } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import FormErrorBanner from "@/components/common/FormErrorBanner";
import FormSubmitButton from "@/components/common/FormSubmitButton";
import { useDismissible } from "@/lib/use-dismissible";
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

    const closeTypeMenu = useCallback(() => setTypeMenuOpen(false), []);
    useDismissible(typeMenuOpen, typeMenuRef, closeTypeMenu);

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
            <FormErrorBanner error={error} />

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
                <p className="mt-1 text-sm text-muted-foreground">
                    PDF, JPEG, or PNG — max 10MB
                </p>
            </div>

            <div className="space-y-4">
                <div className="space-y-1.5">
                    <Label>Document type</Label>
                    <div ref={typeMenuRef} className="relative">
                        <button
                            type="button"
                            onClick={() => setTypeMenuOpen((open) => !open)}
                            className={cn(
                                "flex h-9 w-full items-center justify-between rounded-md border px-3 text-sm",
                                inputClass,
                                "border-input"
                            )}
                        >
                            <span>
                                {documentType
                                    ? DOCUMENT_LABELS[documentType]
                                    : "Select type"}
                            </span>
                            <ChevronDown className="h-4 w-4 opacity-60" />
                        </button>
                        {typeMenuOpen && (
                            <div className="absolute z-50 mt-1 w-full rounded-md border border-white/10 bg-background p-1 shadow-lg">
                                {DOCUMENT_TYPES.map((type) => (
                                    <button
                                        key={type}
                                        type="button"
                                        className="flex w-full cursor-pointer rounded-md px-3 py-2 text-left text-sm hover:bg-white/5"
                                        onClick={() => {
                                            setValue("document_type", type, {
                                                shouldValidate: true,
                                            });
                                            setTypeMenuOpen(false);
                                        }}
                                    >
                                        {DOCUMENT_LABELS[type]}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                    {errors.document_type && (
                        <p className="text-xs text-destructive">
                            {errors.document_type.message}
                        </p>
                    )}
                </div>

                <div className="space-y-1.5">
                    <Label htmlFor="expiry_date">
                        Expiry date{" "}
                        <span className="text-xs text-muted-foreground">
                            (optional)
                        </span>
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
                        <span className="text-xs text-muted-foreground">
                            (optional)
                        </span>
                    </Label>
                    <Input
                        id="notes"
                        className={inputClass}
                        placeholder="Policy number, remarks..."
                        {...register("notes")}
                    />
                </div>

                <div className="space-y-1.5">
                    <Label>{isEditing ? "Replace file" : "File"}</Label>
                    <button
                        type="button"
                        className={cn(
                            "w-full rounded-lg border border-dashed border-white/20 px-4 py-6 text-center transition-colors hover:border-brand/50",
                            inputClass
                        )}
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

            <FormSubmitButton
                isPending={isPending}
                isEdit={isEditing}
                createLabel="Upload document"
                pendingLabel={isEditing ? "Saving..." : "Uploading..."}
                className="w-full bg-brand text-brand-foreground hover:bg-brand/90"
            />
        </form>
    );
}
