import { useEffect, type RefObject } from "react";

/**
 * Close a popover/menu on outside mousedown or Escape.
 */
export function useDismissible(
    open: boolean,
    rootRef: RefObject<HTMLElement | null>,
    onDismiss: () => void
) {
    useEffect(() => {
        if (!open) return;

        const onPointerDown = (event: MouseEvent) => {
            if (!rootRef.current?.contains(event.target as Node)) {
                onDismiss();
            }
        };
        const onKeyDown = (event: KeyboardEvent) => {
            if (event.key === "Escape") onDismiss();
        };

        document.addEventListener("mousedown", onPointerDown);
        document.addEventListener("keydown", onKeyDown);
        return () => {
            document.removeEventListener("mousedown", onPointerDown);
            document.removeEventListener("keydown", onKeyDown);
        };
    }, [open, rootRef, onDismiss]);
}
