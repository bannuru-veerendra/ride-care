import axios from "axios";

import useAuthStore from "@/store/auth.store";

/**
 * Axios instance for the RideCare API.
 * Auth uses httpOnly cookies (`withCredentials`); no tokens in localStorage.
 *
 * Same-origin `/api` in prod (Vercel rewrite → Render) and in local Vite
 * (proxy → 127.0.0.1:8000). Absolute VITE_API_URL is still allowed in
 * dev for pointing at a remote API; it is ignored in production builds
 * because a dashboard URL at onrender.com would break cookie auth.
 */
const API_BASE =
    import.meta.env.DEV &&
    typeof import.meta.env.VITE_API_URL === "string" &&
    import.meta.env.VITE_API_URL.startsWith("http")
        ? import.meta.env.VITE_API_URL
        : "/api";

const apiClient = axios.create({
    baseURL: API_BASE,
    withCredentials: true,
    headers: {
        "Content-Type": "application/json",
    },
});

// FormData must not keep application/json — browser sets multipart + boundary
apiClient.interceptors.request.use((config) => {
    if (typeof FormData !== "undefined" && config.data instanceof FormData) {
        const headers = config.headers;
        if (headers && typeof headers.set === "function") {
            headers.set("Content-Type", false);
        } else if (headers) {
            delete (headers as Record<string, unknown>)["Content-Type"];
            delete (headers as Record<string, unknown>)["content-type"];
        }
    }
    return config;
});

// Guard against SPA HTML leaking through a broken /api rewrite
apiClient.interceptors.response.use((response) => {
    // Blob / ArrayBuffer downloads (CSV export) are not HTML JSON responses
    if (
        typeof Blob !== "undefined" &&
        response.data instanceof Blob
    ) {
        return response;
    }
    if (response.data instanceof ArrayBuffer) {
        return response;
    }

    const contentType = String(response.headers["content-type"] ?? "");
    if (
        contentType.includes("text/html") ||
        (typeof response.data === "string" &&
            response.data.trimStart().startsWith("<!doctype"))
    ) {
        return Promise.reject(
            new Error("API returned HTML instead of JSON — check /api proxy")
        );
    }
    return response;
});

type QueueItem = {
    resolve: () => void;
    reject: (error: unknown) => void;
};

let isRefreshing = false;
let failedQueue: QueueItem[] = [];

function processQueue(error: unknown) {
    failedQueue.forEach((item) => {
        if (error) {
            item.reject(error);
        } else {
            item.resolve();
        }
    });
    failedQueue = [];
}

function redirectToLogin() {
    useAuthStore.getState().clearSession();
    window.location.href = "/login";
}

// On 401, try one cookie-based refresh+retry; otherwise clear session and go to login
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        const status = error.response?.status;
        const requestUrl: string = originalRequest?.url ?? "";

        const skipRefresh =
            requestUrl.includes("/auth/refresh") ||
            requestUrl.includes("/auth/login") ||
            requestUrl.includes("/auth/register") ||
            requestUrl.includes("/auth/logout") ||
            // Wrong current password returns 401 — not an expired session
            requestUrl.includes("/users/me/password");

        if (
            status !== 401 ||
            !originalRequest ||
            originalRequest._retry ||
            skipRefresh
        ) {
            if (status === 401 && !skipRefresh) {
                redirectToLogin();
            }
            return Promise.reject(error);
        }

        if (isRefreshing) {
            return new Promise<void>((resolve, reject) => {
                failedQueue.push({ resolve, reject });
            }).then(() => apiClient(originalRequest));
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
            await axios.post(
                `${API_BASE}/auth/refresh`,
                {},
                {
                    withCredentials: true,
                    headers: { "Content-Type": "application/json" },
                }
            );

            processQueue(null);
            return apiClient(originalRequest);
        } catch (refreshError) {
            processQueue(refreshError);
            redirectToLogin();
            return Promise.reject(refreshError);
        } finally {
            isRefreshing = false;
        }
    }
);

export default apiClient;
