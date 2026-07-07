import { QueryClient } from "@tanstack/react-query";

/**
 * Global React Query client.
 * - Retries failed requests once before showing an error.
 * - Does not refetch on window focus in development to avoid
 *   unnecessary API calls during debugging.
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  },
});

export default queryClient;
