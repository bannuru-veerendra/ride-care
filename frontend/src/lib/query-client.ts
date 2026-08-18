import { isAxiosError } from "axios";
import { QueryClient } from "@tanstack/react-query";

import type { CursorPage } from "@/types";

/** Retry once on network/5xx. Never retry 4xx — that doubles a failed first paint. */
function shouldRetryQuery(failureCount: number, error: unknown): boolean {
    if (failureCount >= 1) {
        return false;
    }
    if (isAxiosError(error)) {
        const status = error.response?.status;
        if (status !== undefined && status < 500) {
            return false;
        }
    }
    return true;
}

/**
 * Global React Query client.
 * - Retries failed requests once before showing an error.
 * - Does not refetch on window focus in development to avoid
 *   unnecessary API calls during debugging.
 */
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: shouldRetryQuery,
            refetchOnWindowFocus: false,
            staleTime: 1000 * 60 * 5, // 5 minutes
        },
    },
});

/** Shared getNextPageParam for cursor-paginated infinite queries. */
export function getCursorNextPageParam<T>(
    lastPage: CursorPage<T>
): string | undefined {
    return lastPage.has_more ? lastPage.next_cursor ?? undefined : undefined;
}

export default queryClient;
