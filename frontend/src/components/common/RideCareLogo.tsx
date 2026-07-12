import { Link } from "react-router-dom";

interface RideCareLogoProps {
    to?: string;
    /** Compact horizontal layout for the navbar */
    compact?: boolean;
    /** Light wordmark for dark surfaces */
    inverted?: boolean;
}

/**
 * RideCare brand logo.
 * Mark: wheelie rider (black / white / red) — defines rider identity.
 * Wordmark: RIDE + CARE split color, italic speed typography.
 */
export default function RideCareLogo({
    to = "/dashboard",
    compact = true,
    inverted = false,
}: RideCareLogoProps) {
    return (
        <Link
            to={to}
            className={
                compact
                    ? "flex items-center gap-2.5 transition-opacity hover:opacity-85"
                    : "flex flex-col items-center gap-2 transition-opacity hover:opacity-85"
            }
        >
            <img
                src="/ridecare-mark.png?v=2"
                alt=""
                className={
                    compact
                        ? "h-11 w-11 object-contain"
                        : "h-24 w-24 object-contain"
                }
            />
            <div
                className={
                    compact
                        ? "flex flex-col leading-none"
                        : "flex flex-col items-center leading-none"
                }
            >
                <span
                    className={
                        compact
                            ? "text-[17px] font-black italic uppercase tracking-wide"
                            : "font-heading text-4xl font-extrabold italic uppercase tracking-wide sm:text-5xl"
                    }
                >
                    <span className={inverted ? "text-white" : "text-foreground"}>
                        Ride
                    </span>
                    <span className="text-brand">Care</span>
                </span>
                <span
                    className={
                        compact
                            ? "mt-1 text-[9px] font-bold uppercase tracking-[0.18em] text-brand"
                            : "mt-1.5 text-xs font-bold uppercase tracking-[0.22em] text-brand"
                    }
                >
                    For riders
                </span>
            </div>
        </Link>
    );
}
