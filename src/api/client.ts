import {
  ApiError,
  type ApiEnvelope,
  type ApiMethod,
  type ApiProblem,
  type ApiResponse,
  type JsonObject,
  type JsonValue,
  type QueryParams,
} from "@/types/api";

const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";
const DEFAULT_TIMEOUT_MS = 15_000;

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL).replace(
  /\/$/,
  "",
);

export interface RequestOptions extends Omit<
  RequestInit,
  "body" | "headers" | "method" | "signal"
> {
  body?: BodyInit | JsonValue | null;
  headers?: HeadersInit;
  query?: object;
  signal?: AbortSignal;
  timeoutMs?: number;
}

function buildUrl(path: string, query?: object): string {
  const url = new URL(path.replace(/^\//, ""), `${API_BASE_URL}/`);
  const entries = Object.entries(query ?? {}) as Array<[string, QueryParams[string]]>;
  for (const [key, value] of entries) {
    if (value === undefined || value === null) continue;
    for (const item of Array.isArray(value) ? value : [value]) {
      url.searchParams.append(key, String(item));
    }
  }
  return url.toString();
}

function isJsonBody(body: RequestOptions["body"]): body is JsonValue {
  return (
    body !== null &&
    typeof body === "object" &&
    !(body instanceof Blob) &&
    !(body instanceof FormData) &&
    !(body instanceof URLSearchParams) &&
    !(body instanceof ArrayBuffer)
  );
}

async function parseJson(body: string, status: number): Promise<JsonValue> {
  try {
    return JSON.parse(body) as JsonValue;
  } catch (cause) {
    throw new ApiError({
      kind: "invalid_json",
      message: "The API returned an invalid JSON response.",
      status,
      cause,
    });
  }
}

function problemFromBody(body: JsonValue | undefined, fallback: string): ApiProblem {
  if (body !== null && typeof body === "object" && !Array.isArray(body)) {
    const candidate = body as JsonObject;
    const detail = candidate.detail;
    if (typeof detail === "string") return { message: detail };
    if (detail !== null && typeof detail === "object" && !Array.isArray(detail)) {
      const detailObject = detail as JsonObject;
      return {
        code: typeof detailObject.code === "string" ? detailObject.code : undefined,
        message: typeof detailObject.message === "string" ? detailObject.message : fallback,
        details: detail,
      };
    }
    if (typeof candidate.message === "string") return { message: candidate.message, details: body };
  }
  return { message: fallback, details: body };
}

function isEnvelope<T>(value: JsonValue): value is JsonObject & ApiEnvelope<T> {
  return (
    value !== null &&
    typeof value === "object" &&
    !Array.isArray(value) &&
    "data" in value &&
    "metadata" in value &&
    "api_version" in value
  );
}

/**
 * Sends a versioned TITAN request and unwraps the backend's opt-in response
 * envelope. All non-success paths are exposed as ApiError instances.
 */
export async function request<T>(
  method: ApiMethod,
  path: string,
  options: RequestOptions = {},
): Promise<ApiResponse<T>> {
  const {
    body,
    headers: suppliedHeaders,
    query,
    signal,
    timeoutMs = DEFAULT_TIMEOUT_MS,
    ...init
  } = options;
  const controller = new AbortController();
  let timedOut = false;
  const timeout = globalThis.setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
  const abortFromCaller = () => controller.abort(signal?.reason);

  if (signal?.aborted) abortFromCaller();
  signal?.addEventListener("abort", abortFromCaller, { once: true });

  const headers = new Headers(suppliedHeaders);
  headers.set("Accept", "application/json");
  headers.set("X-TITAN-Response-Envelope", "v1");
  if (isJsonBody(body)) headers.set("Content-Type", "application/json");

  try {
    const response = await fetch(buildUrl(path, query), {
      ...init,
      method,
      headers,
      body: isJsonBody(body) ? JSON.stringify(body) : body,
      signal: controller.signal,
    });
    const text = await response.text();
    const parsed = text ? await parseJson(text, response.status) : undefined;

    if (!response.ok) {
      const fallback = `The API request failed with status ${response.status}.`;
      const problem = problemFromBody(parsed, fallback);
      throw new ApiError({
        kind: "http",
        message: problem.message,
        status: response.status,
        problem,
      });
    }
    if (parsed === undefined) {
      return {
        data: undefined as T,
        metadata: {},
        requestId: null,
        apiVersion: null,
        timestamp: null,
        status: response.status,
      };
    }
    if (!isEnvelope<T>(parsed)) {
      throw new ApiError({
        kind: "invalid_json",
        message: "The API response did not match the TITAN response envelope.",
        status: response.status,
      });
    }
    return {
      data: parsed.data as T,
      metadata: parsed.metadata,
      requestId: parsed.request_id,
      apiVersion: parsed.api_version,
      timestamp: parsed.timestamp,
      status: response.status,
    };
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (timedOut)
      throw new ApiError({ kind: "timeout", message: "The API request timed out.", cause: error });
    if (controller.signal.aborted)
      throw new ApiError({
        kind: "aborted",
        message: "The API request was cancelled.",
        cause: error,
      });
    throw new ApiError({ kind: "network", message: "Unable to reach the API.", cause: error });
  } finally {
    globalThis.clearTimeout(timeout);
    signal?.removeEventListener("abort", abortFromCaller);
  }
}

export const apiClient = {
  get: <T>(path: string, options?: RequestOptions) => request<T>("GET", path, options),
  post: <T>(path: string, options?: RequestOptions) => request<T>("POST", path, options),
  put: <T>(path: string, options?: RequestOptions) => request<T>("PUT", path, options),
  patch: <T>(path: string, options?: RequestOptions) => request<T>("PATCH", path, options),
  delete: <T = void>(path: string, options?: RequestOptions) => request<T>("DELETE", path, options),
};
