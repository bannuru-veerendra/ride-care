import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { isAxiosError } from "axios";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/common/PasswordInput";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";

import { useRegister } from "@/features/auth/hooks/useRegister";
import { registerSchema, type RegisterSchema } from "@/features/auth/schemas";

/**
 * Register page.
 * Collects user details and redirects to login on success.
 */
export default function RegisterPage() {
  const { mutate: registerUser, isPending, error } = useRegister();
  const { register, handleSubmit, formState: { errors } } = useForm<RegisterSchema>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = (data: RegisterSchema) => {
    registerUser(data);
  };

  const apiError = isAxiosError(error)
    ? error.response?.data?.detail ?? "Registration failed. Please try again."
    : null;

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-primary">RideCare</h1>
          <p className="text-muted-foreground mt-1">Your vehicle companion</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">Create an account</CardTitle>
            <CardDescription>Enter your details to create an account</CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {apiError && (
                <div className="bg-destructive/10 text-destructive text-sm rounded-md px-3 py-2">
                  {apiError}
                </div>
              )}

              <div className="space-y-1.5">
                <Label htmlFor="full_name">Full Name</Label>
                <Input id="full_name" type="text" placeholder="Your full name" autoComplete="name" {...register("full_name")} />
                {errors.full_name && <p className="text-sm text-destructive">{errors.full_name.message}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" placeholder="your@email.com" autoComplete="email" {...register("email")} />
                {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="password">Password</Label>
                <PasswordInput id="password" placeholder="Password" autoComplete="new-password" {...register("password")} />
                {errors.password && <p className="text-sm text-destructive">{errors.password.message}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="confirm_password">Confirm Password</Label>
                <PasswordInput id="confirm_password" placeholder="Confirm password" autoComplete="new-password" {...register("confirm_password")} />
                {errors.confirm_password && <p className="text-sm text-destructive">{errors.confirm_password.message}</p>}
              </div>

              <Button type="submit" className="w-full" disabled={isPending}>
                {isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : "Register"}
              </Button>
            </form>
          </CardContent>

          <CardFooter>
            <p className="text-sm text-muted-foreground">
              Already have an account? <Link to="/login" className="text-primary hover:text-primary/80">Login</Link>
            </p>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
