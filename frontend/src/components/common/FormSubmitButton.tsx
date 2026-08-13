import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";

interface FormSubmitButtonProps {
    isPending: boolean;
    isEdit?: boolean;
    createLabel: string;
    pendingLabel?: string;
    className?: string;
}

/** Brand submit button with pending spinner for create/edit forms. */
export default function FormSubmitButton({
    isPending,
    isEdit = false,
    createLabel,
    pendingLabel = "Saving...",
    className,
}: FormSubmitButtonProps) {
    return (
        <Button
            type="submit"
            disabled={isPending}
            className={
                className ??
                "bg-brand text-brand-foreground hover:bg-brand/90"
            }
        >
            {isPending ? (
                <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {pendingLabel}
                </>
            ) : isEdit ? (
                "Save changes"
            ) : (
                createLabel
            )}
        </Button>
    );
}
