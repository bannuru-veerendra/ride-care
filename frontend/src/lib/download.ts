import { toast } from "sonner";

/**
 * Build a safe CSV download name like ridecare-fuel-shine-100.csv.
 */
export function csvExportFilename(
    kind: "fuel" | "service",
    vehicleName: string | undefined,
    fallbackId: string
): string {
    const slug =
        (vehicleName ?? "")
            .trim()
            .replace(/[^\w\-]+/g, "-")
            .replace(/-+/g, "-")
            .replace(/^-|-$/g, "") || fallbackId;
    return `ridecare-${kind}-${slug}.csv`;
}

/**
 * Trigger a browser download for a Blob (CSV exports, etc.).
 */
export function downloadBlob(blob: Blob, filename: string): void {
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(objectUrl);
}

/**
 * Download a CSV blob with consistent loading/toast handling.
 */
export async function exportCsvWithToast(
    fetchBlob: () => Promise<Blob>,
    filename: string,
    labels: { success: string; error: string }
): Promise<void> {
    try {
        const blob = await fetchBlob();
        downloadBlob(blob, filename);
        toast.success(labels.success);
    } catch {
        toast.error(labels.error);
    }
}

/** Success toast for bulk CSV import counts. */
export function importedCountMessage(
    count: number,
    singular: string,
    plural: string
): string {
    return count === 1
        ? `Imported 1 ${singular}`
        : `Imported ${count} ${plural}`;
}
