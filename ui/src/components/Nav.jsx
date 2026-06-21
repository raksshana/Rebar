import React from 'react'

const LINKS = ['Product','Benchmarks','Training','Research']
const TICKER = ['● AGENT.ONLINE','SCHEMAS_DISCOVERED 18','FIELDS_MAPPED 142/142','RECORDS 24,000','VALIDATION 99.6%','ISSUES_REPAIRED 31','RL_CHECKPOINT 380','HELD_OUT_SCORE 84.7']

export default function Nav() {
  return (
    <>
      <nav style={{
        position:'sticky', top:0, zIndex:50,
        display:'flex', alignItems:'center', justifyContent:'space-between',
        padding:'18px 40px',
        borderBottom:'1px solid rgba(255,255,255,.06)',
        background:'rgba(6,8,15,.72)',
        backdropFilter:'blur(14px)', WebkitBackdropFilter:'blur(14px)'
      }}>
        <div style={{ display:'flex', alignItems:'center', gap:11 }}>
          <div style={{ display:'flex', gap:3, alignItems:'flex-end', height:18 }}>
            <div style={{ width:3, height:8,  background:'#8b7bff' }} />
            <div style={{ width:3, height:16, background:'#8b7bff' }} />
            <div style={{ width:3, height:12, background:'#2fe6d6' }} />
          </div>
          <span style={{ fontWeight:700, letterSpacing:'.22em', fontSize:15 }}>REBAR</span>
        </div>
        <div style={{ display:'flex', gap:38, fontFamily:"'JetBrains Mono',monospace", fontSize:12.5, letterSpacing:'.04em', color:'#9aa3b8' }}>
          {LINKS.map(l => <span key={l} style={{ cursor:'pointer' }}>{l}</span>)}
        </div>
        <div style={{
          display:'flex', alignItems:'center', gap:8, padding:'9px 16px',
          border:'1px solid rgba(139,123,255,.5)', borderRadius:6,
          background:'rgba(139,123,255,.08)',
          fontFamily:"'JetBrains Mono',monospace", fontSize:12.5, fontWeight:500,
          cursor:'pointer', boxShadow:'0 0 22px rgba(139,123,255,.18)'
        }}>
          Run live migration <span style={{ color:'#8b7bff', marginLeft:4 }}>→</span>
        </div>
      </nav>

      {/* Telemetry ticker */}
      <div style={{
        position:'relative', zIndex:40, overflow:'hidden',
        borderBottom:'1px solid rgba(255,255,255,.06)',
        background:'rgba(8,10,18,.6)', height:30,
        display:'flex', alignItems:'center'
      }}>
        <div style={{
          display:'flex', gap:42, whiteSpace:'nowrap',
          fontFamily:"'JetBrains Mono',monospace", fontSize:10.5,
          letterSpacing:'.12em', color:'#5a6178',
          animation:'ticker 36s linear infinite', paddingLeft:42
        }}>
          {[...TICKER, ...TICKER].map((t,i) => (
            <span key={i} style={t.startsWith('●') ? {color:'#2fe6d6'} : t.includes('VALIDATION') || t.includes('CHECKPOINT') ? {color:'#8b7bff'} : {}}>{t}</span>
          ))}
        </div>
      </div>
    </>
  )
}
