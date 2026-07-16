import { Component, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error?: Error | null;
}

/**
 * Catches unhandled React render errors and displays a fallback UI.
 * Wrap page-level components or the entire app with this
 * 
 * Usage:
 * <ErrorBoundary>
 *     <YourComponent />
 * </ErrorBoundary>
 */

export default class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, info: { componentStack: string }) {
        console.error("ErrorBoundary caught an error:", error, info);
    }

    handleRefresh = () => {
        this.setState({ hasError: false, error: null });
        window.location.reload();
    }

    render() {
    if (this.state.hasError) {
        if (this.props.fallback) return this.props.fallback;

        return (
        <div className="min-h-screen flex items-center justify-center px-4">
            <div className="text-center max-w-md space-y-4">
            <div className="flex justify-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
                <AlertTriangle className="h-8 w-8 text-destructive" />
                </div>
            </div>
            <h1 className="font-heading text-2xl font-bold uppercase tracking-wide">
                Something went wrong
            </h1>
            <p className="text-sm text-muted-foreground">
                An unexpected error occurred. Try refreshing the page — if
                the problem persists, please contact support.
            </p>
            {import.meta.env.DEV && this.state.error && (
                <pre className="mt-2 rounded-lg bg-muted p-3 text-left text-xs text-muted-foreground overflow-auto max-h-40">
                {this.state.error.message}
                </pre>
            )}
            <div className="flex gap-3 justify-center">
                <Button onClick={this.handleRefresh} variant="outline">
                <RefreshCw className="mr-2 h-4 w-4" />
                Try again
                </Button>
                <Button onClick={() => (window.location.href = "/dashboard")}>
                Go to dashboard
                </Button>
            </div>
            </div>
        </div>
        );
    }

    return this.props.children;
    }
}

