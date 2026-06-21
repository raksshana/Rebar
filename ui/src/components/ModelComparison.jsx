import React, { useState } from 'react'

const MODELS = [
  { name: 'GPT-5.5',            key: 'gpt'    },
  { name: 'Claude Sonnet 4.6',  key: 'sonnet' },
  { name: 'Claude Opus 4.8',    key: 'opus'   },
  { name: 'Gemini 2.5 Flash',   key: 'gemini' },
]

const METRICS = [
  { label: 'Coverage',               key: 'coverage',               tip: 'Did all records reach the correct destination entity?' },
  { label: 'Field Fidelity',         key: 'field_fidelity',         tip: 'Are field values correctly mapped and preserved?' },
  { label: 'Relationship Integrity', key: 'relationship_integrity', tip: 'Do foreign-key references point to valid destination IDs?' },
  { label: 'Type Correctness',       key: 'type_correctness',       tip: 'Are Python types correct for each field (str, int, bool, etc.)?' },
  { label: 'Structural',             key: 'structural',             tip: 'Were merges, splits, and partitions executed? Models that skip structural transforms are capped at ~20/100.' },
]

const DATA = {
  coverage:               { gpt: 0.86, sonnet: 0.80, opus: 0.72, gemini: 0.59 },
  field_fidelity:         { gpt: 0.91, sonnet: 0.87, opus: 0.80, gemini: 0.63 },
  relationship_integrity: { gpt: 0.94, sonnet: 0.95, opus: 0.87, gemini: 0.68 },
  type_correctness:       { gpt: 0.98, sonnet: 0.98, opus: 0.97, gemini: 0.79 },
  structural:             { gpt: 0.61, sonnet: 0.58, opus: 0.53, gemini: 0.44 },
  total:                  { gpt: 63.5, sonnet: 60.0, opus: 52.4, gemini: 41.4 },
}

function scoreColor(val, isTotal) {
  const v = isTotal ? val / 100 : val
  if (v >= 0.85) return '#2fe6d6'
  if (v >= 0.65) return '#cfd5e4'
  return '#ff6b8a'
}

function MetricRow({ metric, i }) {
  const [hovered, setHovered] = useState(false)
  return (
    <div style={{ display:'grid', gridTemplateColumns:'1fr repeat(4, 1fr)', borderBottom:'1px solid rgba(255,255,255,.05)', background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,.012)', position:'relative' }}>
      <div
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        style={{ padding:'16px 20px', fontSize:14, color: hovered ? '#cfd5e4' : '#717a90', cursor:'default', position:'relative', userSelect:'none' }}
      >
        {metric.label}
        <span style={{ marginLeft:6, fontSize:11, color:'#5a6178', verticalAlign:'middle' }}>ⓘ</span>
        {hovered && (
          <div style={{
            position:'absolute', left:0, top:'100%', zIndex:50,
            background:'rgba(14,16,28,.97)', border:'1px solid rgba(139,123,255,.3)',
            borderRadius:8, padding:'10px 14px', width:280,
            fontSize:12.5, lineHeight:1.6, color:'#cfd5e4',
            boxShadow:'0 8px 28px rgba(0,0,0,.5)',
            pointerEvents:'none',
          }}>
            {metric.tip}
          </div>
        )}
      </div>
      {MODELS.map(m => {
        const val = DATA[metric.key][m.key]
        return (
          <div key={m.key} style={{ padding:'16px 20px', textAlign:'right', fontFamily:"'JetBrains Mono',monospace", fontSize:15, fontWeight:500, color: scoreColor(val, false) }}>
            {val.toFixed(2)}
          </div>
        )
      })}
    </div>
  )
}

export default function ModelComparison() {
  return (
    <section id="benchmarks" style={{ position:'relative', zIndex:10, maxWidth:1280, margin:'0 auto', padding:'30px 40px 80px' }}>
      <div style={{ display:'inline-flex', alignItems:'center', gap:10, fontFamily:"'JetBrains Mono',monospace", fontSize:11, letterSpacing:'.32em', color:'#8b7bff', marginBottom:22 }}>
        <span style={{ width:24, height:1, background:'#8b7bff', display:'inline-block' }} />FRONTIER BENCHMARKS
      </div>
      <h2 style={{ margin:'0 0 44px', fontSize:52, lineHeight:1.02, fontWeight:700, letterSpacing:'-.025em', maxWidth:880 }}>
        Frontier Benchmarks
      </h2>

      <div style={{ border:'1px solid rgba(255,255,255,.08)', borderRadius:14, overflow:'visible', background:'rgba(255,255,255,.015)' }}>
        {/* Header */}
        <div style={{ display:'grid', gridTemplateColumns:'1fr repeat(4, 1fr)', borderBottom:'1px solid rgba(255,255,255,.08)' }}>
          <div style={{ padding:'14px 20px', fontFamily:"'JetBrains Mono',monospace", fontSize:10, letterSpacing:'.16em', color:'#5a6178' }}>METRIC</div>
          {MODELS.map(m => (
            <div key={m.key} style={{ padding:'14px 20px', textAlign:'right' }}>
              <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:11, letterSpacing:'.08em', color:'#8b7bff' }}>{m.name}</div>
              <div style={{ fontFamily:"'JetBrains Mono',monospace", fontSize:22, fontWeight:700, color: scoreColor(DATA.total[m.key], true), marginTop:4 }}>{DATA.total[m.key].toFixed(1)}</div>
            </div>
          ))}
        </div>

        {/* Metric rows */}
        {METRICS.map((metric, i) => (
          <MetricRow key={metric.key} metric={metric} i={i} />
        ))}

        {/* Total row */}
        <div style={{ display:'grid', gridTemplateColumns:'1fr repeat(4, 1fr)', background:'rgba(139,123,255,.06)', borderTop:'1px solid rgba(139,123,255,.2)' }}>
          <div style={{ padding:'20px 20px', fontSize:14, fontWeight:700, color:'#cfd5e4' }}>Total</div>
          {MODELS.map(m => {
            const val = DATA.total[m.key]
            return (
              <div key={m.key} style={{ padding:'20px 20px', textAlign:'right', fontFamily:"'JetBrains Mono',monospace", fontSize:22, fontWeight:700, color: scoreColor(val, true) }}>
                {val.toFixed(1)}
              </div>
            )
          })}
        </div>
      </div>

      <div style={{ marginTop:16, fontFamily:"'JetBrains Mono',monospace", fontSize:11, color:'#5a6178' }}>
        averaged over 5 migrations · tier 3 (obfuscated schemas + structural transforms)
      </div>
    </section>
  )
}
