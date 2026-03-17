import useSWR from "swr";
import { apiRequest } from "@/lib/api/client";

type HealthResponse = {
  status: string;
  env: string;
  service: string;
};

const fetcher = () => apiRequest<HealthResponse>("/api/v1/health");

export function useHealth() {
  const { data, error, isLoading } = useSWR<HealthResponse>("health", fetcher, {
    revalidateOnFocus: false,
    shouldRetryOnError: false
  });

  return {
    data,
    error,
    isLoading
  };
}

