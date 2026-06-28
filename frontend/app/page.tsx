// app/page.tsx
export default function Home() {
  const showFull = process.env.NEXT_PUBLIC_SHOW_FULL === 'true';

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>QEDSoft</h1>
      <p>Automated RTL Verification & Formal Proof Platform</p>

      {showFull ? (
        <div>
          <h2>Industry Problems Solved</h2>
          <p>Built around verification pain points at companies like Infineon, NXP, Renesas</p>
          
          <ul>
            <li><strong>Specs are informal and ambiguous</strong> → LLM + regex extraction with confidence scoring</li>
            <li><strong>Signal names in specs don't match RTL</strong> → Fuzzy signal mapping with difflib</li>
            <li><strong>SVA writing requires formal expertise</strong> → Automatic SVA generation from NL requirements</li>
            <li><strong>Formal tool diagnostics are not acted on</strong> → SERA-VGP automated repair loop</li>
            <li><strong>MATLAB and RTL verified in separate flows</strong> → Job 1 unifies both into Lean4 equivalence proof</li>
            <li><strong>Verification coverage hard to trace to requirements</strong> → mapping_coverage metric with REQ → SVA traceability</li>
          </ul>

          <p><em>Semiconductor RTL Verification · Aligned with ISO 26262 / ASIL-D</em></p>
        </div>
      ) : (
        <div>
          <p>Secure formal verification platform for semiconductor design.</p>
          <p><a href="mailto:contact@qedai.org">Contact us for details</a></p>
        </div>
      )}
    </div>
  );
}