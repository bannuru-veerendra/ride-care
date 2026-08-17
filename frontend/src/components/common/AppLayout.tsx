import { Suspense } from "react";
import { Outlet } from "react-router-dom";
import Navbar from "@/components/common/Navbar";
import { ConfirmProvider } from "@/components/common/ConfirmDialog";

/**
 * Main application layout
 * Wraps all protected pages with navbar.
 */
export default function AppLayout() {
    return (
        <ConfirmProvider>
            <div className="relative min-h-screen">
                <div
                    aria-hidden
                    className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
                >
                    <div className="absolute -top-40 left-1/4 h-[28rem] w-[28rem] rounded-full bg-[radial-gradient(circle,oklch(0.58_0.23_25/0.22),transparent_70%)]" />
                    <div className="absolute right-0 bottom-0 h-72 w-72 rounded-full bg-[radial-gradient(circle,oklch(1_0_0/0.06),transparent_70%)]" />
                </div>

                <Navbar />
                <main className="mx-auto max-w-6xl px-4 pb-8 sm:px-6 sm:pb-10">
                    <Suspense
                        fallback={
                            <div className="flex min-h-[40vh] items-center justify-center">
                                <div
                                    className="h-8 w-8 animate-spin rounded-full border-2 border-brand border-t-transparent"
                                    aria-label="Loading"
                                />
                            </div>
                        }
                    >
                        <Outlet />
                    </Suspense>
                </main>
            </div>
        </ConfirmProvider>
    );
}
