import { isAxiosError } from "axios";

/**
 * Prefer backend error messages so validation rules stay server-owned.
 */
export function getApiErrorMessage(error: unknown, fallback: string): string {
    if (!isAxiosError(error)) {
        return fallback;
    }

    const detail = error.response?.data?.detail;

    if (typeof detail === "string" && detail.trim()) {
        return detail;
    }

    if (
        detail &&
        typeof detail === "object" &&
        !Array.isArray(detail) &&
        Array.isArray((detail as { errors?: unknown }).errors)
    ) {
        const errors = (detail as { errors: { row?: number; message?: string }[] })
            .errors;
        const messages = errors
            .map((item) => {
                if (typeof item?.message !== "string" || !item.message.trim()) {
                    return null;
                }
                return typeof item.row === "number"
                    ? `Row ${item.row}: ${item.message}`
                    : item.message;
            })
            .filter((message): message is string => Boolean(message));
        if (messages.length > 0) {
            return messages.slice(0, 3).join(". ");
        }
        if (
            typeof (detail as { message?: string }).message === "string" &&
            (detail as { message: string }).message.trim()
        ) {
            return (detail as { message: string }).message;
        }
    }

    if (Array.isArray(detail)) {
        const messages = detail
            .map((item) => {
                if (typeof item?.msg !== "string") {
                    return null;
                }
                return item.msg.replace(/^Value error,\s*/i, "");
            })
            .filter((message): message is string => Boolean(message));

        if (messages.length > 0) {
            return messages.join(". ");
        }
    }

    return fallback;
}
