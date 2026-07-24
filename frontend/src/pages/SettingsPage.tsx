import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/common/PasswordInput";
import { Skeleton } from "@/components/ui/skeleton";
import { getApiErrorMessage } from "@/lib/api-error";

import {
    useCurrentUser,
    useUpdatePassword,
    useUpdateProfile,
} from "@/features/users/hooks/useUsers";
import {
    passwordUpdateSchema,
    profileUpdateSchema,
    type PasswordUpdateSchema,
    type ProfileUpdateSchema,
} from "@/features/users/schemas";

/**
 * Account settings — update profile and password.
 */
export default function SettingsPage() {
    const { data: user, isLoading, isError } = useCurrentUser();
    const updateProfile = useUpdateProfile();
    const updatePassword = useUpdatePassword();

    const profileForm = useForm<ProfileUpdateSchema>({
        resolver: zodResolver(profileUpdateSchema),
        defaultValues: {
            full_name: "",
            email: "",
        },
    });
    const { reset: resetProfile } = profileForm;

    const passwordForm = useForm<PasswordUpdateSchema>({
        resolver: zodResolver(passwordUpdateSchema),
        defaultValues: {
            current_password: "",
            new_password: "",
            confirm_password: "",
        },
    });

    useEffect(() => {
        if (!user) return;
        resetProfile({
            full_name: user.full_name,
            email: user.email,
        });
    }, [user, resetProfile]);

    const onProfileSubmit = (values: ProfileUpdateSchema) => {
        updateProfile.mutate(
            {
                full_name: values.full_name,
                email: values.email,
            },
            {
                onSuccess: () => toast.success("Profile updated"),
                onError: (error) =>
                    toast.error(
                        getApiErrorMessage(error, "Failed to update profile")
                    ),
            }
        );
    };

    const onPasswordSubmit = (values: PasswordUpdateSchema) => {
        updatePassword.mutate(values, {
            onSuccess: () =>
                toast.success("Password changed. Please log in again."),
        });
    };

    if (isLoading) {
        return (
            <div className="animate-fade-up space-y-8">
                <div>
                    <Skeleton className="h-3 w-24" />
                    <Skeleton className="mt-3 h-12 w-48" />
                    <Skeleton className="mt-3 h-4 w-64" />
                </div>
                <Skeleton className="h-64 w-full max-w-xl" />
                <Skeleton className="h-80 w-full max-w-xl" />
            </div>
        );
    }

    if (isError || !user) {
        return (
            <div className="animate-fade-up surface-panel px-6 py-8 sm:px-8">
                <h1 className="font-heading text-3xl font-bold uppercase tracking-wide">
                    Settings
                </h1>
                <p className="mt-2 text-sm text-muted-foreground">
                    Could not load your profile. Please try again.
                </p>
            </div>
        );
    }

    return (
        <div className="animate-fade-up space-y-8">
            <div>
                <p className="text-xs font-bold uppercase tracking-[0.22em] text-brand">
                    Your account
                </p>
                <h1 className="font-heading mt-1 text-5xl font-extrabold uppercase italic tracking-wide sm:text-6xl">
                    Settings
                </h1>
                <p className="mt-2 text-sm text-muted-foreground">
                    Update your profile details or change your password
                </p>
            </div>

            <div className="surface-panel max-w-xl px-6 py-6 sm:px-8">
                <h2 className="font-heading text-xl font-bold uppercase tracking-wide">
                    Profile
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                    Name and email used across RideCare
                </p>

                <form
                    onSubmit={profileForm.handleSubmit(onProfileSubmit)}
                    className="mt-6 space-y-5"
                >
                    <div className="space-y-1.5">
                        <Label htmlFor="full_name">Full Name</Label>
                        <Input
                            id="full_name"
                            type="text"
                            autoComplete="name"
                            className="border-white/15 bg-white/5"
                            {...profileForm.register("full_name")}
                        />
                        {profileForm.formState.errors.full_name && (
                            <p className="text-sm text-destructive">
                                {profileForm.formState.errors.full_name.message}
                            </p>
                        )}
                    </div>

                    <div className="space-y-1.5">
                        <Label htmlFor="email">Email</Label>
                        <Input
                            id="email"
                            type="email"
                            autoComplete="email"
                            autoCapitalize="none"
                            autoCorrect="off"
                            spellCheck={false}
                            className="border-white/15 bg-white/5 lowercase"
                            {...profileForm.register("email")}
                        />
                        {profileForm.formState.errors.email && (
                            <p className="text-sm text-destructive">
                                {profileForm.formState.errors.email.message}
                            </p>
                        )}
                    </div>

                    <Button
                        type="submit"
                        className="bg-brand text-brand-foreground hover:bg-brand/90"
                        disabled={updateProfile.isPending}
                    >
                        {updateProfile.isPending ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            "Save profile"
                        )}
                    </Button>
                </form>
            </div>

            <div className="surface-panel max-w-xl px-6 py-6 sm:px-8">
                <h2 className="font-heading text-xl font-bold uppercase tracking-wide">
                    Password
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                    Changing your password signs you out on all devices
                </p>

                <form
                    onSubmit={passwordForm.handleSubmit(onPasswordSubmit)}
                    className="mt-6 space-y-5"
                >
                    <div className="space-y-1.5">
                        <Label htmlFor="current_password">Current password</Label>
                        <PasswordInput
                            id="current_password"
                            autoComplete="current-password"
                            className="border-white/15 bg-white/5"
                            {...passwordForm.register("current_password")}
                        />
                        {passwordForm.formState.errors.current_password && (
                            <p className="text-sm text-destructive">
                                {
                                    passwordForm.formState.errors.current_password
                                        .message
                                }
                            </p>
                        )}
                    </div>

                    <div className="space-y-1.5">
                        <Label htmlFor="new_password">New password</Label>
                        <PasswordInput
                            id="new_password"
                            autoComplete="new-password"
                            className="border-white/15 bg-white/5"
                            {...passwordForm.register("new_password")}
                        />
                        <p className="text-xs text-muted-foreground">
                            At least 8 characters, with one uppercase letter, one
                            number, and one special character.
                        </p>
                        {passwordForm.formState.errors.new_password && (
                            <p className="text-sm text-destructive">
                                {passwordForm.formState.errors.new_password.message}
                            </p>
                        )}
                    </div>

                    <div className="space-y-1.5">
                        <Label htmlFor="confirm_password">Confirm new password</Label>
                        <PasswordInput
                            id="confirm_password"
                            autoComplete="new-password"
                            className="border-white/15 bg-white/5"
                            {...passwordForm.register("confirm_password")}
                        />
                        {passwordForm.formState.errors.confirm_password && (
                            <p className="text-sm text-destructive">
                                {
                                    passwordForm.formState.errors.confirm_password
                                        .message
                                }
                            </p>
                        )}
                    </div>

                    <Button
                        type="submit"
                        className="bg-brand text-brand-foreground hover:bg-brand/90"
                        disabled={updatePassword.isPending}
                    >
                        {updatePassword.isPending ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            "Change password"
                        )}
                    </Button>
                </form>
            </div>
        </div>
    );
}
