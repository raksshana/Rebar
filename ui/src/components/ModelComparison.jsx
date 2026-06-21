import React from 'react'
export default function ModelComparison() {
  return (
    <section style={{ position:'relative', zIndex:10, maxWidth:1280, margin:'0 auto', padding:'30px 40px 80px' }}>
      <div style={{ display:'inline-flex', alignItems:'center', gap:10, fontFamily:"'JetBrains Mono',monospace", fontSize:11, letterSpacing:'.32em', color:'#8b7bff', marginBottom:22 }}>
        <span style={{ width:24, height:1, background:'#8b7bff', display:'inline-block' }} />UNEXPECTED FINDING
      </div>
      <h2 style={{ margin:'0 0 44px', fontSize:52, lineHeight:1.02, fontWeight:700, letterSpacing:'-.025em', maxWidth:880 }}>
        The largest model was not the <span style={{ background:'linear-gradient(100deg,#8b7bff,#2fe6d6)', WebkitBackgroundClip:'text', backgroundClip:'text', color:'transparent' }}>strongest migration agent.</span>
      </h2>
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:16 }}>
        {/* What happened */}
        <div style={{ border:'1px solid rgba(255,255,255,.08)', borderRadius:14, padding:22, background:'rgba(255,255,255,.015)' }}>
          <Tag>WHAT HAPPENED</Tag>
          <ScoreRow label="Claude Sonnet 4.6" value="79.3" color="#2fe6d6" />
          <ScoreRow label="Claude Opus 4.8"   value="53.2" color="#ff6b8a" />
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'baseline', paddingTop:18 }}>
            <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:'#717a90' }}>Performance gap</span>
            <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:26, fontWeight:700, color:'#ff6b8a' }}>−26.1</span>
          </div>
        </div>
        {/* Where it failed */}
        <div style={{ border:'1px solid rgba(255,255,255,.08)', borderRadius:14, padding:22, background:'rgba(255,255,255,.015)' }}>
          <Tag>WHERE IT FAILED</Tag>
          {[['Incorrect tool sequence','34%','#ff6b8a',34],['Incomplete migration','27%','#ff8a6b',27],['Invalid output structure','19%','#ffb86b',19],['Unnecessary changes','12%','#ffd16b',12]].map(([l,v,c,w]) => (
            <FailRow key={l} label={l} value={v} color={c} width={w} />
          ))}
        </div>
        {/* Hypothesis */}
        <div style={{ border:'1px solid rgba(139,123,255,.25)', borderRadius:14, padding:22, background:'linear-gradient(160deg,rgba(139,123,255,.08),rgba(139,123,255,.01))' }}>
          <Tag>CURRENT HYPOTHESIS</Tag>
          <p style={{ margin:'0 0 18px', fontSize:15, lineHeight:1.55, color:'#cfd5e4' }}>Opus optimizes for elaborate interpretation, while the grader rewards precise execution and strict adherence.</p>
          <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:10, color:'#5a6178' }}>— pending trace-level validation</div>
        </div>
      </div>
      {/* Execution paths */}
      <div style={{ display:'grid', gridTemplateColumns:'.8fr 1fr 1fr', gap:16, marginTop:16, alignItems:'center' }}>
        <div>
          <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:10, letterSpacing:'.16em', color:'#5a6178', marginBottom:10 }}>SAME GENERATED TASK</div>
          <div style={{ fontSize:20, fontWeight:600, lineHeight:1.2 }}>One task. Two execution paths.</div>
        </div>
        <PathCard model="Claude Sonnet 4.6" score="91" good items={['Mapped 47 / 47 fields','Executed the full migration','Repaired 3 relationships','Completed final validation']} />
        <PathCard model="Claude Opus 4.8"   score="48" items={['Proposed 52 mappings','Changed destination assumptions','Consumed tool budget early','Did not complete validation']} good={false} />
      </div>
    </section>
  )
}
function Tag({ children }) {
  return <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:10, letterSpacing:'.16em', color:'#8b7bff', marginBottom:20 }}>{children}</div>
}
function ScoreRow({ label, value, color }) {
  return (
    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'baseline', paddingBottom:14, borderBottom:'1px solid rgba(255,255,255,.06)', marginBottom:14 }}>
      <span style={{ fontSize:14 }}>{label}</span>
      <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:22, fontWeight:700, color }}>{value}</span>
    </div>
  )
}
function FailRow({ label, value, color, width }) {
  return (
    <div style={{ marginBottom:16 }}>
      <div style={{ display:'flex', justifyContent:'space-between', fontSize:12.5, color:'#cfd5e4', marginBottom:7 }}>
        <span>{label}</span><span style={{ fontFamily:"'JetBrains Mono',monospace", color }}>{value}</span>
      </div>
      <div style={{ height:5, borderRadius:99, background:'rgba(255,255,255,.06)' }}>
        <div style={{ height:'100%', width:width+'%', borderRadius:99, background:color }} />
      </div>
    </div>
  )
}
function PathCard({ model, score, items, good }) {
  const goodItems = good ? items : [items[0]]
  const badItems  = good ? [] : items.slice(1)
  return (
    <div style={{ border:`1px solid ${good?'rgba(47,230,214,.2)':'rgba(255,107,138,.2)'}`, borderRadius:14, padding:20, background:good?'rgba(47,230,214,.025)':'rgba(255,107,138,.025)' }}>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16 }}>
        <span style={{ fontWeight:600, fontSize:14 }}>{model}</span>
        <span style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:good?'#2fe6d6':'#ff6b8a' }}>SCORE {score}</span>
      </div>
      <div style={{ display:'flex', flexDirection:'column', gap:11, fontSize:12.5, color:'#cfd5e4' }}>
        {goodItems.map(t => <div key={t}><span style={{ color:'#2fe6d6' }}>✓</span> {t}</div>)}
        {badItems.map(t  => <div key={t}><span style={{ color:'#ff6b8a' }}>✕</span> {t}</div>)}
      </div>
    </div>
  )
}
