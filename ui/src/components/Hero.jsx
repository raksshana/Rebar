import React from 'react'

export default function Hero() {
  return (
    <section style={{
      position:'relative', zIndex:10,
      maxWidth:1280, margin:'0 auto',
      padding:'96px 40px 70px'
    }}>
      <div>
        <div style={{ display:'inline-flex', alignItems:'center', gap:10, fontFamily:"'JetBrains Mono',monospace", fontSize:11, letterSpacing:'.32em', color:'#8b7bff', marginBottom:30 }}>
          <span style={{ width:24, height:1, background:'#8b7bff', display:'inline-block' }} />
          AUTONOMOUS DATA MIGRATION
        </div>
        <h1 style={{ margin:0, fontSize:'clamp(74px, 7.8vw, 112px)', lineHeight:1.0, fontWeight:700, letterSpacing:'-.03em', textShadow:'0 0 30px rgba(139,123,255,.18)' }}>
          <span style={{ display:'block', animation:'heroFadeIn 0.7s ease 0.1s forwards', opacity:0 }}>Migrate any</span>
          <span style={{ display:'block', animation:'heroFadeIn 0.7s ease 0.25s forwards', opacity:0 }}>schema.</span>
          <span style={{ display:'block', paddingBottom:'0.15em', background:'linear-gradient(100deg,#8b7bff,#2fe6d6)', WebkitBackgroundClip:'text', backgroundClip:'text', color:'transparent', animation:'heroFadeIn 0.7s ease 0.4s forwards', opacity:0 }}>
            Verify every record.
          </span>
        </h1>
        <p style={{ margin:'10px 0 0', maxWidth:640, fontSize:17, lineHeight:1.55, color:'#9aa3b8', animation:'heroFadeIn 0.7s ease 0.55s forwards', opacity:0 }}>
          REBAR is an RL training stack for autonomous data migration. We generate verifiable schema-to-schema tasks and use them to train models on the long-horizon structural reasoning frontier LLMs still fail at.
        </p>
        <div style={{ display:'flex', gap:14, marginTop:40 }}>
          <button style={{ display:'flex', alignItems:'center', gap:9, padding:'14px 24px', borderRadius:8, border:'none', background:'linear-gradient(100deg,#8b7bff,#6d5cf0)', color:'#fff', fontWeight:600, fontSize:14.5, cursor:'pointer', boxShadow:'0 0 34px rgba(139,123,255,.4)', fontFamily:"'Space Grotesk',sans-serif" }}>
            Run a live migration →
          </button>
          <button onClick={() => document.getElementById('benchmarks')?.scrollIntoView({ behavior:'smooth' })} style={{ display:'flex', alignItems:'center', gap:9, padding:'14px 24px', borderRadius:8, border:'1px solid rgba(255,255,255,.14)', background:'rgba(255,255,255,.03)', color:'#cfd5e4', fontWeight:500, fontSize:14.5, cursor:'pointer', fontFamily:"'Space Grotesk',sans-serif" }}>
            View benchmark results
          </button>
        </div>
        <div style={{ display:'flex', gap:26, marginTop:34, fontFamily:"'JetBrains Mono',monospace", fontSize:11.5, letterSpacing:'.05em', color:'#717a90' }}>
          <span>◇ Random schemas</span><span>◇ Deterministic grading</span><span>◇ RL-trained model</span>
        </div>
      </div>
    </section>
  )
}
