import React from 'react'
const CAPS = [
  { tag:'▣ NO SCRIPTS',  label:'Discovers schemas automatically', accent:'#8b7bff' },
  { tag:'⟳ SELF-REPAIRING', label:'Diagnoses failures and retries', accent:'#8b7bff' },
  { tag:'✓ END-TO-END',  label:'Proves records survived', accent:'#2fe6d6' },
]
export default function CapabilityStrip() {
  return (
    <section style={{ position:'relative', zIndex:10, maxWidth:1280, margin:'0 auto', padding:'0 40px 60px' }}>
      <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:1, border:'1px solid rgba(255,255,255,.07)', borderRadius:14, overflow:'hidden', background:'rgba(255,255,255,.05)' }}>
        {CAPS.map(c => (
          <div key={c.tag} style={{ padding:'24px 26px', background:'#080a12' }}>
            <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:10, letterSpacing:'.16em', color:c.accent, marginBottom:8 }}>{c.tag}</div>
            <div style={{ fontWeight:600, fontSize:15 }}>{c.label}</div>
          </div>
        ))}
      </div>
    </section>
  )
}
