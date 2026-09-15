const rawUrl = import.meta.env.VITE_API_URL || "https://project-nexora.onrender.com";
export const API_URL = rawUrl.replace(/\/+$/, "");

if (import.meta.env.PROD && !import.meta.env.VITE_API_URL) {
  console.warn("VITE_API_URL is not defined in production build environment. Falling back to default.");
}
