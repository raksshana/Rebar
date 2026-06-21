import React from 'react'

export default function Hero() {
  return (
    <section style={{
      position:'relative', zIndex:10,
      display:'grid', gridTemplateColumns:'1fr 1fr', gap:56,
      alignItems:'center', maxWidth:1280, margin:'0 auto',
      padding:'96px 40px 70px'
    }}>
      {/* Left copy */}
      <div>
        <div style={{ display:'inline-flex', alignItems:'center', gap:10, fontFamily:"'JetBrains Mono',monospace", fontSize:11, letterSpacing:'.32em', color:'#8b7bff', marginBottom:30 }}>
          <span style={{ width:24, height:1, background:'#8b7bff', display:'inline-block' }} />
          AUTONOMOUS DATA MIGRATION
        </div>
        <h1 style={{ margin:0, fontSize:74, lineHeight:.96, fontWeight:700, letterSpacing:'-.03em', textShadow:'0 0 30px rgba(139,123,255,.18)' }}>
          Migrate any<br/>schema.<br/>
          <span style={{ background:'linear-gradient(100deg,#8b7bff,#2fe6d6)', WebkitBackgroundClip:'text', backgroundClip:'text', color:'transparent' }}>
            Verify every record.
          </span>
        </h1>
        <p style={{ margin:'30px 0 0', maxWidth:430, fontSize:17, lineHeight:1.55, color:'#9aa3b8' }}>
          AI agents understand, transform, repair, and verify — no hand-written mappings.
        </p>
        <div style={{ display:'flex', gap:14, marginTop:40 }}>
          <button style={{ display:'flex', alignItems:'center', gap:9, padding:'14px 24px', borderRadius:8, border:'none', background:'linear-gradient(100deg,#8b7bff,#6d5cf0)', color:'#fff', fontWeight:600, fontSize:14.5, cursor:'pointer', boxShadow:'0 0 34px rgba(139,123,255,.4)', fontFamily:"'Space Grotesk',sans-serif" }}>
            Run a live migration →
          </button>
          <button style={{ display:'flex', alignItems:'center', gap:9, padding:'14px 24px', borderRadius:8, border:'1px solid rgba(255,255,255,.14)', background:'rgba(255,255,255,.03)', color:'#cfd5e4', fontWeight:500, fontSize:14.5, cursor:'pointer', fontFamily:"'Space Grotesk',sans-serif" }}>
            View benchmark results
          </button>
        </div>
        <div style={{ display:'flex', gap:26, marginTop:34, fontFamily:"'JetBrains Mono',monospace", fontSize:11.5, letterSpacing:'.05em', color:'#717a90' }}>
          <span>◇ Random schemas</span><span>◇ Deterministic grading</span><span>◇ RL-trained model</span>
        </div>
      </div>

      {/* Right HUD panel */}
      <div style={{ position:'relative', animation:'floatY 8s ease-in-out infinite' }}>
        {/* corner brackets */}
        {[{top:-7,left:-7,borderLeft:'2px solid #8b7bff',borderTop:'2px solid #8b7bff'},{top:-7,right:-7,borderRight:'2px solid #8b7bff',borderTop:'2px solid #8b7bff'},{bottom:-7,left:-7,borderLeft:'2px solid #2fe6d6',borderBottom:'2px solid #2fe6d6'},{bottom:-7,right:-7,borderRight:'2px solid #2fe6d6',borderBottom:'2px solid #2fe6d6'}].map((s,i) => (
          <div key={i} style={{ position:'absolute', width:22, height:22, zIndex:5, ...s }} />
        ))}
        <div style={{ position:'relative', border:'1px solid rgba(139,123,255,.22)', borderRadius:16, background:'linear-gradient(160deg,rgba(20,22,38,.92),rgba(10,12,22,.92))', overflow:'hidden', boxShadow:'0 30px 80px rgba(0,0,0,.55),0 0 0 1px rgba(255,255,255,.02) inset' }}>
          {/* scan line */}
          <div style={{ position:'absolute', inset:0, pointerEvents:'none', background:'linear-gradient(rgba(139,123,255,.06),transparent 40%)', height:46, animation:'scan 4.5s linear infinite' }} />
          {/* title bar */}
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'13px 18px', borderBottom:'1px solid rgba(255,255,255,.06)', fontFamily:"'JetBrains Mono',monospace" }}>
            <div style={{ display:'flex', gap:6 }}>
              {[0,1,2].map(i => <span key={i} style={{ width:9, height:9, borderRadius:'50%', background:'#2a2f44', display:'inline-block' }} />)}
            </div>
            <span style={{ fontSize:11, color:'#5a6178' }}>app.rebar.ai / migration-4821</span>
            <span style={{ display:'flex', alignItems:'center', gap:6, fontSize:11, color:'#2fe6d6' }}>
              <span style={{ width:6, height:6, borderRadius:'50%', background:'#2fe6d6', display:'inline-block', animation:'pulseDot 1.4s infinite' }} />
              LIVE
            </span>
          </div>
          <div style={{ padding:'20px 18px' }}>
            <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:10, letterSpacing:'.2em', color:'#5a6178', marginBottom:6 }}>AUTONOMOUS MIGRATION</div>
            <div style={{ fontSize:17, fontWeight:600, marginBottom:18 }}>Legacy CRM <span style={{ color:'#8b7bff' }}>→</span> Customer Platform</div>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:11 }}>
              <PanelBefore />
              <PanelMiddle />
              <PanelAfter />
            </div>
            <div style={{ marginTop:16, border:'1px solid rgba(255,255,255,.07)', borderRadius:10, padding:'13px 14px', background:'rgba(255,255,255,.015)' }}>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', fontFamily:"'JetBrains Mono',monospace", fontSize:10, color:'#5a6178', marginBottom:9 }}>
                <span style={{ letterSpacing:'.14em' }}>AUTOMATIC REPAIR · 31 ISSUES RESOLVED</span>
                <span style={{ fontSize:14, color:'#2fe6d6', fontWeight:600 }}>99.6%</span>
              </div>
              <div style={{ height:6, borderRadius:99, background:'rgba(255,255,255,.06)', overflow:'hidden' }}>
                <div style={{ height:'100%', width:'99.6%', borderRadius:99, background:'linear-gradient(90deg,#8b7bff,#2fe6d6)', boxShadow:'0 0 14px rgba(47,230,214,.6)' }} />
              </div>
            </div>
          </div>
        </div>
        {/* floating chip */}
        <div style={{ position:'absolute', top:64, right:-18, display:'flex', alignItems:'center', gap:9, padding:'10px 14px', borderRadius:9, background:'rgba(14,16,28,.95)', border:'1px solid rgba(47,230,214,.3)', boxShadow:'0 14px 34px rgba(0,0,0,.5)' }}>
          <span style={{ width:7, height:7, borderRadius:'50%', background:'#2fe6d6', boxShadow:'0 0 10px #2fe6d6', display:'inline-block' }} />
          <div style={{ fontFamily:"'JetBrains Mono',monospace" }}>
            <div style={{ fontSize:8.5, letterSpacing:'.14em', color:'#5a6178' }}>VALIDATION</div>
            <div style={{ fontSize:11.5, color:'#e9edf6' }}>0 unresolved issues</div>
          </div>
        </div>
      </div>
    </section>
  )
}

function Row({ label, value, valueColor }) {
  return (
    <div style={{ display:'flex', justifyContent:'space-between', fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:'#9aa3b8', marginBottom:8 }}>
      <span>{label}</span><span style={{ color: valueColor || '#e9edf6' }}>{value}</span>
    </div>
  )
}
function PanelBefore() {
  return (
    <div style={{ border:'1px solid rgba(255,255,255,.07)', borderRadius:10, padding:13, background:'rgba(255,255,255,.015)' }}>
      <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:9, letterSpacing:'.16em', color:'#5a6178', marginBottom:8 }}>BEFORE</div>
      <div style={{ fontWeight:600, fontSize:13, marginBottom:12 }}>Legacy CRM</div>
      <Row label="tables"  value="18" />
      <Row label="fields"  value="142" />
      <Row label="records" value="24k" />
      <Row label="issues"  value="31" valueColor="#ff6b8a" />
    </div>
  )
}
function PanelMiddle() {
  return (
    <div style={{ border:'1px solid rgba(139,123,255,.3)', borderRadius:10, padding:13, background:'rgba(139,123,255,.06)', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', textAlign:'center' }}>
      <div style={{ width:38, height:38, borderRadius:10, background:'linear-gradient(135deg,#8b7bff,#6d5cf0)', display:'flex', alignItems:'center', justifyContent:'center', marginBottom:10, boxShadow:'0 0 22px rgba(139,123,255,.5)', fontSize:16 }}>✦</div>
      <div style={{ fontWeight:600, fontSize:12.5 }}>AI migration</div>
      <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:9.5, color:'#717a90', marginTop:4 }}>everything mapped</div>
      <div style={{ marginTop:10, fontFamily:"'JetBrains Mono',monospace", fontSize:9, color:'#8b7bff', background:'rgba(139,123,255,.12)', padding:'4px 7px', borderRadius:5 }}>email → customer_id</div>
    </div>
  )
}
function PanelAfter() {
  return (
    <div style={{ border:'1px solid rgba(47,230,214,.22)', borderRadius:10, padding:13, background:'rgba(47,230,214,.03)' }}>
      <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:9, letterSpacing:'.16em', color:'#5a6178', marginBottom:8 }}>AFTER</div>
      <div style={{ fontWeight:600, fontSize:13, marginBottom:12 }}>Customer Platform</div>
      <Row label="mapped"   value="142" valueColor="#2fe6d6" />
      <Row label="migrated" value="24k" valueColor="#2fe6d6" />
      <Row label="relations" value="12" valueColor="#2fe6d6" />
      <Row label="unresolved" value="0" valueColor="#2fe6d6" />
    </div>
  )
}
