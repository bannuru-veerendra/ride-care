import { Link } from "react-router-dom";

interface RideCareLogoProps {
  to?: string;
  /** Compact horizontal layout for the navbar */
  compact?: boolean;
}

/**
 * RideCare brand logo.
 * Mark: wheelie rider (black / white / red) — defines rider identity.
 * Wordmark: RIDE + CARE split color, italic speed typography.
 */
export default function RideCareLogo({ to = "/dashboard", compact = true }: RideCareLogoProps) {
  return (
    <Link
      to={to}
      className={
        compact
          ? "flex items-center gap-2.5 hover:opacity-85 transition-opacity"
          : "flex flex-col items-center gap-2 hover:opacity-85 transition-opacity"
      }
    >
      <img
        src="/ridecare-mark.png?v=2"
        alt=""
        className={compact ? "h-11 w-11 object-contain" : "h-24 w-24 object-contain"}
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
              : "text-3xl font-black italic uppercase tracking-wide"
          }
        >
          <span className="text-foreground">Ride</span>
          <span className="text-red-600">Care</span>
        </span>
        <span
          className={
            compact
              ? "text-[9px] font-bold uppercase tracking-[0.18em] text-red-600 mt-1"
              : "text-xs font-bold uppercase tracking-[0.22em] text-red-600 mt-1.5"
          }
        >
          For riders
        </span>
      </div>
    </Link>
  );
}
