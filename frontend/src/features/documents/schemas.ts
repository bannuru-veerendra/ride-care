import { z } from "zod";

/**
 * Built-in certificate types + Other (free-text custom_label).
 * Order: everyday renewals first, then RC, then Other.
 */
export const DOCUMENT_TYPES = [
    "insurance",
    "pollution",
    "driving_license",
    "registration_certificate",
    "other",
] as const;

export type DocumentTypeValue = (typeof DOCUMENT_TYPES)[number];

/** Matches backend MAX_DOCUMENT_TEXT_LENGTH for custom_label / identifier. */
export const MAX_DOCUMENT_TEXT_LENGTH = 120;

export const DOCUMENT_LABELS: Record<DocumentTypeValue, string> = {
    insurance: "Insurance",
    pollution: "Pollution",
    driving_license: "Driving Licence",
    registration_certificate: "Registration Certificate",
    other: "Other",
};

/** Field label for the certificate identity / number (RC has none — reg is on the vehicle). */
const IDENTIFIER_LABELS: Record<
    Exclude<DocumentTypeValue, "registration_certificate">,
    string
> = {
    insurance: "Policy number",
    pollution: "PUC number",
    driving_license: "DL number",
    other: "ID / reference",
};

export function documentAllowsExpiry(type: DocumentTypeValue): boolean {
    return type !== "registration_certificate";
}

/** RC already lives on the vehicle — skip a duplicate number field. */
export function documentShowsIdentifier(
    type: DocumentTypeValue
): type is Exclude<DocumentTypeValue, "registration_certificate"> {
    return type !== "registration_certificate";
}

export function documentIdentifierLabel(type: DocumentTypeValue): string | null {
    if (!documentShowsIdentifier(type)) return null;
    return IDENTIFIER_LABELS[type];
}

export function documentRequiresExpiry(type: DocumentTypeValue): boolean {
    return (
        type === "insurance" ||
        type === "driving_license" ||
        type === "pollution"
    );
}

/**
 * Zod validation schema for document form.
 * File is validated separately — multipart File objects don't fit cleanly in RHF defaults.
 */
export const documentSchema = z
    .object({
        document_type: z.enum(DOCUMENT_TYPES, {
            error: "Document type is required",
        }),
        custom_label: z
            .string()
            .max(MAX_DOCUMENT_TEXT_LENGTH, {
                message: `Keep the name under ${MAX_DOCUMENT_TEXT_LENGTH} characters`,
            })
            .optional(),
        identifier: z
            .string()
            .max(MAX_DOCUMENT_TEXT_LENGTH, {
                message: `Keep this under ${MAX_DOCUMENT_TEXT_LENGTH} characters`,
            })
            .optional(),
        expiry_date: z.string().optional(),
        notes: z.string().optional(),
    })
    .superRefine((values, ctx) => {
        if (values.document_type === "other") {
            if (!values.custom_label?.trim()) {
                ctx.addIssue({
                    code: "custom",
                    path: ["custom_label"],
                    message: "Enter a name for this document",
                });
            }
        }

        if (documentRequiresExpiry(values.document_type)) {
            if (!values.expiry_date?.trim()) {
                ctx.addIssue({
                    code: "custom",
                    path: ["expiry_date"],
                    message: "Expiry date is required",
                });
            }
        }
    });

export type DocumentSchema = z.infer<typeof documentSchema>;
