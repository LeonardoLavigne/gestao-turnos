import axios from 'axios';

console.log('API Base URL Env:', process.env.NEXT_PUBLIC_API_URL);

// Use absolute URL on server-side, relative URL on client-side (to leverage Next.js rewrites/proxy)
// This ensures cookies set by the backend are correctly associated with the frontend domain (localhost)
const baseURL = typeof window === 'undefined'
    ? (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000')
    : '';

const api = axios.create({
    baseURL: baseURL,
    headers: {
        'Content-Type': 'application/json',
    },
});

api.interceptors.request.use(
    (config) => {
        // No manual Authorization header needed (Using HttpOnly Cookies)
        // Ensure credentials are sent with requests (cookies)
        config.withCredentials = true;
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            if (typeof window !== 'undefined') {
                localStorage.removeItem('user'); // Optional: Clear user metadata if stored
                // Avoid infinite loop if already on login
                if (!window.location.pathname.includes('/login')) {
                    window.location.href = '/login';
                }
            }
        }
        return Promise.reject(error);
    }
);

export default api;