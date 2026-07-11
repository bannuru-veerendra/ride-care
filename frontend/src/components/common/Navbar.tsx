import { Link, useNavigate } from "react-router-dom";
import { LogOut, Menu } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import useAuthStore from "@/store/auth.store";
import RideCareLogo from "./RideCareLogo";


/**
 * Navigation bar component
 * Responsive - Shows hamburger menu on small screens.
 * full nav link list on larger screens.
 */

export default function Navbar() {
    const navigate = useNavigate();
    const clearToken = useAuthStore((state) => state.clearToken);

    const handleLogout = () => {
        clearToken();
        toast.success("Logged out successfully");
        navigate("/login");
    };

    const navLinks = (
        <>
            <Link to="/dashboard" className="text-sm font-medium text-foreground hover:text-primary">Dashboard</Link>
            <Link to="/vehicles" className="text-sm font-medium text-foreground hover:text-primary">Vehicles</Link>
        </>
    );

    return (
        <header className="border-b sticky top-0 bg-background z-50">
            <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">

                <RideCareLogo />

                {/* Desktop nav */}
                <nav className="hidden md:flex items-center gap-6">
                    {navLinks}
                    <Button variant="ghost" size="icon" onClick={handleLogout}>
                        <LogOut className="w-4 h-4" />
                        Logout
                    </Button>
                </nav>

                {/* Mobile nav */}
                <div className="md:hidden">
                    <Sheet>
                        <SheetTrigger render={<Button variant="ghost" size="icon" />}>
                            <Menu className="w-6 h-6" />
                            <span className="sr-only">Open Menu</span>
                        </SheetTrigger>
                        <SheetContent side="right" className="w-64">
                            <div className="flex flex-col gap-4 pt-8">
                                <nav className="flex flex-col gap-2">
                                    {navLinks}
                                </nav>
                                <Button variant="outline" onClick={handleLogout}>
                                    <LogOut className="w-4 h-4" />
                                    Logout
                                </Button>
                            </div>
                        </SheetContent>
                    </Sheet>
                </div>

            </div>
        </header>
    );
}
