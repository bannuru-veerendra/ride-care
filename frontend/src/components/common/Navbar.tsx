import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { LogOut, Menu, Settings, Wrench } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { useLogout } from "@/features/auth/hooks/useLogout";
import AccountMenu from "./AccountMenu";
import RideCareLogo from "./RideCareLogo";
import { cn } from "@/lib/utils";

/**
 * Navigation bar — primary product links + account menu.
 */
export default function Navbar() {
    const location = useLocation();
    const logout = useLogout();
    const [mobileOpen, setMobileOpen] = useState(false);

    const links = [
        { to: "/dashboard", label: "Dashboard" },
        { to: "/vehicles", label: "Garage" },
    ];

    const renderLinks = (onNavigate?: () => void) =>
        links.map((link) => {
            const active = location.pathname.startsWith(link.to);
            return (
                <Link
                    key={link.to}
                    to={link.to}
                    onClick={onNavigate}
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
        });

    const settingsActive = location.pathname.startsWith("/settings");
    const maintenanceActive = location.pathname.startsWith("/maintenance");

    return (
        <header className="sticky top-0 z-50 border-b border-white/10 bg-background/70 backdrop-blur-xl">
            <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
                <RideCareLogo inverted />

                <div className="hidden items-center gap-8 md:flex">
                    <nav className="flex items-center gap-8">{renderLinks()}</nav>
                    <AccountMenu />
                </div>

                <div className="md:hidden">
                    <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
                        <SheetTrigger
                            render={<Button variant="ghost" size="icon" />}
                        >
                            <Menu className="h-6 w-6" />
                            <span className="sr-only">Open Menu</span>
                        </SheetTrigger>
                        <SheetContent
                            side="right"
                            className="w-64 border-white/10 bg-background p-0"
                        >
                            <div className="flex flex-col gap-6 px-6 pb-6 pt-14">
                                <nav className="flex flex-col gap-5">
                                    {renderLinks(() => setMobileOpen(false))}
                                </nav>

                                <div className="border-t border-white/10 pt-5">
                                    <p className="mb-3 text-xs font-bold uppercase tracking-[0.18em] text-muted-foreground">
                                        Account
                                    </p>
                                    <div className="flex flex-col gap-4">
                                        <Link
                                            to="/settings"
                                            onClick={() => setMobileOpen(false)}
                                            className={cn(
                                                "inline-flex cursor-pointer items-center gap-2 text-sm font-medium transition-colors",
                                                settingsActive
                                                    ? "text-foreground"
                                                    : "text-muted-foreground hover:text-foreground"
                                            )}
                                        >
                                            <Settings className="h-4 w-4" />
                                            Settings
                                        </Link>
                                        <Link
                                            to="/maintenance"
                                            onClick={() => setMobileOpen(false)}
                                            className={cn(
                                                "inline-flex cursor-pointer items-center gap-2 text-sm font-medium transition-colors",
                                                maintenanceActive
                                                    ? "text-foreground"
                                                    : "text-muted-foreground hover:text-foreground"
                                            )}
                                        >
                                            <Wrench className="h-4 w-4" />
                                            Maintenance guide
                                        </Link>
                                        <button
                                            type="button"
                                            onClick={() => {
                                                setMobileOpen(false);
                                                void logout();
                                            }}
                                            className="inline-flex cursor-pointer items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-brand"
                                        >
                                            <LogOut className="h-4 w-4" />
                                            Log out
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </SheetContent>
                    </Sheet>
                </div>
            </div>
        </header>
    );
}
