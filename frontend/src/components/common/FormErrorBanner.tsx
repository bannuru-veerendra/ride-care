import { getApiErrorMessage } from "@/lib/api-error";

interface FormErrorBannerProps {
    error: unknown;
    fallback?: string;
}

/** Renders a safe string for API/validation errors (handles FastAPI 422 arrays). */
export default function FormErrorBanner({
    error,
    fallback = "Something went wrong. Please try again.",
}: FormErrorBannerProps) {
    if (!error) return null;

    const message = getApiErrorMessage(error, fallback);

    return (
        <div className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {message}
        </div>
    );
}
