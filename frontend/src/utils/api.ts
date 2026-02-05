/**
 * API utilities with automatic token refresh
 *
 * Provides fetchWithAuth() wrapper that:
 * - Automatically includes credentials (cookies)
 * - Detects 401 errors
 * - Attempts token refresh
 * - Retries failed request with new token
 * - Falls back to 401 if refresh fails
 */

let isRefreshing = false;
let refreshPromise: Promise<boolean> | null = null;

/**
 * Refresh the access token using the refresh token cookie
 * Uses singleton pattern to prevent multiple simultaneous refresh attempts
 */
async function refreshToken(): Promise<boolean> {
    // If already refreshing, return the existing promise
    if (isRefreshing && refreshPromise) {
        return refreshPromise;
    }

    isRefreshing = true;
    refreshPromise = (async () => {
        try {
            const response = await fetch('/api/auth/refresh', {
                method: 'POST',
                credentials: 'include', // Send cookies
            });

            if (response.ok) {
                console.log('[AUTH] Token refreshed successfully');
                return true;
            }

            console.log('[AUTH] Token refresh failed:', response.status);
            return false;
        } catch (error) {
            console.error('[AUTH] Token refresh error:', error);
            return false;
        } finally {
            isRefreshing = false;
            refreshPromise = null;
        }
    })();

    return refreshPromise;
}

/**
 * Fetch wrapper with automatic token refresh on 401
 *
 * @param url - The URL to fetch
 * @param options - Fetch options (credentials: 'include' is added automatically)
 * @returns Response object
 *
 * Usage:
 *   const response = await fetchWithAuth('/api/reservations/availability')
 *   if (response.ok) {
 *       const data = await response.json()
 *   }
 */
export async function fetchWithAuth(url: string, options?: RequestInit): Promise<Response> {
    // First attempt
    const response = await fetch(url, {
        ...options,
        credentials: 'include', // Always include cookies
    });

    // If 401 (Unauthorized), try to refresh token and retry once
    if (response.status === 401) {
        console.log('[AUTH] 401 detected, attempting token refresh...');

        const refreshed = await refreshToken();

        if (refreshed) {
            // Retry the original request with new token
            console.log('[AUTH] Retrying request with new token...');
            return fetch(url, {
                ...options,
                credentials: 'include',
            });
        }

        console.log('[AUTH] Refresh failed, returning 401');
    }

    return response;
}
