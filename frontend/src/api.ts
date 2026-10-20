export async function api<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`/api${path}`, {signal, ...(body ? {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)} : {})});
  if (!response.ok) throw new Error(`Request failed (${response.status}). Check your match clock and try again.`);
  return response.json();
}
