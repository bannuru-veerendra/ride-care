import { z } from "zod";

/** Positive number with at most 2 decimal places; normalize to 2 dp. */
export const positiveDecimal2Schema = z
    .number({ error: "Must be a number" })
    .positive({ message: "Must be greater than 0" })
    .refine(
        (value) => Math.abs(value * 100 - Math.round(value * 100)) < 1e-6,
        { message: "Use up to 2 decimal places" }
    )
    .transform((value) => Math.round(value * 100) / 100);

/** Non-negative number with at most 2 decimal places; normalize to 2 dp. */
export const nonNegativeDecimal2Schema = z
    .number({ error: "Must be a number" })
    .min(0, { message: "Must be greater than or equal to 0" })
    .refine(
        (value) => Math.abs(value * 100 - Math.round(value * 100)) < 1e-6,
        { message: "Use up to 2 decimal places" }
    )
    .transform((value) => Math.round(value * 100) / 100);
