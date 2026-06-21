import React from 'react'
export default function CTA() {
  return (
    <section style={{ position:'relative', zIndex:10, maxWidth:1280, margin:'0 auto', padding:'40px 40px 110px' }}>
      <div style={{ position:'relative', border:'1px solid rgba(139,123,255,.3)', borderRadius:20, padding:'64px 48px', background:'linear-gradient(140deg,rgba(139,123,255,.16),rgba(47,230,214,.06))', overflow:'hidden', textAlign:'center' }}>
        <div style={{ position:'absolute', inset:0, pointerEvents:'none', backgroundImage:'linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.04) 1px,transparent 1px)', backgroundSize:'40px 40px', maskImage:'radial-gradient(ellipse 70% 100% at 50% 50%,#000,transparent)', WebkitMaskImage:'radial-gradient(ellipse 70% 100% at 50% 50%,#000,transparent)' }} />
        <div style={{ position:'relative' }}>
          <h2 style={{ margin:'0 auto', fontSize:42, lineHeight:1.1, fontWeight:700, letterSpacing:'-.02em', maxWidth:760 }}>
            The next migration shouldn't start with months of manual mapping.
          </h2>
          <div style={{ display:'flex', gap:14, justifyContent:'center', marginTop:34 }}>
            <button style={{ display:'flex', alignItems:'center', gap:9, padding:'15px 28px', borderRadius:8, background:'#06080f', border:'1px solid rgba(255,255,255,.12)', fontWeight:600, fontSize:15, color:'#fff', cursor:'pointer', boxShadow:'0 0 34px rgba(0,0,0,.4)', fontFamily:"'Space Grotesk',sans-serif" }}>Run a live migration <span style={{ color:'#2fe6d6' }}>→</span></button>
            <button style={{ display:'flex', alignItems:'center', gap:9, padding:'15px 28px', borderRadius:8, border:'1px solid rgba(255,255,255,.18)', fontWeight:500, fontSize:15, color:'#e9edf6', background:'transparent', cursor:'pointer', fontFamily:"'Space Grotesk',sans-serif" }}>View benchmarks</button>
          </div>
        </div>
      </div>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginTop:40, fontFamily:"'JetBrains Mono',monospace", fontSize:11.5, color:'#5a6178' }}>
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <span style={{ fontWeight:600, letterSpacing:'.2em', color:'#9aa3b8' }}>REBAR</span>
          <span>// autonomous data migration</span>
        </div>
        <div style={{ display:'flex', gap:24 }}>
          {['Product','Benchmarks','Training','Research'].map(l => <span key={l}>{l}</span>)}
        </div>
      </div>
    </section>
  )
}
