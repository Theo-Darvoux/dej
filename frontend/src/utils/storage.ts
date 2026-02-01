/**
 * Safe localStorage utilities that handle corrupted data gracefully.
 */

/**
 * Safely parse JSON from localStorage, returning a default value if parsing fails.
 * Clears the corrupted key to prevent repeated errors.
 *
 * @param key - The localStorage key to read
 * @param defaultValue - Value to return if key doesn't exist or is corrupted
 * @returns The parsed value or defaultValue
 */
export function safeJSONParse<T>(key: string, defaultValue: T): T {
    try {
        const saved = localStorage.getItem(key)
        if (!saved) return defaultValue
        return JSON.parse(saved) as T
    } catch (e) {
        console.error(`Corrupted localStorage key "${key}", clearing:`, e)
        localStorage.removeItem(key)
        return defaultValue
    }
}

/**
 * Safely get a string value from localStorage.
 *
 * @param key - The localStorage key to read
 * @param defaultValue - Value to return if key doesn't exist (default: '')
 * @returns The stored string or defaultValue
 */
export function safeGetItem(key: string, defaultValue: string = ''): string {
    try {
        return localStorage.getItem(key) || defaultValue
    } catch (e) {
        console.error(`Error reading localStorage key "${key}":`, e)
        return defaultValue
    }
}
