import React from 'react'

const LINKS = [
  { label:'Benchmarks', href:'#benchmarks' },
  { label:'Training',   href:'#training' },
  { label:'Research',   href:'#research' },
]

export default function Nav() {
  return (
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
          {LINKS.map(({ label, href }) => (
            <a key={label} href={href} style={{ color:'inherit', textDecoration:'none', cursor:'pointer' }}
              onMouseEnter={e => e.currentTarget.style.color='#e9edf6'}
              onMouseLeave={e => e.currentTarget.style.color='#9aa3b8'}>
              {label}
            </a>
          ))}
        </div>
      </nav>
  )
}
