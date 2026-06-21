import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const MODEL_DATA = {
  overall: [
    { name: 'Kimi K2.7 32B + RL', score: 84.7, type: 'trained', note: 'Specialized model' },
    { name: 'Claude Sonnet 4.6', score: 79.3, type: 'frontier', note: 'Reliable generalist' },
    { name: 'GPT-5.4', score: 76.8, type: 'frontier', note: 'Strong reasoning' },
    { name: 'Kimi K2.7 32B Base', score: 61.4, type: 'base', note: 'No fine-tuning' },
    { name: 'Claude Opus 4.8', score: 53.2, type: 'anomaly', note: 'Unexpected result' },
  ],
  mapping: [
    { name: 'Kimi K2.7 32B + RL', score: 89.4, type: 'trained' },
    { name: 'Claude Sonnet 4.6', score: 87.1, type: 'frontier' },
    { name: 'GPT-5.4', score: 82.8, type: 'frontier' },
    { name: 'Claude Opus 4.8', score: 70.4, type: 'anomaly' },
    { name: 'Kimi K2.7 32B Base', score: 67.3, type: 'base' },
  ],
  correctness: [
    { name: 'Kimi K2.7 32B + RL', score: 86.2, type: 'trained' },
    { name: 'Claude Sonnet 4.6', score: 80.5, type: 'frontier' },
    { name: 'GPT-5.4', score: 78.1, type: 'frontier' },
    { name: 'Kimi K2.7 32B Base', score: 59.7, type: 'base' },
    { name: 'Claude Opus 4.8', score: 51.9, type: 'anomaly' },
  ],
  relationships: [
    { name: 'Kimi K2.7 32B + RL', score: 83.8, type: 'trained' },
    { name: 'Claude Sonnet 4.6', score: 76.4, type: 'frontier' },
    { name: 'GPT-5.4', score: 73.2, type: 'frontier' },
    { name: 'Kimi K2.7 32B Base', score: 57.6, type: 'base' },
    { name: 'Claude Opus 4.8', score: 49.3, type: 'anomaly' },
  ],
  repair: [
    { name: 'Kimi K2.7 32B + RL', score: 82.9, type: 'trained' },
    { name: 'Claude Sonnet 4.6', score: 72.3, type: 'frontier' },
    { name: 'GPT-5.4', score: 68.6, type: 'frontier' },
    { name: 'Kimi K2.7 32B Base', score: 46.8, type: 'base' },
    { name: 'Claude Opus 4.8', score: 38.7, type: 'anomaly' },
  ],
}

const SCENARIOS = [
  {
    source: 'Legacy CRM', destination: 'Modern Customer Platform', tables: 18, fields: 142,
    records: 24000, issues: 31, relationships: 12,
    examples: [
      ['customer_name', 'full_name', 'Renaming a customer field'],
      ['12/04/2024', '2024-12-04', 'Standardizing a date'],
      ['order.customer_email', 'order.customer_id', 'Repairing a relationship'],
    ],
  },
  {
    source: 'Retail Operations DB', destination: 'Unified Commerce Cloud', tables: 27, fields: 216,
    records: 48600, issues: 44, relationships: 19,
    examples: [
      ['cust_ref', 'customer_id', 'Resolving an entity'],
      ['$1,240.00', '1240.00 USD', 'Normalizing currency'],
      ['duplicate_order × 2', 'verified_order × 1', 'Removing a duplicate'],
    ],
  },
  {
    source: 'Claims Archive', destination: 'Care Data Platform', tables: 34, fields: 308,
    records: 72500, issues: 57, relationships: 26,
    examples: [
      ['7-2-91', '1991-07-02', 'Converting a date format'],
      ['member_code', 'patient_id', 'Connecting patient records'],
      ['ACTIVE / A / 1', 'active', 'Mapping inconsistent values'],
    ],
  },
]

const TRAINING_POINTS = [
  { step: 'Base', score: 61.4 },
  { step: '80', score: 65.8 },
  { step: '160', score: 70.6 },
  { step: '240', score: 75.4 },
  { step: '320', score: 80.9 },
  { step: 'Final', score: 84.7 },
]

const Icon = ({ name, size = 18 }) => {
  const paths = {
    arrow: <><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></>,
    check: <path d="m5 12 4 4L19 6"/>,
    spark: <><path d="m12 3 1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7-4.7-1.8 4.7-1.8L12 3Z"/><path d="m19 15 .8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15Z"/></>,
    database: <><ellipse cx="12" cy="5" rx="7" ry="3"/><path d="M5 5v6c0 1.7 3.1 3 7 3s7-1.3 7-3V5"/><path d="M5 11v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6"/></>,
    shield: <><path d="M12 3 5 6v5c0 4.8 2.9 8.3 7 10 4.1-1.7 7-5.2 7-10V6l-7-3Z"/><path d="m9 12 2 2 4-4"/></>,
    code: <><path d="m8 9-4 3 4 3"/><path d="m16 9 4 3-4 3"/><path d="m14 5-4 14"/></>,
    chart: <><path d="M4 19V5"/><path d="M4 19h16"/><path d="m7 15 4-4 3 2 5-7"/></>,
    wrench: <><path d="M14.7 6.3a4 4 0 0 0-5 5L4 17l3 3 5.7-5.7a4 4 0 0 0 5-5l-2.5 2.5-3-3 2.5-2.5Z"/></>,
    menu: <><path d="M4 7h16"/><path d="M4 12h16"/><path d="M4 17h16"/></>,
    x: <><path d="m6 6 12 12"/><path d="M18 6 6 18"/></>,
    chevron: <path d="m9 18 6-6-6-6"/>,
  }
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>
}

function App() {
  const [scenarioIndex, setScenarioIndex] = useState(0)
  const [running, setRunning] = useState(false)
  const [stage, setStage] = useState(0)
  const [exampleIndex, setExampleIndex] = useState(0)
  const [metric, setMetric] = useState('overall')
  const [technicalOpen, setTechnicalOpen] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const scenario = SCENARIOS[scenarioIndex]

  const progress = [0, 22, 64, 100][stage]
  const mapped = Math.round(scenario.fields * progress / 100)
  const migrated = Math.round(scenario.records * Math.max(0, progress - 10) / 90)
  const repaired = Math.round(scenario.issues * Math.max(0, progress - 38) / 62)
  const activeExample = scenario.examples[exampleIndex]

  useEffect(() => {
    if (!running) return
    const timings = [
      setTimeout(() => setStage(1), 500),
      setTimeout(() => setStage(2), 2200),
      setTimeout(() => setExampleIndex(1), 3900),
      setTimeout(() => setExampleIndex(2), 5400),
      setTimeout(() => setStage(3), 7000),
      setTimeout(() => setRunning(false), 8400),
    ]
    return () => timings.forEach(clearTimeout)
  }, [running, scenarioIndex])

  const runMigration = () => {
    setStage(0)
    setExampleIndex(0)
    setRunning(true)
  }

  const newScenario = () => {
    setScenarioIndex((scenarioIndex + 1) % SCENARIOS.length)
    setStage(0)
    setExampleIndex(0)
    setRunning(false)
  }

  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
    setMobileOpen(false)
  }

  return (
    <div className="site-shell">
      <header className="nav-wrap">
        <nav className="nav container">
          <button className="brand" onClick={() => scrollTo('top')} aria-label="Rebar home">
            <span className="brand-mark"><span></span><span></span><span></span></span>
            <span>REBAR</span>
          </button>
          <div className={`nav-links ${mobileOpen ? 'open' : ''}`}>
            <button onClick={() => scrollTo('product')}>Product</button>
            <button onClick={() => scrollTo('benchmarks')}>Benchmarks</button>
            <button onClick={() => scrollTo('training')}>Training</button>
            <button onClick={() => scrollTo('research')}>Research</button>
          </div>
          <button className="nav-cta desktop-only" onClick={() => scrollTo('product')}>Run live migration <Icon name="arrow" size={15}/></button>
          <button className="mobile-menu" onClick={() => setMobileOpen(!mobileOpen)} aria-label="Toggle menu"><Icon name={mobileOpen ? 'x' : 'menu'} /></button>
        </nav>
      </header>

      <main id="top">
        <section className="hero section-dark">
          <div className="orb orb-one"></div><div className="orb orb-two"></div>
          <div className="container hero-grid">
            <div className="hero-copy reveal">
              <div className="eyebrow light"><span></span>AUTONOMOUS DATA MIGRATION</div>
              <h1>Migrate any schema.<br/><em>Verify every record.</em></h1>
              <p>Rebar uses AI agents to understand unfamiliar databases, generate transformations, repair failures, and validate the completed result—without hand-written mappings.</p>
              <div className="future-tagline">Data is always migrating into the future. Autonomy is needed — hand-mapped migrations cannot provide a solution at scale.</div>
              <div className="hero-actions">
                <button className="button primary" onClick={() => scrollTo('product')}>Run a live migration <Icon name="arrow"/></button>
                <button className="button ghost" onClick={() => scrollTo('benchmarks')}>View benchmark results</button>
              </div>
              <div className="credibility"><span><Icon name="spark" size={15}/> Random schemas</span><span><Icon name="shield" size={15}/> Deterministic grading</span><span><Icon name="chart" size={15}/> RL-trained model</span></div>
            </div>

            <div className="hero-product reveal delay-one">
              <div className="browser-frame">
                <div className="browser-bar"><div className="window-dots"><i></i><i></i><i></i></div><div className="browser-url">app.rebar.ai / migration-4821</div><div className="live-dot">LIVE</div></div>
                <div className="preview-body">
                  <div className="preview-header"><div><small>AUTONOMOUS MIGRATION</small><strong>Legacy CRM → Customer Platform</strong></div><span className="success-pill">Verified</span></div>
                  <div className="preview-flow">
                    <div className="mini-system"><small>BEFORE</small><h4>Legacy CRM</h4><div><span>Tables</span><b>18</b></div><div><span>Fields</span><b>142</b></div><div><span>Records</span><b>24,000</b></div><div><span>Issues</span><b>31</b></div></div>
                    <div className="mini-agent"><div className="agent-core"><Icon name="spark" size={22}/></div><strong>AI migration</strong><span>Everything mapped</span><div className="flow-line"><i></i></div><div className="code-transform"><code>customer_email</code><Icon name="arrow" size={13}/><code>customer_id</code></div></div>
                    <div className="mini-system after"><small>AFTER</small><h4>Customer Platform</h4><div><span>Mapped</span><b>142</b></div><div><span>Migrated</span><b>24,000</b></div><div><span>Relations</span><b>12</b></div><div><span>Unresolved</span><b className="green">0</b></div></div>
                  </div>
                  <div className="preview-score"><span>Validation score</span><strong>99.6%</strong><div><i></i></div></div>
                </div>
              </div>
              <div className="floating-card fc-one"><Icon name="wrench"/><div><small>AUTOMATIC REPAIR</small><strong>31 issues resolved</strong></div></div>
              <div className="floating-card fc-two"><Icon name="shield"/><div><small>VALIDATION</small><strong>0 unresolved issues</strong></div></div>
            </div>
          </div>
          <div className="container capability-strip">
            <div><Icon name="database"/><span><strong>No migration scripts</strong>Discovers unfamiliar schemas automatically.</span></div>
            <div><Icon name="wrench"/><span><strong>Self-repairing execution</strong>Diagnoses failed transformations and retries.</span></div>
            <div><Icon name="shield"/><span><strong>End-to-end verification</strong>Proves records and relationships survived.</span></div>
          </div>
        </section>

        <section className="section light" id="product">
          <div className="container">
            <SectionHeading eyebrow="LIVE PRODUCT DEMO" title={<>Watch the agent migrate a database<br/><em>it has never seen before.</em></>} text="Every scenario is generated dynamically. The model receives the source, destination, and migration tools—but no prewritten solution." />

            <div className="app-window">
              <div className="app-topbar">
                <div><span className="app-logo"><span></span><span></span><span></span></span><b>Rebar Migration Engine</b></div>
                <div className="app-status"><span className={stage === 3 ? 'green-dot' : 'pulse-dot'}></span>{stage === 3 ? 'Migration verified' : running ? 'Agent working' : 'Ready to run'}</div>
                <div className="app-actions"><button onClick={newScenario}>Generate scenario</button><button className="run-button" onClick={runMigration} disabled={running}>{running ? 'Migration running…' : stage === 3 ? 'Run again' : 'Run migration'} <Icon name="arrow" size={15}/></button></div>
              </div>
              <div className="app-content">
                <div className="migration-title"><div><small>GENERATED SCENARIO</small><h3>{scenario.source} <span>→</span> {scenario.destination}</h3></div><div className={`status-chip stage-${stage}`}>{stage === 0 ? 'Ready' : stage === 1 ? 'Analyzing source' : stage === 2 ? 'Transforming data' : 'Migration successful'}</div></div>

                <div className="migration-grid">
                  <SystemCard label="BEFORE" title={scenario.source} subtitle="Complex source data" stats={[['Tables', scenario.tables], ['Fields', scenario.fields], ['Records', scenario.records.toLocaleString()], ['Data issues', scenario.issues]]}/>

                  <div className="agent-panel">
                    <div className="stage-row">
                      {['Understand','Transform','Verify'].map((s,i) => <div key={s} className={`stage-tab ${stage > i ? 'done' : stage === i + 1 ? 'active' : ''}`}><span>{stage > i ? '✓' : i+1}</span>{s}</div>)}
                    </div>
                    <div className="agent-message" aria-live="polite">
                      <div className="agent-kicker">{stage === 0 ? 'READY' : stage === 1 ? 'STEP 1 OF 3' : stage === 2 ? exampleIndex === 2 ? 'AUTOMATIC REPAIR' : 'STEP 2 OF 3' : 'MIGRATION COMPLETE'}</div>
                      <h3>{stage === 0 ? 'Waiting to begin' : stage === 1 ? 'Understanding the data' : stage === 2 ? activeExample[2] : 'Everything moved and verified'}</h3>
                      <p>{stage === 0 ? 'The agent works even when source and destination schemas are generated at random.' : stage === 1 ? `Inspecting ${scenario.tables} tables, ${scenario.fields} fields, and ${scenario.records.toLocaleString()} records.` : stage === 2 ? exampleIndex === 2 ? 'The agent detected an issue, selected a repair, and retried the affected records.' : 'A representative transformation from the live migration.' : `${scenario.records.toLocaleString()} records migrated, ${scenario.issues} issues repaired, and no unresolved problems remain.`}</p>
                      {stage === 2 && <div className="transform-box"><code>{activeExample[0]}</code><span><Icon name="arrow"/></span><code>{activeExample[1]}</code></div>}
                      {stage === 1 && <div className="scan-lines"><i></i><i></i><i></i></div>}
                      {stage === 3 && <div className="completion-mark"><Icon name="check" size={28}/></div>}
                    </div>
                  </div>

                  <SystemCard label="AFTER" title={scenario.destination} subtitle="Clean, verified destination" stats={[['Mapped fields', mapped], ['Records migrated', Math.min(migrated, scenario.records).toLocaleString()], ['Relationships rebuilt', Math.round(scenario.relationships * progress / 100)], ['Unresolved issues', stage === 3 ? 0 : '—']]}/>
                </div>

                <div className="metric-grid">
                  <Metric label="Fields mapped" value={`${mapped} / ${scenario.fields}`} progress={progress}/>
                  <Metric label="Records migrated" value={Math.min(migrated, scenario.records).toLocaleString()} helper={stage === 3 ? 'All records transferred' : running ? 'Moving records' : 'Waiting to start'}/>
                  <Metric label="Issues repaired" value={Math.min(repaired, scenario.issues)} helper="Automatically handled"/>
                  <Metric label="Validation score" value={stage === 3 ? '99.6%' : '—'} helper="End-to-end correctness"/>
                </div>

                <div className="demo-lower">
                  <div className="proof-card">
                    <div className="card-heading"><div><small>MODEL IMPROVEMENT</small><h3>Specialization changes the result</h3></div><span className="gain-badge">+23.3 pts</span></div>
                    <div className="mini-comparison"><div><span>Kimi K2.7 base</span><b>61.4</b><i style={{width:'61.4%'}}></i></div><div className="trained"><span>Kimi K2.7 + RL</span><b>84.7</b><i style={{width:'84.7%'}}></i></div></div>
                    <p>Task-specific reinforcement learning improves multi-step execution, repair behavior, and final validation.</p>
                  </div>
                  <div className="event-card">
                    <div className="card-heading"><div><small>LIVE EVENT FEED</small><h3>What the agent is doing</h3></div><span className="event-count">4 events</span></div>
                    <div className="event-list">
                      <Event title={stage === 3 ? 'Migration completed successfully' : stage >= 2 ? 'Transformation plan executing' : 'Source structure discovered'} text={stage === 3 ? `${scenario.records.toLocaleString()} records transferred with 0 unresolved issues.` : stage >= 2 ? 'Mappings are being executed and checked in the sandbox.' : `${scenario.tables} tables and ${scenario.fields} fields found automatically.`} active/>
                      <Event title="Migration plan created" text={`The agent identified ${scenario.relationships} relationships and proposed field mappings.`}/>
                      <Event title="Deterministic validation ready" text="Completeness, relationships, and destination meaning will be checked."/>
                    </div>
                  </div>
                </div>

                <button className="technical-toggle" onClick={() => setTechnicalOpen(!technicalOpen)}>{technicalOpen ? 'Hide technical details' : 'View technical details'} <Icon name="chevron" size={15}/></button>
                {technicalOpen && <div className="technical-panel">
                  <div><small>REPRESENTATIVE MAPPINGS</small><table><thead><tr><th>Source</th><th>Destination</th><th>Operation</th></tr></thead><tbody><tr><td>customer_name</td><td>full_name</td><td><span>Rename</span></td></tr><tr><td>signup_date</td><td>created_at</td><td><span>Date conversion</span></td></tr><tr><td>customer_email</td><td>customer_id</td><td><span>Relationship lookup</span></td></tr></tbody></table></div>
                  <div><small>VALIDATION CHECKS</small><table><thead><tr><th>Validation</th><th>Status</th></tr></thead><tbody><tr><td>Schema compatibility</td><td className="pass">✓ Passed</td></tr><tr><td>Record completeness</td><td className="pass">✓ Passed</td></tr><tr><td>Relationship integrity</td><td className="pass">✓ Passed</td></tr></tbody></table></div>
                </div>}
              </div>
            </div>
          </div>
        </section>

        <section className="section benchmark-section" id="benchmarks">
          <div className="container">
            <SectionHeading eyebrow="MODEL EVALUATION" title={<>Frontier models are powerful.<br/><em>Specialization changes the leaderboard.</em></>} text="Every model receives the same generated migrations, tools, execution limits, and deterministic grader." />
            <div className="benchmark-shell">
              <div className="benchmark-topline"><div><span className="tested-dot"></span> 5 models tested</div><span>Scores shown below are editable demo placeholders</span></div>
              <div className="metric-tabs">
                {[['overall','Overall score'],['mapping','Schema mapping'],['correctness','Data correctness'],['relationships','Relationships'],['repair','Repair success']].map(([key,label]) => <button key={key} className={metric===key?'active':''} onClick={() => setMetric(key)}>{label}</button>)}
              </div>
              <Leaderboard data={MODEL_DATA[metric]}/>
              <div className="benchmark-callout">
                <div className="base-box"><small>BASE MODEL</small><strong>61.4</strong><span>Kimi K2.7 32B</span></div>
                <div className="gain-arrow"><span>+23.3 points</span><div><i></i><Icon name="arrow" size={20}/></div><small>THROUGH REINFORCEMENT LEARNING</small></div>
                <div className="trained-box"><small>SPECIALIZED MODEL</small><strong>84.7</strong><span>Kimi K2.7 32B + RL</span></div>
              </div>
            </div>
          </div>
        </section>

        <section className="section training-section" id="training">
          <div className="container">
            <SectionHeading eyebrow="REINFORCEMENT LEARNING" title={<>The model learned to migrate,<br/><em>repair, and verify.</em></>} text="The RL loop rewards completed migrations using the same deterministic grader used for held-out evaluation." />
            <div className="training-grid">
              <TrainingChart />
              <div className="training-sidebar">
                <div className="training-card highlight"><small>SCORE IMPROVEMENT</small><strong>+23.3</strong><span>held-out benchmark points</span></div>
                <div className="training-card"><small>FINAL SCORE</small><strong>84.7</strong><span>selected checkpoint</span></div>
                <div className="training-card"><small>TRAINING TASKS</small><strong>400</strong><span>generated migrations</span></div>
                <div className="training-card"><small>CHECKPOINT</small><strong>380</strong><span>best held-out result</span></div>
              </div>
            </div>
            <div className="method-note"><Icon name="shield"/><div><strong>Held-out score, not training reward</strong><span>The visible curve should use migrations excluded from RL updates so the improvement is credible to judges.</span></div></div>
          </div>
        </section>

        <section className="section research-section" id="research">
          <div className="container">
            <div className="research-heading">
              <div className="eyebrow light"><span></span>UNEXPECTED FINDING</div>
              <h2>The largest model was not the<br/><em>strongest migration agent.</em></h2>
              <p>Claude Opus 4.8 substantially underperformed Sonnet in this environment. We investigated the failure modes instead of treating the aggregate score as the whole explanation.</p>
            </div>
            <div className="research-grid">
              <div className="finding-card score-gap"><small>WHAT HAPPENED</small><div className="model-score-line"><span>Claude Sonnet 4.6</span><b>79.3</b></div><div className="model-score-line bad"><span>Claude Opus 4.8</span><b>53.2</b></div><div className="difference"><span>Performance gap</span><strong>−26.1</strong></div></div>
              <div className="finding-card"><small>WHERE IT FAILED</small><FailureRow label="Incorrect tool sequence" value={34}/><FailureRow label="Incomplete migration" value={27}/><FailureRow label="Invalid output structure" value={19}/><FailureRow label="Unnecessary changes" value={12}/></div>
              <div className="finding-card hypothesis"><small>CURRENT HYPOTHESIS</small><div className="quote-mark">“</div><p>Opus may be optimizing for a more elaborate interpretation, while the grader rewards precise execution and strict adherence to the requested migration.</p><span>Hypothesis — pending trace-level validation</span></div>
            </div>
            <div className="trace-comparison">
              <div className="trace-label"><small>SAME GENERATED TASK</small><h3>One task. Two very different execution paths.</h3></div>
              <div className="trace-card good"><div className="trace-head"><span>Claude Sonnet 4.6</span><b>Score 91</b></div><ul><li><Icon name="check"/>Mapped 47 / 47 fields</li><li><Icon name="check"/>Executed the full migration</li><li><Icon name="check"/>Repaired 3 relationships</li><li><Icon name="check"/>Completed final validation</li></ul></div>
              <div className="trace-card bad"><div className="trace-head"><span>Claude Opus 4.8</span><b>Score 48</b></div><ul><li><Icon name="check"/>Proposed 52 mappings</li><li><span className="xicon">×</span>Changed destination assumptions</li><li><span className="xicon">×</span>Consumed tool budget early</li><li><span className="xicon">×</span>Did not complete validation</li></ul></div>
            </div>
          </div>
        </section>

        <section className="section business-section">
          <div className="container">
            <SectionHeading eyebrow="BUILT FOR REAL OPERATIONS" title={<>Migrations too complex<br/><em>to map by hand.</em></>} text="Rebar turns a months-long custom engineering project into an inspectable, repeatable workflow." />
            <div className="use-case-grid"><UseCase icon="database" title="CRM modernization" text="Move customer, account, and activity data into a new operational system."/><UseCase icon="spark" title="Database consolidation" text="Merge inconsistent schemas from acquired teams or legacy products."/><UseCase icon="code" title="Platform replacement" text="Translate records and relationships while preserving business meaning."/></div>
            <div className="workflow"><div><span>01</span><strong>Connect systems</strong></div><Icon name="arrow"/><div><span>02</span><strong>Generate plan</strong></div><Icon name="arrow"/><div><span>03</span><strong>Execute safely</strong></div><Icon name="arrow"/><div><span>04</span><strong>Repair failures</strong></div><Icon name="arrow"/><div><span>05</span><strong>Approve output</strong></div></div>
          </div>
        </section>

        <section className="final-cta">
          <div className="container final-cta-inner"><div><div className="eyebrow light"><span></span>BUILD THE NEXT MIGRATION</div><h2>The next database migration should not begin with months of manual mapping.</h2><p>Generate a scenario, watch the agent execute it, and inspect every transformation it made.</p></div><button className="button primary light-button" onClick={() => scrollTo('product')}>Run another migration <Icon name="arrow"/></button></div>
        </section>
      </main>

      <footer><div className="container"><div className="brand footer-brand"><span className="brand-mark"><span></span><span></span><span></span></span><span>REBAR</span></div><p>Autonomous data migration, repair, and verification.</p><span>Built for the hackathon demo.</span></div></footer>
    </div>
  )
}

function SectionHeading({ eyebrow, title, text }) {
  return <div className="section-heading"><div className="eyebrow"><span></span>{eyebrow}</div><h2>{title}</h2><p>{text}</p></div>
}

function SystemCard({ label, title, subtitle, stats }) {
  return <div className="system-card"><small>{label}</small><h3>{title}</h3><p>{subtitle}</p><div className="system-stats">{stats.map(([k,v]) => <div key={k}><span>{k}</span><b className={k==='Unresolved issues' && v===0 ? 'green' : ''}>{v}</b></div>)}</div></div>
}

function Metric({ label, value, helper, progress }) {
  return <div className="metric-card"><small>{label}</small><strong>{value}</strong>{typeof progress === 'number' ? <div className="metric-progress"><i style={{width:`${progress}%`}}></i></div> : <span>{helper}</span>}</div>
}

function Event({ title, text, active }) {
  return <div className={`event ${active?'active':''}`}><div><Icon name={active?'spark':'check'} size={15}/></div><span><strong>{title}</strong><small>{text}</small></span></div>
}

function Leaderboard({ data }) {
  const sorted = useMemo(() => [...data].sort((a,b)=>b.score-a.score), [data])
  return <div className="leaderboard">{sorted.map((model,index) => <div className={`leader-row ${model.type}`} key={model.name}><div className="rank">{String(index+1).padStart(2,'0')}</div><div className="model-info"><div><strong>{model.name}</strong>{model.note && <span>{model.note}</span>}</div><div className="score-bar"><i style={{width:`${model.score}%`}}></i></div></div><div className="score-number">{model.score.toFixed(1)}</div>{model.type==='trained' && <div className="best-badge">BEST</div>}</div>)}</div>
}

function TrainingChart() {
  const min = 58, max = 88
  const width = 760, height = 360, padX = 58, padY = 38
  const points = TRAINING_POINTS.map((p,i) => ({...p, x: padX + i*((width-padX*2)/(TRAINING_POINTS.length-1)), y: height-padY-((p.score-min)/(max-min))*(height-padY*2)}))
  const path = points.map((p,i)=>`${i===0?'M':'L'} ${p.x} ${p.y}`).join(' ')
  const area = `${path} L ${points.at(-1).x} ${height-padY} L ${points[0].x} ${height-padY} Z`
  const refs = [{score:79.3,label:'Claude Sonnet 4.6'},{score:76.8,label:'GPT-5.4'}]
  return <div className="chart-card"><div className="chart-card-head"><div><small>HELD-OUT MIGRATION SCORE</small><h3>Improvement across RL checkpoints</h3></div><div className="legend"><span className="line-legend"></span>Validation score</div></div><div className="chart-wrap"><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Training curve rising from 61.4 to 84.7">
    <defs><linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#7668ff" stopOpacity=".28"/><stop offset="100%" stopColor="#7668ff" stopOpacity="0"/></linearGradient></defs>
    {[60,70,80].map(v => {const y=height-padY-((v-min)/(max-min))*(height-padY*2); return <g key={v}><line x1={padX} x2={width-padX} y1={y} y2={y} className="grid-line"/><text x={22} y={y+4} className="axis-label">{v}</text></g>})}
    {refs.map(r=>{const y=height-padY-((r.score-min)/(max-min))*(height-padY*2); return <g key={r.label}><line x1={padX} x2={width-padX} y1={y} y2={y} className="ref-line"/><text x={width-padX-4} y={y-7} textAnchor="end" className="ref-label">{r.label} · {r.score}</text></g>})}
    <path d={area} fill="url(#areaFill)"/><path d={path} className="curve-line"/>
    {points.map((p,i)=><g key={p.step}><circle cx={p.x} cy={p.y} r={i===points.length-1?7:5} className={i===points.length-1?'final-point':'point'}/><text x={p.x} y={height-10} textAnchor="middle" className="axis-label">{p.step}</text>{(i===0||i===points.length-1)&&<g><rect x={p.x-27} y={p.y-34} width="54" height="23" rx="7" className="score-bubble"/><text x={p.x} y={p.y-18} textAnchor="middle" className="bubble-text">{p.score}</text></g>}</g>)}
  </svg></div></div>
}

function FailureRow({label,value}) { return <div className="failure-row"><div><span>{label}</span><b>{value}%</b></div><i><em style={{width:`${value}%`}}></em></i></div> }
function UseCase({icon,title,text}) { return <div className="use-case"><div><Icon name={icon}/></div><h3>{title}</h3><p>{text}</p><button>Explore use case <Icon name="arrow" size={14}/></button></div> }

createRoot(document.getElementById('root')).render(<React.StrictMode><App /></React.StrictMode>)
