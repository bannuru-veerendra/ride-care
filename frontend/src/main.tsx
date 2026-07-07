import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import queryClient from "./lib/query-client";
import "./index.css";
import App from "./App";

/**
 * Application entry point.
 * Wraps the app with:
 * - BrowserRouter for client-side routing
 * - QueryClientProvider for server state management
 */
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </BrowserRouter>
  </StrictMode>
);