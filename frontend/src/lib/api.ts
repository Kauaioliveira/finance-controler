import type {
  ApiConfig,
  ApiErrorPayload,
  AuthTokenResponse,
  AuthUser,
  FieldError,
  FinanceCategoryCatalogResponse,
  FinanceImportListResponse,
  FinanceImportResponse,
  FinanceReportResponse,
  FinanceTransactionListResponse,
  FinalizeFinanceImportResponse,
  HealthStatus,
  StoredSession,
  UserListResponse,
  UserResponse,
} from "../types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8010";
const SESSION_KEY = "finance-controler.session";

type RequestOptions = {
  auth?: boolean;
  retryOnAuth?: boolean;
};

type RequestInitWithJson = RequestInit & {
  json?: unknown;
};

type CreateUserPayload = {
  name: string;
  email: string;
  role: "admin" | "analyst" | "viewer";
  password: string;
};

type UpdateUserPayload = {
  name?: string;
  role?: "admin" | "analyst" | "viewer";
};

type UpdateTransactionPayload = {
  final_category: string;
  review_notes: string | null;
};

type ListImportsParams = {
  page?: number;
  pageSize?: number;
  status?: string;
  dateFrom?: string;
  dateTo?: string;
  uploadedByUserId?: string;
};

type ListTransactionsParams = {
  page?: number;
  pageSize?: number;
  category?: string;
  query?: string;
};

export class ApiError extends Error {
  status: number;
  code: string;
  fieldErrors: FieldError[];

  constructor(
    status: number,
    detail: string,
    code = "api_error",
    fieldErrors: FieldError[] = [],
  ) {
    super(detail);
    this.status = status;
    this.code = code;
    this.fieldErrors = fieldErrors;
  }
}

let sessionCache: StoredSession | null = null;
let refreshPromise: Promise<StoredSession | null> | null = null;

function getStorage(): Storage | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.sessionStorage;
}

function persistSession(session: StoredSession | null) {
  sessionCache = session;
  const storage = getStorage();
  if (!storage) {
    return;
  }

  if (session) {
    storage.setItem(SESSION_KEY, JSON.stringify(session));
  } else {
    storage.removeItem(SESSION_KEY);
  }
}

function restoreSession(): StoredSession | null {
  if (sessionCache) {
    return sessionCache;
  }

  const storage = getStorage();
  if (!storage) {
    return null;
  }

  const raw = storage.getItem(SESSION_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as StoredSession;
    sessionCache = parsed;
    return parsed;
  } catch {
    storage.removeItem(SESSION_KEY);
    return null;
  }
}

function buildHeaders(init?: HeadersInit, hasJsonBody = false): Headers {
  const headers = new Headers(init ?? {});
  if (hasJsonBody && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return headers;
}

function withQuery(path: string, params: Record<string, string | number | undefined>) {
  const url = new URL(`${API_BASE_URL}${path}`);
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") {
      continue;
    }
    url.searchParams.set(key, String(value));
  }
  return url.toString();
}

async function performRefresh(): Promise<StoredSession | null> {
  const current = restoreSession();
  if (!current?.refreshToken) {
    persistSession(null);
    return null;
  }

  try {
    const refreshed = await rawRequest<AuthTokenResponse>(
      "/auth/refresh",
      {
        method: "POST",
        json: {
          refresh_token: current.refreshToken,
        },
      },
      {
        auth: false,
        retryOnAuth: false,
      },
    );

    const nextSession = toStoredSession(refreshed);
    persistSession(nextSession);
    return nextSession;
  } catch {
    persistSession(null);
    return null;
  }
}

async function refreshSession(): Promise<StoredSession | null> {
  if (!refreshPromise) {
    refreshPromise = performRefresh().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

async function rawRequest<T>(
  path: string,
  init?: RequestInitWithJson,
  options?: RequestOptions,
): Promise<T> {
  const auth = options?.auth ?? true;
  const retryOnAuth = options?.retryOnAuth ?? auth;
  const current = restoreSession();
  const hasJsonBody = Object.prototype.hasOwnProperty.call(init ?? {}, "json");
  const headers = buildHeaders(init?.headers, hasJsonBody);

  if (auth && current?.accessToken) {
    headers.set("Authorization", `Bearer ${current.accessToken}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    body: hasJsonBody ? JSON.stringify(init?.json ?? null) : init?.body,
  });

  if (response.status === 401 && retryOnAuth && current?.refreshToken) {
    const refreshed = await refreshSession();
    if (refreshed?.accessToken) {
      return rawRequest<T>(path, init, {
        ...options,
        retryOnAuth: false,
      });
    }
  }

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as ApiErrorPayload | null;
    throw new ApiError(
      response.status,
      payload?.detail ?? "Falha ao consultar a API.",
      payload?.code ?? "api_error",
      payload?.field_errors ?? [],
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

function toStoredSession(payload: AuthTokenResponse): StoredSession {
  return {
    accessToken: payload.access_token,
    refreshToken: payload.refresh_token,
    user: payload.user,
  };
}

export const api = {
  getApiBaseUrl() {
    return API_BASE_URL;
  },
  restoreSession,
  persistSession,
  async bootstrapSession(): Promise<StoredSession | null> {
    const current = restoreSession();
    if (!current) {
      return null;
    }

    try {
      const user = await rawRequest<AuthUser>("/auth/me");
      const nextSession = {
        ...current,
        user,
      };
      persistSession(nextSession);
      return nextSession;
    } catch {
      return refreshSession();
    }
  },
  async login(email: string, password: string): Promise<StoredSession> {
    const payload = await rawRequest<AuthTokenResponse>(
      "/auth/login",
      {
        method: "POST",
        json: {
          email,
          password,
        },
      },
      {
        auth: false,
        retryOnAuth: false,
      },
    );
    const nextSession = toStoredSession(payload);
    persistSession(nextSession);
    return nextSession;
  },
  async logout(): Promise<void> {
    const current = restoreSession();
    if (current?.refreshToken) {
      await rawRequest<{ detail: string }>(
        "/auth/logout",
        {
          method: "POST",
          json: {
            refresh_token: current.refreshToken,
          },
        },
        {
          auth: false,
          retryOnAuth: false,
        },
      ).catch(() => undefined);
    }
    persistSession(null);
  },
  async getMe() {
    return rawRequest<AuthUser>("/auth/me");
  },
  getHealth() {
    return rawRequest<HealthStatus>("/health", undefined, {
      auth: false,
      retryOnAuth: false,
    });
  },
  getConfig() {
    return rawRequest<ApiConfig>("/config", undefined, {
      auth: false,
      retryOnAuth: false,
    });
  },
  getFinanceCategories() {
    return rawRequest<FinanceCategoryCatalogResponse>("/finance/categories");
  },
  listFinanceImports(params: ListImportsParams = {}) {
    return rawRequest<FinanceImportListResponse>(
      withQuery("/finance/imports", {
        page: params.page ?? 1,
        page_size: params.pageSize ?? 12,
        status: params.status,
        date_from: params.dateFrom,
        date_to: params.dateTo,
        uploaded_by_user_id: params.uploadedByUserId,
      }).replace(API_BASE_URL, ""),
    );
  },
  createFinanceImport(file: File) {
    const body = new FormData();
    body.append("file", file);
    return rawRequest<FinanceImportResponse>("/finance/imports", {
      method: "POST",
      body,
    });
  },
  getFinanceImport(importId: string) {
    return rawRequest<FinanceImportResponse>(`/finance/imports/${importId}`);
  },
  getFinanceTransactions(importId: string, params: ListTransactionsParams = {}) {
    return rawRequest<FinanceTransactionListResponse>(
      withQuery(`/finance/imports/${importId}/transactions`, {
        page: params.page ?? 1,
        page_size: params.pageSize ?? 25,
        category: params.category,
        query: params.query,
      }).replace(API_BASE_URL, ""),
    );
  },
  updateFinanceTransaction(
    importId: string,
    transactionId: string,
    payload: UpdateTransactionPayload,
  ) {
    return rawRequest(`/finance/imports/${importId}/transactions/${transactionId}`, {
      method: "PATCH",
      json: payload,
    });
  },
  finalizeFinanceImport(importId: string) {
    return rawRequest<FinalizeFinanceImportResponse>(
      `/finance/imports/${importId}/finalize`,
      {
        method: "POST",
      },
    );
  },
  getFinanceReport(importId: string) {
    return rawRequest<FinanceReportResponse>(`/finance/imports/${importId}/report`);
  },
  listUsers(page = 1, pageSize = 25) {
    return rawRequest<UserListResponse>(
      withQuery("/users", {
        page,
        page_size: pageSize,
      }).replace(API_BASE_URL, ""),
    );
  },
  createUser(payload: CreateUserPayload) {
    return rawRequest<UserResponse>("/users", {
      method: "POST",
      json: payload,
    });
  },
  updateUser(userId: string, payload: UpdateUserPayload) {
    return rawRequest<UserResponse>(`/users/${userId}`, {
      method: "PATCH",
      json: payload,
    });
  },
  updateUserStatus(userId: string, isActive: boolean) {
    return rawRequest<UserResponse>(`/users/${userId}/status`, {
      method: "PATCH",
      json: {
        is_active: isActive,
      },
    });
  },
  updateUserPassword(userId: string, password: string) {
    return rawRequest<{ detail: string }>(`/users/${userId}/password`, {
      method: "PATCH",
      json: {
        password,
      },
    });
  },
};
