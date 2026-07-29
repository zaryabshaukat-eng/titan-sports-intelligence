/** Shared transport contracts used by every frontend API module. */

export type ApiMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
export type ResourceId = string;
export type IsoDateTime = string;

export type JsonPrimitive = boolean | number | string | null;
export type JsonValue = JsonPrimitive | JsonObject | JsonValue[];
export interface JsonObject {
  [key: string]: JsonValue;
}

export interface ApiEnvelope<T> {
  data: T;
  metadata: JsonObject;
  request_id: string | null;
  api_version: string;
  timestamp: IsoDateTime;
}

export interface ApiResponse<T> {
  data: T;
  metadata: JsonObject;
  requestId: string | null;
  apiVersion: string | null;
  timestamp: IsoDateTime | null;
  status: number;
}

export interface ApiPage<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface PaginationParams {
  limit?: number;
  offset?: number;
}

export type QueryValue =
  boolean | number | string | null | undefined | ReadonlyArray<boolean | number | string>;
export type QueryParams = Record<string, QueryValue>;

export type ApiErrorKind = "aborted" | "http" | "invalid_json" | "network" | "timeout";

export interface ApiProblem {
  code?: string;
  message: string;
  details?: JsonValue;
}

export interface ApiErrorOptions {
  kind: ApiErrorKind;
  message: string;
  status?: number;
  problem?: ApiProblem;
  cause?: unknown;
}

/** Normalized error thrown by all request helpers. */
export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status?: number;
  readonly problem?: ApiProblem;

  constructor({ kind, message, status, problem, cause }: ApiErrorOptions) {
    super(message, cause === undefined ? undefined : { cause });
    this.name = "ApiError";
    this.kind = kind;
    this.status = status;
    this.problem = problem;
  }
}
