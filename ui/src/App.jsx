import React from 'react'
import Nav from './components/Nav'
import Hero from './components/Hero'
import CapabilityStrip from './components/CapabilityStrip'
import MigrationEngine from './components/MigrationEngine'
import RLChart from './components/RLChart'
import ModelComparison from './components/ModelComparison'
import UseCases from './components/UseCases'
import CTA from './components/CTA'

export default function App() {
  return (
    <div style={{ position:'relative', minHeight:'100vh', background:'#06080f', color:'#e9edf6', overflow:'hidden' }}>
      <div className="grid-bg" />
      <div className="glow-violet" />
      <div className="glow-cyan" />
      <div className="scanlines" />
      <div className="vignette" />
      <div className="sweep-band" />
      <div className="reticle reticle-tl" />
      <div className="reticle reticle-tr" />
      <div className="reticle reticle-bl" />
      <div className="reticle reticle-br" />

      <Nav />
      <Hero />
      <CapabilityStrip />
      <MigrationEngine />
      <RLChart />
      <ModelComparison />
      <UseCases />
      <CTA />
    </div>
  )
}
