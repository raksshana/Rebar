import React from 'react'

const CASES = [
  {
    icon: '⇄',
    title: 'Schema heterogeneity',
    scenario: 'Multiple vendors (Salesforce, Databricks, Foundry) with no single source of truth',
    body: 'The same entity is modeled differently across systems. The agent must reconcile conflicting representations without explicit documentation.',
  },
  {
    icon: '∫',
    title: 'Business logic in queries',
    scenario: '$100M reconciliation gaps after Redshift → Snowflake',
    body: 'Transformation is not just reshaping columns. Computed meaning lives in ad-hoc SQL the agent never sees.',
  },
  {
    icon: '#',
    title: 'ID remapping',
    scenario: 'Auto-incremented IDs in the new system with no traceability back to Salesforce',
    body: 'New primary keys are generated and every foreign-key reference must be rewritten consistently across tables.',
  },
  {
    icon: '⬡',
    title: 'Ordering constraints at scale',
    scenario: '32-layer dependency graph, ~1B records, strict ordering (migrate X before Y)',
    body: 'Topological dependencies plus volume. One wrong step corrupts downstream tables with no easy rollback.',
  },
  {
    icon: '⚠',
    title: 'Data quality',
    scenario: 'Excel exports with duplicate rows, broken links, and inconsistent date formats',
    body: 'Nulls, format drift, orphan references, and duplicates that only surface when the script runs on the full dataset.',
  },
]

export default function UseCases() {
  return (
    <section style={{ position:'relative', zIndex:10, maxWidth:1280, margin:'0 auto', padding:'30px 40px 60px', textAlign:'center' }}>
      <div style={{ display:'inline-flex', alignItems:'center', gap:10, fontFamily:"'JetBrains Mono',monospace", fontSize:11, letterSpacing:'.32em', color:'#8b7bff', marginBottom:22 }}>
        <span style={{ width:24, height:1, background:'#8b7bff', display:'inline-block' }} />WHY THIS IS HARD<span style={{ width:24, height:1, background:'#8b7bff', display:'inline-block' }} />
      </div>
      <h2 style={{ margin:'0 0 44px', fontSize:48, lineHeight:1.05, fontWeight:700, letterSpacing:'-.025em' }}>
        Migrations too complex<br/>
        <span style={{ background:'linear-gradient(100deg,#8b7bff,#2fe6d6)', WebkitBackgroundClip:'text', backgroundClip:'text', color:'transparent' }}>to map by hand.</span>
      </h2>
      <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:16, textAlign:'left' }}>
        {CASES.slice(0,3).map(c => <Card key={c.title} c={c} />)}
      </div>
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, textAlign:'left', marginTop:16 }}>
        {CASES.slice(3).map(c => <Card key={c.title} c={c} />)}
      </div>
    </section>
  )
}

function Card({ c }) {
  return (
    <div style={{ border:'1px solid rgba(255,255,255,.08)', borderRadius:14, padding:24, background:'rgba(255,255,255,.015)' }}>
      <div style={{ width:36, height:36, borderRadius:9, background:'rgba(139,123,255,.12)', border:'1px solid rgba(139,123,255,.3)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:15, marginBottom:16, fontFamily:"'JetBrains Mono',monospace", color:'#8b7bff' }}>{c.icon}</div>
      <div style={{ fontWeight:600, fontSize:15, marginBottom:6 }}>{c.title}</div>
      <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:10.5, color:'#5a6178', marginBottom:10, lineHeight:1.5 }}>{c.scenario}</div>
      <p style={{ margin:0, fontSize:13, lineHeight:1.55, color:'#9aa3b8' }}>{c.body}</p>
    </div>
  )
}
