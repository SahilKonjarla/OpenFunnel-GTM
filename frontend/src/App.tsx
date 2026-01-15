import React, { useEffect, useState } from 'react'
import { searchJobs, Job } from './api'
import { highlight } from './highlight'

export default function App() {
  const [q, setQ] = useState('')
  const [company, setCompany] = useState('')
  const [city, setCity] = useState('')
  const [minSalary, setMinSalary] = useState('')
  const [roleFunction, setRoleFunction] = useState('')
  const [seniority, setSeniority] = useState('')
  const [skill, setSkill] = useState('')
  const [items, setItems] = useState<Job[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function runSearch() {
    setLoading(true); setError(null)
    try {
      const res = await searchJobs({
        q, company, city,
        min_salary: minSalary ? Number(minSalary) : undefined,
        role_function: roleFunction || undefined,
        seniority: seniority || undefined,
        skill: skill || undefined,
        limit: 50,
        offset: 0,
      })
      setItems(res.items)
    } catch (e: any) {
      setError(e?.message ?? 'unknown error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { runSearch() }, [])

  return (
    <div style={{ fontFamily: 'system-ui', padding: 16, maxWidth: 1200, margin: '0 auto' }}>
      <h2>OpenFunnel – Job GTM Intelligence</h2>
      <p style={{ marginTop: 4, color: '#555' }}>
        Search across ingested job postings and filter by company, role, salary, location, and skills.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginTop: 12 }}>
        <label>Title query<input value={q} onChange={(e) => setQ(e.target.value)} style={{ width: '100%' }} /></label>
        <label>Company<input value={company} onChange={(e) => setCompany(e.target.value)} style={{ width: '100%' }} /></label>
        <label>City<input value={city} onChange={(e) => setCity(e.target.value)} style={{ width: '100%' }} /></label>

        <label>Min salary<input value={minSalary} onChange={(e) => setMinSalary(e.target.value)} style={{ width: '100%' }} /></label>
        <label>Role function<input value={roleFunction} onChange={(e) => setRoleFunction(e.target.value)} style={{ width: '100%' }} /></label>
        <label>Seniority<input value={seniority} onChange={(e) => setSeniority(e.target.value)} style={{ width: '100%' }} /></label>

        <label>Skill contains (canonical)<input value={skill} onChange={(e) => setSkill(e.target.value)} style={{ width: '100%' }} /></label>

        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8 }}>
          <button onClick={runSearch}>Search</button>
          {loading ? <span>Loading…</span> : null}
        </div>
      </div>

      {error ? <p style={{ color: 'crimson' }}>{error}</p> : null}

      <div style={{ marginTop: 16 }}>
        <h3>Results ({items.length})</h3>
        <div style={{ display: 'grid', gap: 12 }}>
          {items.map((it) => (
            <div key={it.id} style={{ border: '1px solid #ddd', borderRadius: 10, padding: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                <div>
                  <div style={{ fontSize: 14, color: '#333' }}>{it.company_name}</div>
                  <div style={{ fontSize: 18 }}>
                    {it.canonical_url ? (
                      <a href={it.canonical_url} target="_blank" rel="noreferrer">{it.title ?? '(untitled)'}</a>
                    ) : (it.title ?? '(untitled)')}
                  </div>
                  <div style={{ fontSize: 13, color: '#555' }}>
                    {it.location_raw ?? it.location_city ?? '—'} · {it.seniority ?? '—'} · {it.role_function ?? '—'} · status: {it.status}
                  </div>
                </div>
                <div style={{ textAlign: 'right', fontSize: 13, color: '#555' }}>
                  <div>salary: {it.salary_min ?? '—'} – {it.salary_max ?? '—'}</div>
                  <div>skills: {(it.skills ?? []).slice(0, 10).join(', ')}</div>
                </div>
              </div>

              {it.summary ? <p style={{ marginTop: 10 }}>{it.summary}</p> : null}

              {it.description_text ? (
                <details style={{ marginTop: 8 }}>
                  <summary>Show raw posting (highlight query)</summary>
                  <div
                    style={{ marginTop: 8, padding: 10, background: '#fafafa', borderRadius: 8, overflowX: 'auto' }}
                    dangerouslySetInnerHTML={{ __html: highlight(it.description_text, q) }}
                  />
                </details>
              ) : null}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
