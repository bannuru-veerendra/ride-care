import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/**
 * 404 — shown when a route doesn't match anything.
 */
export default function NotFoundPage() {
    return (
        <div className="min-h-screen flex items-center justify-center px-4">
            <div className="text-center space-y-4 max-w-md">
                <p className="font-heading text-8xl font-extrabold text-brand/20 tracking-widest">
                    404
                </p>
                <h1 className="font-heading text-2xl font-bold uppercase tracking-wide">
                    Page not found
                </h1>
                <p className="text-sm text-muted-foreground">
                    The page you're looking for doesn't exist or has been moved.
                </p>
                <Link
                    to="/dashboard"
                    className={cn(
                        buttonVariants(),
                        "mt-2 inline-flex bg-brand text-brand-foreground hover:bg-brand/90"
                    )}
                >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back to dashboard
                </Link>
            </div>
        </div>
    );
}