import { z } from "zod";

/**
 * Document type options and display labels.
 */
export const DOCUMENT_TYPES = [
    "insurance",
    "driving_license",
    "registration_certificate",
] as const;

export const DOCUMENT_LABELS: Record<(typeof DOCUMENT_TYPES)[number], string> = {
    insurance: "Insurance",
    driving_license: "Driving Licence",
    registration_certificate: "Registration Certificate",
};

/**
 * Zod validation schema for document form.
 * File is validated separately — multipart File objects don't fit cleanly in RHF defaults.
 */
export const documentSchema = z.object({
    document_type: z.enum(DOCUMENT_TYPES, {
        error: "Document type is required",
    }),
    expiry_date: z.string().optional(),
    notes: z.string().optional(),
});

export type DocumentSchema = z.infer<typeof documentSchema>;
