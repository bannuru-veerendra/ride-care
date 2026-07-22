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
