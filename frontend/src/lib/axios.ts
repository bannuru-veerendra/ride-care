import axios from "axios";

/**
 * Axios instance configured with the base API URL.
 * JWT token is automatically attached to every request
 * via the request interceptor below.
 */
const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

type QueueItem = {
    resolve: (token: string) => void;
    reject: (error: unknown) => void;
};

let isRefreshing = false;
let failedQueue: QueueItem[] = [];

function processQueue(error: unknown, token: string | null) {
    failedQueue.forEach((item) => {
        if (error || !token) {
            item.reject(error);
        } else {
            item.resolve(token);
        }
    });
    failedQueue = [];
}

function clearAuthStorage() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
}

function redirectToLogin() {
    clearAuthStorage();
    window.location.href = "/login";
}

// Attach JWT token to every outgoing request
apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// On 401, try one refresh+retry; otherwise clear session and go to login
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
            requestUrl.includes("/auth/logout");

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
            return new Promise<string>((resolve, reject) => {
                failedQueue.push({ resolve, reject });
            }).then((token) => {
                originalRequest.headers.Authorization = `Bearer ${token}`;
                return apiClient(originalRequest);
            });
        }

        originalRequest._retry = true;
        isRefreshing = true;

        const refreshToken = localStorage.getItem("refresh_token");
        if (!refreshToken) {
            isRefreshing = false;
            redirectToLogin();
            return Promise.reject(error);
        }

        try {
            const { data } = await axios.post(
                `${import.meta.env.VITE_API_URL}/auth/refresh`,
                { refresh_token: refreshToken },
                { headers: { "Content-Type": "application/json" } }
            );

            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("refresh_token", data.refresh_token);
            processQueue(null, data.access_token);

            originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
            return apiClient(originalRequest);
        } catch (refreshError) {
            processQueue(refreshError, null);
            redirectToLogin();
            return Promise.reject(refreshError);
        } finally {
            isRefreshing = false;
        }
    }
);

export default apiClient;
