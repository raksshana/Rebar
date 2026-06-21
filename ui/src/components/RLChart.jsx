import React from 'react'
const READOUTS = [
  { label:'SCORE IMPROVEMENT', value:'+23.3', sub:'held-out benchmark points', accent:true },
  { label:'FINAL SCORE',       value:'84.7',  sub:'selected checkpoint' },
  { label:'TRAINING TASKS',    value:'400',   sub:'generated migrations' },
  { label:'BEST CHECKPOINT',   value:'380',   sub:'held-out result' },
]
export default function RLChart() {
  return (
    <section id="training" style={{ position:'relative', zIndex:10, maxWidth:1280, margin:'0 auto', padding:'30px 40px 80px' }}>
      <div style={{ textAlign:'center', marginBottom:48 }}>
        <div style={{ display:'inline-flex', alignItems:'center', gap:10, fontFamily:"'JetBrains Mono',monospace", fontSize:11, letterSpacing:'.32em', color:'#8b7bff', marginBottom:22 }}>
          <span style={{ width:24, height:1, background:'#8b7bff', display:'inline-block' }} />REINFORCEMENT LEARNING<span style={{ width:24, height:1, background:'#8b7bff', display:'inline-block' }} />
        </div>
        <h2 style={{ margin:0, fontSize:48, lineHeight:1.05, fontWeight:700, letterSpacing:'-.025em' }}>
          <span style={{ background:'linear-gradient(100deg,#8b7bff,#2fe6d6)', WebkitBackgroundClip:'text', backgroundClip:'text', color:'transparent' }}>Training curve.</span>
        </h2>
      </div>
      <div style={{ display:'grid', gridTemplateColumns:'1.55fr 1fr', gap:18, alignItems:'stretch' }}>
        {/* Chart */}
        <div style={{ border:'1px solid rgba(255,255,255,.08)', borderRadius:16, padding:24, background:'linear-gradient(170deg,rgba(16,18,32,.6),rgba(8,10,18,.6))' }}>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:6 }}>
            <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:10, letterSpacing:'.16em', color:'#5a6178' }}>HELD-OUT MIGRATION SCORE</div>
            <div style={{ display:'flex', alignItems:'center', gap:7, fontFamily:"'JetBrains Mono',monospace", fontSize:10.5, color:'#9aa3b8' }}>
              <span style={{ width:14, height:2, background:'#8b7bff', display:'inline-block' }} />Validation score
            </div>
          </div>
          <div style={{ fontWeight:600, fontSize:16, marginBottom:14 }}>Improvement across RL checkpoints</div>
          <svg viewBox="0 0 800 320" style={{ width:'100%', height:'auto', display:'block', fontFamily:"'JetBrains Mono',monospace" }}>
            <defs>
              <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#8b7bff" stopOpacity="0.28"/><stop offset="100%" stopColor="#8b7bff" stopOpacity="0"/></linearGradient>
              <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stopColor="#8b7bff"/><stop offset="100%" stopColor="#2fe6d6"/></linearGradient>
            </defs>
            <line x1="60" y1="42.88" x2="760" y2="42.88" stroke="rgba(255,255,255,.05)"/>
            <line x1="60" y1="166"   x2="760" y2="166"   stroke="rgba(255,255,255,.05)"/>
            <line x1="60" y1="280"   x2="760" y2="280"   stroke="rgba(255,255,255,.08)"/>
            <line x1="60" y1="94.72" x2="760" y2="94.72" stroke="rgba(255,255,255,.22)" strokeDasharray="4 5"/>
            <text x="755" y="89"  textAnchor="end" fill="#6b7488" fontSize="11">Claude Sonnet 4.6 · 79.3</text>
            <line x1="60" y1="118.72" x2="760" y2="118.72" stroke="rgba(255,255,255,.15)" strokeDasharray="4 5"/>
            <text x="755" y="113" textAnchor="end" fill="#5a6178" fontSize="11">GPT-5.4 · 76.8</text>
            <text x="48" y="46"  textAnchor="end" fill="#5a6178" fontSize="11">85</text>
            <text x="48" y="170" textAnchor="end" fill="#5a6178" fontSize="11">72</text>
            <text x="48" y="284" textAnchor="end" fill="#5a6178" fontSize="11">60</text>
            <path d="M80 266.6 L212 232 L344 174.4 L476 126.4 L608 88 L740 42.88 L740 280 L80 280 Z" fill="url(#areaFill)"/>
            <path d="M80 266.6 L212 232 L344 174.4 L476 126.4 L608 88 L740 42.88" fill="none" stroke="url(#lineGrad)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="900" strokeDashoffset="900" style={{ animation:'drawLine 1.8s ease-out forwards', filter:'drop-shadow(0 0 6px rgba(139,123,255,.5))' }}/>
            {[[80,266.6],[212,232],[344,174.4],[476,126.4],[608,88]].map(([cx,cy],i) => (
              <circle key={i} cx={cx} cy={cy} r="5" fill="#06080f" stroke="#8b7bff" strokeWidth="2.5"/>
            ))}
            <circle cx="740" cy="42.88" r="6" fill="#2fe6d6" stroke="#2fe6d6" strokeWidth="2" style={{ filter:'drop-shadow(0 0 8px #2fe6d6)' }}/>
            <g><rect x="58"  y="244" width="44" height="20" rx="4" fill="#0e1020" stroke="rgba(255,255,255,.1)"/><text x="80"  y="258" textAnchor="middle" fill="#e9edf6" fontSize="11" fontWeight="600">61.4</text></g>
            <g><rect x="716" y="20"  width="48" height="20" rx="4" fill="#0e1020" stroke="rgba(47,230,214,.4)"/><text x="740" y="34"  textAnchor="middle" fill="#2fe6d6" fontSize="11" fontWeight="600">84.7</text></g>
            {[['Base',80],['80',212],['160',344],['240',476],['320',608],['Final',740]].map(([lbl,x]) => (
              <text key={lbl} x={x} y="302" textAnchor="middle" fill="#5a6178" fontSize="11">{lbl}</text>
            ))}
          </svg>
        </div>
        {/* Readouts */}
        <div style={{ display:'grid', gridTemplateRows:'repeat(4,1fr)', gap:14 }}>
          {READOUTS.map(r => (
            <div key={r.label} style={{ border:`1px solid ${r.accent?'rgba(139,123,255,.4)':'rgba(255,255,255,.08)'}`, borderRadius:14, padding:'18px 20px', background: r.accent?'linear-gradient(150deg,rgba(139,123,255,.14),rgba(139,123,255,.02))':'rgba(255,255,255,.015)', boxShadow:r.accent?'0 0 30px rgba(139,123,255,.12)':'none' }}>
              <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:10, letterSpacing:'.14em', color: r.accent?'#8b7bff':'#717a90', marginBottom:6 }}>{r.label}</div>
              <div style={{ fontSize: r.accent?34:30, fontWeight:700, fontFamily:"'JetBrains Mono',monospace", color: r.accent?'#e9edf6':'#2fe6d6' }}>{r.value}</div>
              {r.sub && <div style={{ fontSize:11, color:'#717a90', marginTop:2 }}>{r.sub}</div>}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
