export const TOKEN_KEY = "token";
export const ACCESS_TOKEN_KEY = "access_token";

export function getAuthToken(): string | null {
  try {
    const token = localStorage.getItem(TOKEN_KEY) || localStorage.getItem(ACCESS_TOKEN_KEY);
    if (!token || token.trim() === "" || token === "null" || token === "undefined") {
      return null;
    }
    return token.trim();
  } catch (e) {
    return null;
  }
}

export function setAuthToken(token: string): void {
  if (!token || typeof token !== "string") return;
  try {
    localStorage.setItem(TOKEN_KEY, token.trim());
    localStorage.setItem(ACCESS_TOKEN_KEY, token.trim());
  } catch (e) {
    console.error("Failed to save auth token");
  }
}

export function clearAuthToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(ACCESS_TOKEN_KEY);
  } catch (e) {
    console.error("Failed to clear auth token");
  }
}

export function parseJwtPayload(token: string): any | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    
    let base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    while (base64.length % 4 !== 0) {
      base64 += "=";
    }
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}
