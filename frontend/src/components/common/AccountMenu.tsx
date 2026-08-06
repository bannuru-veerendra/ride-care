import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronDown, LogOut, Settings, Wrench } from "lucide-react";

import { useLogout } from "@/features/auth/hooks/useLogout";
import { useCurrentUser } from "@/features/users/hooks/useUsers";
import { cn } from "@/lib/utils";

function getInitials(fullName: string): string {
    const parts = fullName.trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) return "?";
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

/**
 * Account menu — Settings, Maintenance guide, and Logout.
 */
export default function AccountMenu() {
    const navigate = useNavigate();
    const logout = useLogout();
    const { data: user } = useCurrentUser();
    const [open, setOpen] = useState(false);
    const rootRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!open) return;

        const onPointerDown = (event: MouseEvent) => {
            if (!rootRef.current?.contains(event.target as Node)) {
                setOpen(false);
            }
        };
        const onKeyDown = (event: KeyboardEvent) => {
            if (event.key === "Escape") setOpen(false);
        };

        document.addEventListener("mousedown", onPointerDown);
        document.addEventListener("keydown", onKeyDown);
        return () => {
            document.removeEventListener("mousedown", onPointerDown);
            document.removeEventListener("keydown", onKeyDown);
        };
    }, [open]);

    const displayName = user?.full_name ?? "Account";
    const email = user?.email;
    const initials = getInitials(displayName);

    return (
        <div ref={rootRef} className="relative">
            <button
                type="button"
                aria-expanded={open}
                aria-haspopup="menu"
                onClick={() => setOpen((prev) => !prev)}
                className={cn(
                    "inline-flex cursor-pointer items-center gap-2 rounded-lg px-1.5 py-1",
                    "text-sm font-medium text-muted-foreground transition-colors",
                    "hover:bg-white/5 hover:text-foreground",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/60",
                    open && "bg-white/5 text-foreground"
                )}
            >
                <span
                    aria-hidden
                    className="flex size-8 items-center justify-center rounded-full bg-brand/20 text-xs font-bold text-brand"
                >
                    {initials}
                </span>
                <span className="hidden max-w-[9rem] truncate lg:inline">
                    {displayName}
                </span>
                <ChevronDown
                    className={cn(
                        "hidden size-3.5 opacity-70 transition-transform lg:inline",
                        open && "rotate-180"
                    )}
                />
                <span className="sr-only">Open account menu</span>
            </button>

            {open ? (
                <div
                    role="menu"
                    className={cn(
                        "absolute right-0 top-full z-[60] mt-2 min-w-56",
                        "rounded-lg border border-white/10 bg-background/95 p-1",
                        "shadow-lg backdrop-blur-xl"
                    )}
                >
                    <div className="border-b border-white/10 px-3 py-2.5">
                        <p className="truncate text-sm font-semibold text-foreground">
                            {displayName}
                        </p>
                        {email ? (
                            <p className="truncate text-xs text-muted-foreground">
                                {email}
                            </p>
                        ) : null}
                    </div>

                    <button
                        type="button"
                        role="menuitem"
                        onClick={() => {
                            setOpen(false);
                            navigate("/settings");
                        }}
                        className={cn(
                            "flex w-full cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm",
                            "text-muted-foreground transition-colors",
                            "hover:bg-white/5 hover:text-foreground"
                        )}
                    >
                        <Settings className="size-4" />
                        Settings
                    </button>

                    <button
                        type="button"
                        role="menuitem"
                        onClick={() => {
                            setOpen(false);
                            navigate("/maintenance");
                        }}
                        className={cn(
                            "flex w-full cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm",
                            "text-muted-foreground transition-colors",
                            "hover:bg-white/5 hover:text-foreground"
                        )}
                    >
                        <Wrench className="size-4" />
                        Maintenance guide
                    </button>

                    <div className="my-1 h-px bg-white/10" />

                    <button
                        type="button"
                        role="menuitem"
                        onClick={() => {
                            setOpen(false);
                            void logout();
                        }}
                        className={cn(
                            "flex w-full cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm",
                            "text-muted-foreground transition-colors",
                            "hover:bg-white/5 hover:text-brand"
                        )}
                    >
                        <LogOut className="size-4" />
                        Log out
                    </button>
                </div>
            ) : null}
        </div>
    );
}
