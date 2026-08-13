import { toast } from "sonner";

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
