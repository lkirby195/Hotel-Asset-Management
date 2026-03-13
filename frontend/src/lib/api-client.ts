import axios from "axios";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const DEV_AUTH_BYPASS = process.env.NEXT_PUBLIC_DEV_AUTH_BYPASS === "true";
const DEV_USER_EMAIL = process.env.NEXT_PUBLIC_DEV_USER_EMAIL || "logan.kirby14@gmail.com";

export function createApiClient(getToken: () => Promise<string | null>) {
  const client = axios.create({
    baseURL: API_BASE_URL,
  });

  client.interceptors.request.use(async (config) => {
    if (DEV_AUTH_BYPASS) {
      config.headers["X-Dev-User-Email"] = DEV_USER_EMAIL;
      return config;
    }
    const token = await getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  return client;
}
