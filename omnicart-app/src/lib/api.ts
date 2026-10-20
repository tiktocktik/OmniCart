const rawBase = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

/** Single source of truth for the backend URL. Override with NEXT_PUBLIC_API_BASE. */
export const API_BASE = rawBase.replace(/\/+$/, "");
