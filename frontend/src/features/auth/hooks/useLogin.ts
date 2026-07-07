import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { authApi } from "@/api/auth.api";
import useAuthStore from "@/store/auth.store";
import type { LoginFormValues } from "../types";

/**
 * Handles user login.
 * Stores the token and redirects to the dashboard on success.
 */
export const useLogin = () => {
  const navigate = useNavigate();
  const setToken = useAuthStore((state) => state.setToken);

  return useMutation({
    mutationFn: (values: LoginFormValues) => authApi.login(values),
    onSuccess: (data) => {
      setToken(data.access_token);
      navigate("/dashboard");
    },
  });
};
