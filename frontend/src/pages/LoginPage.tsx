import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link, useSearchParams } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { isAxiosError } from "axios";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/common/PasswordInput";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";

import { useLogin } from "@/features/auth/hooks/useLogin";
import { loginSchema, type LoginSchema } from "@/features/auth/schemas";

/**
 * Login page.
 * Handles form submission, validation, and error display.
 */
export default function LoginPage() {
  const [searchParams] = useSearchParams();
  const { mutate: login, isPending, error } = useLogin();
  const { register, handleSubmit, formState: { errors } } = useForm<LoginSchema>({
    resolver: zodResolver(loginSchema),
  });

  useEffect(() => {
    if (searchParams.get("registered") === "true") {
      toast.success("Registration successful! Please login.");
    }
  }, [searchParams]);

  const onSubmit = (data: LoginSchema) => {
    login(data);
  };

  const apiError = isAxiosError(error)
    ? error.response?.data?.detail ?? "Login failed. Please try again."
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
            <CardTitle className="text-2xl">Welcome back!</CardTitle>
            <CardDescription>Sign in to your account to continue</CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {apiError && (
                <div className="bg-destructive/10 text-destructive text-sm rounded-md px-3 py-2">
                  {apiError}
                </div>
              )}

              <div className="space-y-1.5">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" placeholder="your@email.com" autoComplete="email" {...register("email")} />
                {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="password">Password</Label>
                <PasswordInput id="password" placeholder="Password" autoComplete="current-password" {...register("password")} />
                {errors.password && <p className="text-sm text-destructive">{errors.password.message}</p>}
              </div>

              <Button type="submit" className="w-full" disabled={isPending}>
                {isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : "Login"}
              </Button>
            </form>
          </CardContent>

          <CardFooter>
            <p className="text-sm text-muted-foreground">
              Don't have an account? <Link to="/register" className="text-primary hover:text-primary/80">Register</Link>
            </p>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
