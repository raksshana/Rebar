import React, { useState, useRef, useCallback } from 'react'

const IDLE  = { phase:'idle',    fields:0, records:0, issues:0, relations:0, progress:0 }
const DONE  = { phase:'done',    fields:142, records:24000, issues:31, relations:12, progress:1 }

function ease(t) { return 1 - Math.pow(1 - t, 3) }

export default function MigrationEngine() {
  const [s, setS] = useState(IDLE)
  const raf = useRef(null)

  const run = useCallback(() => {
    if (s.phase === 'running') return
    if (raf.current) cancelAnimationFrame(raf.current)
    setS({ ...IDLE, phase:'running' })
    const dur = 2600, t0 = performance.now()
    const tick = (now) => {
      const p = Math.min(1, (now - t0) / dur), e = ease(p)
      setS({ phase:'running', progress:p, fields:Math.round(e*142), records:Math.round(e*24000), issues:Math.round(e*31), relations:Math.round(e*12) })
      if (p < 1) raf.current = requestAnimationFrame(tick)
      else setS(DONE)
    }
    raf.current = requestAnimationFrame(tick)
  }, [s.phase])

  const reset = useCallback(() => {
    if (raf.current) cancelAnimationFrame(raf.current)
    setS(IDLE)
  }, [])

  const done    = s.phase === 'done'
  const running = s.phase === 'running'
  const pct     = Math.round(s.progress * 100)

  const stepStyle = (active) => ({
    flex:1, textAlign:'center', padding:8, borderRadius:7,
    fontFamily:"'JetBrains Mono',monospace", fontSize:10.5,
    background: active ? 'rgba(139,123,255,.18)' : 'rgba(255,255,255,.03)',
    border:     active ? '1px solid rgba(139,123,255,.5)' : '1px solid rgba(255,255,255,.07)',
    color:      active ? '#cdb9ff' : '#5a6178'
  })

  let statusLabel='Ready to run', statusColor='#8b7bff'
  if (running) { statusLabel='Migrating…'; statusColor='#2fe6d6' }
  if (done)    { statusLabel='Verified ✓'; statusColor='#2fe6d6' }

  let centerKicker='READY', centerTitle='Waiting to begin', centerSub='The agent works even when schemas are generated at random.'
  if (running) { centerKicker='IN PROGRESS'; centerTitle=pct+'%'; centerSub='Understanding, transforming, repairing and verifying records.' }
  if (done)    { centerKicker='COMPLETE';    centerTitle='99.6%'; centerSub='Every record migrated, validated and proven correct.' }

  return (
    <section style={{ position:'relative', zIndex:10, maxWidth:1280, margin:'0 auto', padding:'50px 40px 80px' }}>
      <div style={{ border:'1px solid rgba(139,123,255,.18)', borderRadius:18, background:'linear-gradient(170deg,rgba(16,18,32,.7),rgba(8,10,18,.7))', overflow:'hidden', boxShadow:'0 24px 70px rgba(0,0,0,.4)' }}>
        {/* header */}
        <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'18px 24px', borderBottom:'1px solid rgba(255,255,255,.06)' }}>
          <div style={{ display:'flex', alignItems:'center', gap:11 }}>
            <div style={{ display:'flex', gap:3, alignItems:'flex-end', height:15 }}>
              <div style={{ width:3, height:7,  background:'#8b7bff' }} />
              <div style={{ width:3, height:14, background:'#8b7bff' }} />
              <div style={{ width:3, height:10, background:'#2fe6d6' }} />
            </div>
            <span style={{ fontWeight:600, fontSize:14 }}>Rebar Migration Engine</span>
          </div>
          <div style={{ display:'flex', alignItems:'center', gap:8, fontFamily:"'JetBrains Mono',monospace", fontSize:11.5, color:statusColor }}>
            <span style={{ width:7, height:7, borderRadius:'50%', background:statusColor, display:'inline-block', animation:'pulseDot 1.4s infinite' }} />
            {statusLabel}
          </div>
          <div style={{ display:'flex', gap:10 }}>
            <button onClick={reset} style={{ padding:'9px 15px', border:'1px solid rgba(255,255,255,.14)', borderRadius:7, fontFamily:"'JetBrains Mono',monospace", fontSize:12, color:'#cfd5e4', background:'transparent', cursor:'pointer' }}>Generate scenario</button>
            <button onClick={run}   style={{ display:'flex', alignItems:'center', gap:8, padding:'9px 17px', borderRadius:7, border:'none', background:'linear-gradient(100deg,#8b7bff,#6d5cf0)', fontFamily:"'JetBrains Mono',monospace", fontSize:12, fontWeight:500, color:'#fff', cursor:'pointer', boxShadow:'0 0 24px rgba(139,123,255,.35)' }}>Run migration →</button>
          </div>
        </div>
        <div style={{ padding:'28px 24px' }}>
          <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:10, letterSpacing:'.2em', color:'#5a6178', marginBottom:8 }}>GENERATED SCENARIO</div>
          <div style={{ fontSize:21, fontWeight:600, marginBottom:24 }}>Legacy CRM <span style={{ color:'#8b7bff' }}>→</span> Modern Customer Platform</div>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1.15fr 1fr', gap:16 }}>
            {/* BEFORE */}
            <div style={{ border:'1px solid rgba(255,255,255,.07)', borderRadius:12, padding:18, background:'rgba(255,255,255,.015)' }}>
              <Mono style={{ marginBottom:6 }}>BEFORE</Mono>
              <div style={{ fontWeight:600, fontSize:15 }}>Legacy CRM</div>
              <div style={{ fontSize:11, color:'#717a90', margin:'3px 0 16px' }}>Complex source data</div>
              <EngineRow label="tables"  value="18" />
              <EngineRow label="fields"  value="142" />
              <EngineRow label="records" value="24,000" />
              <EngineRow label="data issues" value="31" valueColor="#ff6b8a" last />
            </div>
            {/* MIDDLE */}
            <div style={{ border:'1px solid rgba(139,123,255,.2)', borderRadius:12, padding:18, background:'rgba(139,123,255,.04)', display:'flex', flexDirection:'column' }}>
              <div style={{ display:'flex', gap:8, marginBottom:20 }}>
                <div style={stepStyle(s.progress>0.02)}>1 Understand</div>
                <div style={stepStyle(s.progress>0.4)}>2 Transform</div>
                <div style={stepStyle(s.progress>0.85||done)}>3 Verify</div>
              </div>
              <div style={{ flex:1, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', textAlign:'center' }}>
                <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:10, letterSpacing:'.2em', color:'#8b7bff', marginBottom:8 }}>{centerKicker}</div>
                <div style={{ fontSize:24, fontWeight:700, marginBottom:8 }}>{centerTitle}</div>
                <div style={{ fontSize:12, color:'#717a90', maxWidth:240, lineHeight:1.5 }}>{centerSub}</div>
                <div style={{ width:'100%', height:5, borderRadius:99, background:'rgba(255,255,255,.06)', marginTop:18, overflow:'hidden' }}>
                  <div style={{ height:'100%', width:pct+'%', borderRadius:99, background:'linear-gradient(90deg,#8b7bff,#2fe6d6)', boxShadow:'0 0 12px rgba(47,230,214,.5)', transition:'width .2s' }} />
                </div>
              </div>
            </div>
            {/* AFTER */}
            <div style={{ border:'1px solid rgba(47,230,214,.18)', borderRadius:12, padding:18, background:'rgba(47,230,214,.025)' }}>
              <Mono style={{ marginBottom:6 }}>AFTER</Mono>
              <div style={{ fontWeight:600, fontSize:15 }}>Modern Customer Platform</div>
              <div style={{ fontSize:11, color:'#717a90', margin:'3px 0 16px' }}>Clean, verified destination</div>
              <EngineRow label="mapped fields"    value={s.fields} valueColor="#2fe6d6" />
              <EngineRow label="records migrated" value={s.records.toLocaleString()} valueColor="#2fe6d6" />
              <EngineRow label="relationships"    value={running||done ? s.relations : '—'} valueColor="#2fe6d6" />
              <EngineRow label="unresolved"       value={done ? 0 : '—'} valueColor="#2fe6d6" last />
            </div>
          </div>
          {/* metric tiles */}
          <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:14, marginTop:18 }}>
            <MetricTile label="Fields mapped"     value={`${s.fields} / 142`} />
            <MetricTile label="Records migrated"  value={s.records.toLocaleString()} />
            <MetricTile label="Issues repaired"   value={running||done ? s.issues : 0} />
            <MetricTile label="Validation score"  value={done ? '99.6' : '—'} accent />
          </div>
        </div>
      </div>
    </section>
  )
}

function Mono({ children, style }) {
  return <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:9, letterSpacing:'.18em', color:'#5a6178', ...style }}>{children}</div>
}
function EngineRow({ label, value, valueColor, last }) {
  return (
    <div style={{ display:'flex', justifyContent:'space-between', paddingBottom:last?0:9, marginBottom:last?0:10, borderBottom:last?'none':'1px solid rgba(255,255,255,.05)', fontFamily:"'JetBrains Mono',monospace", fontSize:12 }}>
      <span style={{ color:'#9aa3b8' }}>{label}</span>
      <span style={{ color: valueColor || '#e9edf6' }}>{value}</span>
    </div>
  )
}
function MetricTile({ label, value, accent }) {
  return (
    <div style={{ border:`1px solid ${accent ? 'rgba(47,230,214,.22)' : 'rgba(255,255,255,.07)'}`, borderRadius:11, padding:16, background: accent ? 'rgba(47,230,214,.03)' : 'rgba(255,255,255,.015)' }}>
      <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:10, letterSpacing:'.1em', color:'#717a90', marginBottom:9 }}>{label}</div>
      <div style={{ fontSize:24, fontWeight:700, fontFamily:"'JetBrains Mono',monospace", color: accent ? '#2fe6d6' : '#e9edf6' }}>{value}</div>
    </div>
  )
}
