export type HealthResponse = {
  status: "ok";
  service: string;
  version: string;
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${apiBaseUrl}/health`);

  if (!response.ok) {
    throw new Error(`Healthcheck failed with status ${response.status}`);
  }

  return response.json() as Promise<HealthResponse>;
}
