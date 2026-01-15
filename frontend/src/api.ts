export type Job = {
  id: string
  company_name: string
  title: string | null
  location_raw: string | null
  location_city: string | null
  salary_min: number | null
  salary_max: number | null
  seniority: string | null
  role_function: string | null
  skills: string[] | null
  summary: string | null
  canonical_url: string | null
  status: string
  description_text: string | null
}
const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'
export async function searchJobs(params: Record<string, string | number | undefined>) {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== '') qs.set(k, String(v)) })
  const res = await fetch(`${API_BASE}/jobs/search?${qs.toString()}`)
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return (await res.json()) as { count: number; items: Job[] }
}
