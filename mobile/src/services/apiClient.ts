/*
KOROBOS — Mobile API Client

Provides cross-platform HTTP client for React Native (AsyncStorage, absolute URLs).
Replaces browser-based fetch with proper mobile auth handling.
*/

let SecureStore: any;

// Try to load SecureStore, fall back gracefully if not available
try {
  SecureStore = require("expo-secure-store");
} catch (e) {
  console.warn("expo-secure-store not available, using in-memory storage");
  SecureStore = {
    getItemAsync: async () => null,
    setItemAsync: async () => {},
    deleteItemAsync: async () => {},
  };
}

const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_URL || "http://localhost:8080/api/v1";

interface RequestOptions extends RequestInit {
  headers?: Record<string, string>;
  method?: string;
}

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  /**
   * Retrieve auth token from secure storage
   */
  private async getAuthToken(): Promise<string | null> {
    try {
      return await SecureStore.getItemAsync("auth_token");
    } catch (error) {
      console.error("Failed to retrieve auth token:", error);
      return null;
    }
  }

  /**
   * Store auth token in secure storage
   */
  async setAuthToken(token: string): Promise<void> {
    try {
      await SecureStore.setItemAsync("auth_token", token);
    } catch (error) {
      console.error("Failed to store auth token:", error);
    }
  }

  /**
   * Clear auth token from secure storage
   */
  async clearAuthToken(): Promise<void> {
    try {
      await SecureStore.deleteItemAsync("auth_token");
    } catch (error) {
      console.error("Failed to clear auth token:", error);
    }
  }

  /**
   * Prepare request headers with auth
   */
  private async prepareHeaders(
    headers: Record<string, string> = {},
  ): Promise<Record<string, string>> {
    const token = await this.getAuthToken();
    const finalHeaders: Record<string, string> = {
      "Content-Type": "application/json",
      ...headers,
    };

    if (token) {
      finalHeaders["Authorization"] = `Bearer ${token}`;
    }

    return finalHeaders;
  }

  /**
   * Make HTTP request with auth
   */
  private async request<T>(
    endpoint: string,
    options: RequestOptions = {},
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const headers = await this.prepareHeaders(options.headers);

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Handle 401 Unauthorized
      if (response.status === 401) {
        await this.clearAuthToken();
        throw new Error("Unauthorized - Please log in again");
      }

      // Handle 4xx/5xx errors
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        );
      }

      return await response.json();
    } catch (error) {
      console.error(
        `API Error [${options.method || "GET"} ${endpoint}]:`,
        error,
      );
      throw error;
    }
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
    let url = endpoint;
    if (params) {
      const queryString = new URLSearchParams(params).toString();
      url = `${endpoint}?${queryString}`;
    }

    return this.request<T>(url, { method: "GET" });
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE" });
  }
}

// Singleton instance
export const apiClient = new ApiClient();

export default ApiClient;
