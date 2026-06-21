import React from 'react'

export default function CTA() {
  return (
    <section id="demo" style={{ position:'relative', zIndex:10, maxWidth:1280, margin:'0 auto', padding:'40px 40px 110px' }}>
      <div style={{ position:'relative', border:'1px solid rgba(139,123,255,.3)', borderRadius:20, padding:'72px 48px 64px', background:'linear-gradient(140deg,rgba(139,123,255,.14),rgba(47,230,214,.05))', overflow:'hidden', textAlign:'center' }}>
        {/* Grid overlay */}
        <div style={{ position:'absolute', inset:0, pointerEvents:'none', backgroundImage:'linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px)', backgroundSize:'40px 40px', maskImage:'radial-gradient(ellipse 80% 100% at 50% 50%,#000,transparent)', WebkitMaskImage:'radial-gradient(ellipse 80% 100% at 50% 50%,#000,transparent)' }} />

        <div style={{ position:'relative' }}>
          <div style={{ display:'inline-flex', alignItems:'center', gap:10, fontFamily:"'JetBrains Mono',monospace", fontSize:11, letterSpacing:'.32em', color:'#2fe6d6', marginBottom:22 }}>
            <span style={{ width:24, height:1, background:'#2fe6d6', display:'inline-block' }} />
            EARLY ACCESS
            <span style={{ width:24, height:1, background:'#2fe6d6', display:'inline-block' }} />
          </div>

          <h2 style={{ margin:'0 auto 18px', fontSize:'clamp(34px,4vw,52px)', lineHeight:1.08, fontWeight:700, letterSpacing:'-.025em', maxWidth:800 }}>
            Your next migration shouldn't take<br/>
            <span style={{ background:'linear-gradient(100deg,#8b7bff,#2fe6d6)', WebkitBackgroundClip:'text', backgroundClip:'text', color:'transparent' }}>six months of manual mapping.</span>
          </h2>

          <p style={{ margin:'0 auto 40px', maxWidth:560, fontSize:16, lineHeight:1.6, color:'#7a839a' }}>
            We're working with a small number of design partners to run live migrations and benchmark results on real enterprise schemas. If you're planning a migration in 2026, let's talk.
          </p>

          <div style={{ display:'flex', gap:14, justifyContent:'center', flexWrap:'wrap' }}>
            <a href="mailto:hello@rebar.ai" style={{ display:'inline-flex', alignItems:'center', gap:9, padding:'16px 32px', borderRadius:8, background:'linear-gradient(100deg,#8b7bff,#6d5cf0)', color:'#fff', fontWeight:600, fontSize:15, cursor:'pointer', boxShadow:'0 0 40px rgba(139,123,255,.45)', fontFamily:"'Space Grotesk',sans-serif", textDecoration:'none', whiteSpace:'nowrap' }}>
              Request a demo →
            </a>
            <a href="mailto:hello@rebar.ai" style={{ display:'inline-flex', alignItems:'center', gap:9, padding:'16px 32px', borderRadius:8, border:'1px solid rgba(255,255,255,.16)', background:'rgba(255,255,255,.03)', color:'#cfd5e4', fontWeight:500, fontSize:15, cursor:'pointer', fontFamily:"'Space Grotesk',sans-serif", textDecoration:'none', whiteSpace:'nowrap' }}>
              Contact us
            </a>
          </div>

          <div style={{ display:'flex', justifyContent:'center', gap:36, marginTop:44, fontFamily:"'JetBrains Mono',monospace", fontSize:11, letterSpacing:'.06em', color:'#5a6478' }}>
            <span>◇ No migration too large</span>
            <span>◇ Verifiable output</span>
            <span>◇ Enterprise-ready</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginTop:40, fontFamily:"'JetBrains Mono',monospace", fontSize:11.5, color:'#5a6178' }}>
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <div style={{ display:'flex', gap:3, alignItems:'flex-end', height:14 }}>
            <div style={{ width:2.5, height:6,  background:'#8b7bff' }} />
            <div style={{ width:2.5, height:12, background:'#8b7bff' }} />
            <div style={{ width:2.5, height:9,  background:'#2fe6d6' }} />
          </div>
          <span style={{ fontWeight:600, letterSpacing:'.2em', color:'#9aa3b8' }}>REBAR</span>
          <span>// autonomous data migration</span>
        </div>
        <div style={{ display:'flex', gap:24 }}>
          {['Benchmarks','Training','The Future'].map(l => <span key={l}>{l}</span>)}
        </div>
      </div>
    </section>
  )
}
