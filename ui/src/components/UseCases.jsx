import React from 'react'

const COMPLEXITY = [
  {
    icon: '⇄',
    title: 'Schema heterogeneity',
    scenario: 'Salesforce, Databricks, Foundry — no single source of truth',
    body: 'The same entity is modeled differently across systems, and reconciling conflicting representations requires inferring relationships that aren\'t documented anywhere.',
  },
  {
    icon: '∫',
    title: 'Business logic in queries',
    scenario: 'The Redshift → Snowflake migration that produced a $100M reconciliation gap',
    body: 'Transformation isn\'t just reshaping columns. Computed meaning lives in ad-hoc SQL that never makes it into the migration spec.',
  },
  {
    icon: '⚠',
    title: 'Data quality',
    scenario: 'Duplicate rows, broken links, inconsistent date formats in real exports',
    body: 'These surface only when the script runs against full data, by which point the migration is partially committed.',
  },
]

const SCALE = [
  {
    icon: '#',
    title: 'ID remapping',
    scenario: 'Auto-incremented IDs across billions of records with no traceability back to source',
    body: 'Every foreign-key reference must be rewritten consistently across billions of records, in the right order.',
  },
  {
    icon: '⬡',
    title: 'Ordering constraints',
    scenario: '32-layer dependency graph, ~1B records, strict ordering',
    body: 'One step out of order corrupts downstream tables with no easy rollback.',
  },
]

export default function UseCases() {
  return (
    <section id="future" style={{ position:'relative', zIndex:10, maxWidth:1280, margin:'0 auto', padding:'30px 40px 60px', textAlign:'center' }}>
      <div style={{ display:'inline-flex', alignItems:'center', gap:10, fontFamily:"'JetBrains Mono',monospace", fontSize:11, letterSpacing:'.32em', color:'#8b7bff', marginBottom:22 }}>
        <span style={{ width:24, height:1, background:'#8b7bff', display:'inline-block' }} />WHY THIS IS HARD<span style={{ width:24, height:1, background:'#8b7bff', display:'inline-block' }} />
      </div>

      <h2 style={{ margin:'0 0 14px', fontSize:44, lineHeight:1.08, fontWeight:700, letterSpacing:'-.025em' }}>
        Hand-Mapping Migrations Doesn't Scale<br/>
        <span style={{ background:'linear-gradient(100deg,#8b7bff,#2fe6d6)', WebkitBackgroundClip:'text', backgroundClip:'text', color:'transparent' }}>to What the Future Demands</span>
      </h2>

      <p style={{ margin:'0 auto 48px', maxWidth:640, fontSize:15, lineHeight:1.65, color:'#7a839a' }}>
        Enterprise migrations fail along two axes that exceed human bandwidth.
      </p>

      <GroupLabel label="Complexity humans can't track" />
      <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:16, textAlign:'left', marginBottom:16 }}>
        {COMPLEXITY.map(c => <Card key={c.title} c={c} />)}
      </div>

      <GroupLabel label="Scale humans can't manage" />
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, textAlign:'left', marginBottom:40 }}>
        {SCALE.map(c => <Card key={c.title} c={c} />)}
      </div>

      <p style={{ margin:'0 auto', maxWidth:720, fontSize:13.5, lineHeight:1.75, color:'#5a6478', fontStyle:'italic', borderTop:'1px solid rgba(255,255,255,.06)', paddingTop:32 }}>
        The pattern is the same: enterprise migration is a long-horizon reasoning problem under constraints humans can't hold simultaneously in their heads. It's exactly the task models would solve —&nbsp;
        <span style={{ color:'#8b7bff', fontStyle:'normal', fontWeight:500 }}>if they could be trained for it.</span>
      </p>
    </section>
  )
}

function GroupLabel({ label }) {
  return (
    <div style={{ textAlign:'left', marginBottom:14, display:'flex', alignItems:'center', gap:12 }}>
      <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:10.5, letterSpacing:'.18em', color:'#5a6478', textTransform:'uppercase' }}>{label}</span>
      <span style={{ flex:1, height:1, background:'rgba(255,255,255,.06)' }} />
    </div>
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
