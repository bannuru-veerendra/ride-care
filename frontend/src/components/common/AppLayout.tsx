import { Outlet } from "react-router-dom";
import Navbar from "@/components/common/Navbar";

/**
 * Main application layout
 * Wraps all protected pages with navbar.
 */
export default function AppLayout() {
    return (
        <div className="relative min-h-screen">
            <div
                aria-hidden
                className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
            >
                <div className="absolute -top-40 left-1/4 h-96 w-96 rounded-full bg-brand/20 blur-[100px]" />
                <div className="absolute bottom-0 right-0 h-72 w-72 rounded-full bg-white/5 blur-[80px]" />
            </div>

            <Navbar />
            <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
                <Outlet />
            </main>
        </div>
    );
}
