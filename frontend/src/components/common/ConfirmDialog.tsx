import {
    createContext,
    useCallback,
    useContext,
    useRef,
    useState,
    type ReactNode,
} from "react";
import { AlertDialog } from "@base-ui/react/alert-dialog";

import { Button } from "@/components/ui/button";

interface ConfirmRequest {
    title: string;
    description: string;
    confirmLabel?: string;
    onConfirm: () => void;
}

const ConfirmContext = createContext<((options: ConfirmRequest) => void) | null>(
    null
);

/**
 * App-level confirm dialog. Replaces window.confirm() so delete clicks
 * do not block the main thread or re-render the page that opened it.
 */
export function ConfirmProvider({ children }: { children: ReactNode }) {
    const [open, setOpen] = useState(false);
    const [copy, setCopy] = useState({
        title: "",
        description: "",
        confirmLabel: "Delete",
    });
    const actionRef = useRef<(() => void) | null>(null);

    const requestConfirm = useCallback((options: ConfirmRequest) => {
        actionRef.current = options.onConfirm;
        setCopy({
            title: options.title,
            description: options.description,
            confirmLabel: options.confirmLabel ?? "Delete",
        });
        setOpen(true);
    }, []);

    const handleOpenChange = useCallback((next: boolean) => {
        setOpen(next);
        if (!next) actionRef.current = null;
    }, []);

    const handleConfirm = useCallback(() => {
        const action = actionRef.current;
        actionRef.current = null;
        setOpen(false);
        action?.();
    }, []);

    return (
        <ConfirmContext.Provider value={requestConfirm}>
            {children}
            <AlertDialog.Root open={open} onOpenChange={handleOpenChange}>
                <AlertDialog.Portal>
                    <AlertDialog.Backdrop className="fixed inset-0 z-50 bg-black/50 transition-opacity duration-150 data-ending-style:opacity-0 data-starting-style:opacity-0" />
                    <AlertDialog.Popup className="fixed top-1/2 left-1/2 z-50 grid w-full max-w-[calc(100vw-2rem)] -translate-x-1/2 -translate-y-1/2 gap-4 rounded-xl bg-popover p-4 text-sm text-popover-foreground ring-1 ring-foreground/10 sm:max-w-sm transition-[opacity,scale] duration-100 ease-out data-ending-style:scale-[0.98] data-ending-style:opacity-0 data-starting-style:scale-[0.98] data-starting-style:opacity-0">
                        <div className="flex flex-col gap-1.5">
                            <AlertDialog.Title className="font-heading text-base font-medium text-foreground">
                                {copy.title}
                            </AlertDialog.Title>
                            <AlertDialog.Description className="text-sm text-muted-foreground">
                                {copy.description}
                            </AlertDialog.Description>
                        </div>
                        <div className="-mx-4 -mb-4 flex flex-col-reverse gap-2 rounded-b-xl border-t bg-muted/50 p-4 sm:flex-row sm:justify-end">
                            <AlertDialog.Close
                                render={<Button type="button" variant="outline" />}
                            >
                                Cancel
                            </AlertDialog.Close>
                            <Button type="button" variant="destructive" onClick={handleConfirm}>
                                {copy.confirmLabel}
                            </Button>
                        </div>
                    </AlertDialog.Popup>
                </AlertDialog.Portal>
            </AlertDialog.Root>
        </ConfirmContext.Provider>
    );
}

export function useConfirmDialog() {
    const requestConfirm = useContext(ConfirmContext);
    if (!requestConfirm) {
        throw new Error("useConfirmDialog must be used within ConfirmProvider");
    }
    return requestConfirm;
}
