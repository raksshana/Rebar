import React from 'react'
const CASES = [
  { icon:'▤', title:'CRM modernization',    body:'Move customer, account, and activity data into a new system.' },
  { icon:'✦', title:'Database consolidation', body:'Merge inconsistent schemas from acquired teams or legacy products.' },
  { icon:'⟨⟩', title:'Platform replacement',  body:'Translate records and relationships while preserving business meaning.' },
]
const STEPS = ['Connect systems','Generate plan','Execute safely','Repair failures','Approve output']
export default function UseCases() {
  return (
    <section style={{ position:'relative', zIndex:10, maxWidth:1280, margin:'0 auto', padding:'30px 40px 60px', textAlign:'center' }}>
      <div style={{ display:'inline-flex', alignItems:'center', gap:10, fontFamily:"'JetBrains Mono',monospace", fontSize:11, letterSpacing:'.32em', color:'#8b7bff', marginBottom:22 }}>
        <span style={{ width:24, height:1, background:'#8b7bff', display:'inline-block' }} />BUILT FOR REAL OPERATIONS<span style={{ width:24, height:1, background:'#8b7bff', display:'inline-block' }} />
      </div>
      <h2 style={{ margin:'0 0 44px', fontSize:48, lineHeight:1.05, fontWeight:700, letterSpacing:'-.025em' }}>
        Migrations too complex<br/>
        <span style={{ background:'linear-gradient(100deg,#8b7bff,#2fe6d6)', WebkitBackgroundClip:'text', backgroundClip:'text', color:'transparent' }}>to map by hand.</span>
      </h2>
      <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:16, textAlign:'left' }}>
        {CASES.map(c => (
          <div key={c.title} style={{ border:'1px solid rgba(255,255,255,.08)', borderRadius:14, padding:24, background:'rgba(255,255,255,.015)' }}>
            <div style={{ width:40, height:40, borderRadius:10, background:'rgba(139,123,255,.12)', border:'1px solid rgba(139,123,255,.3)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:18, marginBottom:18 }}>{c.icon}</div>
            <div style={{ fontWeight:600, fontSize:16, marginBottom:8 }}>{c.title}</div>
            <p style={{ margin:'0 0 16px', fontSize:13, lineHeight:1.5, color:'#9aa3b8' }}>{c.body}</p>
            <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:11.5, color:'#8b7bff' }}>Explore use case →</div>
          </div>
        ))}
      </div>
      {/* workflow rail */}
      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', gap:8, marginTop:16, border:'1px solid rgba(139,123,255,.18)', borderRadius:14, padding:'22px 26px', background:'linear-gradient(100deg,rgba(139,123,255,.05),rgba(47,230,214,.03))', fontFamily:"'JetBrains Mono',monospace" }}>
        {STEPS.map((s,i) => (
          <React.Fragment key={s}>
            <div style={{ textAlign:'left' }}>
              <div style={{ fontSize:11, color: i===4?'#2fe6d6':'#8b7bff' }}>0{i+1}</div>
              <div style={{ fontSize:13, color:'#e9edf6', marginTop:3 }}>{s}</div>
            </div>
            {i < 4 && <span style={{ color:'#5a6178' }}>→</span>}
          </React.Fragment>
        ))}
      </div>
    </section>
  )
}
