import { Link, useLocation, useNavigate } from "react-router-dom";
import { LogOut, Menu } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import useAuthStore from "@/store/auth.store";
import RideCareLogo from "./RideCareLogo";
import { cn } from "@/lib/utils";

/**
 * Navigation bar — sticky glass bar over night asphalt UI.
 */
export default function Navbar() {
    const navigate = useNavigate();
    const location = useLocation();
    const clearToken = useAuthStore((state) => state.clearToken);

    const handleLogout = () => {
        clearToken();
        toast.success("Logged out successfully");
        navigate("/login");
    };

    const links = [
        { to: "/dashboard", label: "Dashboard" },
        { to: "/vehicles", label: "Garage" },
    ];

    const navLinks = (
        <>
            {links.map((link) => {
                const active = location.pathname.startsWith(link.to);
                return (
                    <Link
                        key={link.to}
                        to={link.to}
                        className={cn(
                            "relative text-sm font-semibold uppercase tracking-[0.12em] transition-colors",
                            active
                                ? "text-foreground"
                                : "text-muted-foreground hover:text-foreground"
                        )}
                    >
                        {link.label}
                        {active && (
                            <span className="absolute -bottom-1 left-0 h-0.5 w-full bg-brand" />
                        )}
                    </Link>
                );
            })}
        </>
    );

    return (
        <header className="sticky top-0 z-50 border-b border-white/10 bg-background/70 backdrop-blur-xl">
            <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
                <RideCareLogo inverted />

                <nav className="hidden items-center gap-8 md:flex">
                    {navLinks}
                    <button
                        type="button"
                        onClick={handleLogout}
                        className="inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-brand"
                    >
                        <LogOut className="h-3.5 w-3.5" />
                        Logout
                    </button>
                </nav>

                <div className="md:hidden">
                    <Sheet>
                        <SheetTrigger render={<Button variant="ghost" size="icon" />}>
                            <Menu className="h-6 w-6" />
                            <span className="sr-only">Open Menu</span>
                        </SheetTrigger>
                        <SheetContent side="right" className="w-64 border-white/10 bg-background">
                            <div className="flex flex-col gap-6 pt-8">
                                <nav className="flex flex-col gap-4">{navLinks}</nav>
                                <button
                                    type="button"
                                    onClick={handleLogout}
                                    className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-brand"
                                >
                                    <LogOut className="h-4 w-4" />
                                    Logout
                                </button>
                            </div>
                        </SheetContent>
                    </Sheet>
                </div>
            </div>
        </header>
    );
}
