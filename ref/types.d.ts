// Cloudflare Workers types

export interface ExecutionContext {
  waitUntil(promise: Promise<any>): void;
  passThroughOnException(): void;
}

// Re-export for convenience
export type { ExecutionContext as CloudflareExecutionContext };