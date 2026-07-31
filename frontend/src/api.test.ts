import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "./api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("API client", () => {
  it("loads the public runtime configuration", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          appVersion: "0.2.3",
          buildTag: "test.1",
          profiles: [],
          defaultProfile: "demo",
          maxUploadBytes: 1024,
          supportedExtensions: [".txt"],
          sessionIdleMinutes: 60,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const config = await api.config();

    expect(config.defaultProfile).toBe("demo");
    expect(fetchMock).toHaveBeenCalledWith("/api/v1/config", undefined);
  });

  it("surfaces the safe API error message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: {
              code: "QUEUE_FULL",
              message: "The workflow queue is full.",
              retryable: true,
            },
          }),
          { status: 503, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    await expect(api.config()).rejects.toEqual(
      expect.objectContaining({
        message: "The workflow queue is full.",
        status: 503,
        retryable: true,
      }),
    );
  });
});
