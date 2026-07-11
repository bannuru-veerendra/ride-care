import { Outlet } from "react-router-dom";
import Navbar from "@/components/common/Navbar";


/**
 * Main application layout 
 * Wraps all protected pages with navbar.
 * Uses <Outlet> to render the child route components.
 */
export default function AppLayout() {
    return (
        <div className="min-h-screen bg-background">
            <Navbar />
            <main className="max-w-7xl mx-auto px-4 py-8">
                <Outlet />
            </main>
        </div>
    );
}