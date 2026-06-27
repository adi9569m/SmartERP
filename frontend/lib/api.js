const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000/api";

export function getSession() {
  if (typeof window === "undefined") return {};
  return {
    token: localStorage.getItem("smarterp_token"),
    companyId: localStorage.getItem("smarterp_company"),
  };
}

export async function api(path, options = {}) {
  const { token, companyId } = getSession();
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(companyId ? { "X-Company-ID": companyId } : {}),
      ...options.headers,
    },
  });
  if (response.status === 204) return null;
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    if (!response.ok) throw new Error("Request failed");
    return response.blob();
  }
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}

export function logout() {
  localStorage.removeItem("smarterp_token");
  localStorage.removeItem("smarterp_company");
  location.href = "/login";
}
