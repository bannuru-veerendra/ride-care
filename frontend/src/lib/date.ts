import { format } from "date-fns";
import { z } from "zod";

/** Today's date as YYYY-MM-DD in Asia/Kolkata */
export function appTodayISO(): string {
    return new Intl.DateTimeFormat("en-CA", {
        timeZone: "Asia/Kolkata",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
    }).format(new Date());
}

/** Display dates consistently across cards and dashboard. */
export function formatAppDate(isoDate: string): string {
    return format(new Date(isoDate), "dd MMM yyyy");
}

/** Required date that cannot be in the future (app timezone). */
export function pastOrTodayDateSchema(label: string) {
    return z
        .string()
        .min(1, { message: "Date is required" })
        .refine((value) => value <= appTodayISO(), {
            message: `${label} date cannot be in the future`,
        });
}

/** Positive whole-number odometer (km). */
export const odometerSchema = z
    .number({ error: "Odometer must be a number" })
    .positive({ message: "Odometer must be greater than 0" })
    .int({ message: "Odometer must be a whole number (km)" });
