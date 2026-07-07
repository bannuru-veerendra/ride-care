import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { authApi } from "@/api/auth.api";
import type { RegisterFormValues } from "../types";

/**
 * Handles user registration.
 * Redirects to the login page on success.
 */
export const useRegister = () => {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (values: RegisterFormValues) =>
      authApi.register({
        email: values.email,
        full_name: values.full_name,
        password: values.password,
      }),
    onSuccess: () => {
      navigate("/login?registered=true");
    },
  });
};
