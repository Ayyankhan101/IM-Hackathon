import React, { useState, useEffect, useRef } from 'react';

const SEV_COLOR = { critical: '#ef4444', high: '#f97316', medium: '#f59e0b', low: '#06b6d4' };

// Mock crisis conversation — auto-plays turn by turn
function getMockScript(finding) {
  return [
    {
      role: 'Engineering', color: '#6ee7b7', delay: 800,
      text: `We've isolated the issue — ${finding.title} in ${finding.file}${finding.line_start ? ` line ${finding.line_start}` : ''}. ${finding.exploit_story} Pulling the affected endpoint offline now. Hotfix ETA: 8 minutes.`,
    },
    {
      role: 'CEO', color: '#fcd34d', delay: 2200,
      text: `How many customers are actually at risk? And do we have any evidence this has already been exploited in production?`,
    },
    {
      role: 'Legal', color: '#a5b4fc', delay: 3800,
      text: `Under GDPR Article 33, if personal data was accessed we have 72 hours to notify the supervisory authority. Under CCPA we have a similar obligation. Engineering must complete the blast radius audit before we send anything external. Do not issue any public statement yet — I need to review it first.`,
    },
    {
      role: 'Engineering', color: '#6ee7b7', delay: 5500,
      text: `Hotfix is live on staging. Running log analysis now — no evidence of exploitation in the last 72 hours. Blast radius: authentication bypass only, no data exfiltration detected. Deploying to production in 3 minutes.`,
    },
    {
      role: 'CEO', color: '#fcd34d', delay: 7200,
      text: `Good. Legal, draft a holding statement but do not send it. The moment Engineering confirms clean logs, we assess whether this crosses the materiality threshold for disclosure.`,
    },
    {
      role: 'Legal', color: '#a5b4fc', delay: 8800,
      text: `Draft ready. I've removed all language that admits liability or specifies unverified scope. Under SEC Reg S-K Item 1.05, if this is material we have 4 business days from determination. Based on Engineering's preliminary findings, we may be below threshold — but I need written confirmation.`,
    },
    {
      role: 'Engineering', color: '#6ee7b7', delay: 10500,
      text: `Patch deployed to production. Confirmed: zero exploitation in logs. Endpoint is hardened. Incident contained. I'm writing up the post-mortem now.`,
    },
    {
      role: 'CEO', color: '#fcd34d', delay: 12000,
      text: `Legal — incident is contained, no evidence of exploitation. Does this require disclosure?`,
    },
    {
      role: 'Legal', color: '#a5b4fc', delay: 13500,
      text: `Based on Engineering's written confirmation of no data access, this does not meet the materiality threshold for mandatory disclosure. We document the incident internally, retain all logs for 7 years, and monitor for 30 days. Incident resolved — no external statement required.`,
    },
  ];
}

export default function CrisisChat({ finding, onClose }) {
  const [messages,   setMessages]   = useState([]);
  const [countdown,  setCountdown]  = useState(45);
  const [resolved,   setResolved]   = useState(false);
  const [leaked,     setLeaked]     = useState(false);
  const [turn,       setTurn]       = useState(0);
  const bottomRef  = useRef(null);
  const script     = useRef(getMockScript(finding));
  const reporterAt = useRef(45);

  // Auto-play script
  useEffect(() => {
    const entries = script.current;
    if (turn >= entries.length) return;
    const timer = setTimeout(() => {
      setMessages(prev => [...prev, entries[turn]]);
      setTurn(t => t + 1);
    }, turn === 0 ? entries[0].delay : entries[turn].delay - entries[turn - 1].delay);
    return () => clearTimeout(timer);
  }, [turn]);

  // Scroll to bottom on each new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Reporter countdown
  useEffect(() => {
    if (resolved || leaked) return;
    const id = setInterval(() => {
      setCountdown(c => {
        if (c <= 1) {
          clearInterval(id);
          // If last message (resolved) not yet shown, reporter leaks
          if (turn < script.current.length) setLeaked(true);
          return 0;
        }
        return c - 1;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [resolved, leaked, turn]);

  // Detect resolution (all turns played)
  useEffect(() => {
    if (turn >= script.current.length && !leaked) {
      setResolved(true);
    }
  }, [turn, leaked]);

  const sevColor = SEV_COLOR[finding.severity?.toLowerCase()] || '#ef4444';
  const timerDanger = countdown <= 10 && !resolved && !leaked;

  return (
    // Backdrop
    <div
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
        display: 'flex', justifyContent: 'flex-end',
      }}
    >
      {/* Panel */}
      <div
        className="slide-in-right"
        style={{
          width: '100%', maxWidth: 560,
          height: '100%', display: 'flex', flexDirection: 'column',
          background: '#0a0505',
          borderLeft: `1px solid ${sevColor}30`,
          boxShadow: `-8px 0 40px rgba(0,0,0,0.6)`,
        }}
      >
        {/* Header */}
        <div style={{
          padding: '18px 20px 14px',
          borderBottom: `1px solid ${sevColor}25`,
          background: `linear-gradient(180deg, ${sevColor}08 0%, transparent 100%)`,
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <span style={{ fontSize: 10, fontWeight: 800, letterSpacing: '0.12em', textTransform: 'uppercase', color: sevColor }}>
                  🚨 Crisis Room
                </span>
                <span style={{ fontSize: 10, color: 'var(--gm-text-3)' }}>· {finding.severity?.toUpperCase()}</span>
              </div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#f1f5f9', lineHeight: 1.3, marginBottom: 4 }}>
                {finding.title}
              </div>
              <code style={{ fontSize: 11, color: 'var(--gm-text-3)', fontFamily: 'JetBrains Mono, monospace' }}>
                {finding.file}{finding.line_start ? `:${finding.line_start}` : ''}
              </code>
            </div>

            {/* Reporter timer */}
            {!resolved && !leaked && (
              <div style={{
                flexShrink: 0, textAlign: 'center',
                padding: '8px 14px', borderRadius: 10,
                background: timerDanger ? 'rgba(239,68,68,0.15)' : 'rgba(255,255,255,0.04)',
                border: `1px solid ${timerDanger ? 'rgba(239,68,68,0.4)' : 'rgba(255,255,255,0.08)'}`,
                animation: timerDanger ? 'gm-critical-pulse 0.8s ease-in-out infinite' : 'none',
              }}>
                <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: timerDanger ? '#fca5a5' : 'var(--gm-text-3)', marginBottom: 3 }}>
                  📰 Reporter
                </div>
                <div style={{ fontSize: 22, fontWeight: 800, fontFamily: 'JetBrains Mono, monospace', color: timerDanger ? '#ef4444' : '#f59e0b', lineHeight: 1 }}>
                  0:{String(countdown).padStart(2, '0')}
                </div>
              </div>
            )}

            <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--gm-text-3)', fontSize: 20, padding: '0 4px', flexShrink: 0, lineHeight: 1 }}
              onMouseEnter={e => { e.currentTarget.style.color = '#f1f5f9'; }}
              onMouseLeave={e => { e.currentTarget.style.color = 'var(--gm-text-3)'; }}>
              ×
            </button>
          </div>

          {/* Role legend */}
          <div style={{ display: 'flex', gap: 14, marginTop: 10 }}>
            {[['CEO', '#fcd34d'], ['Legal', '#a5b4fc'], ['Engineering', '#6ee7b7']].map(([role, color]) => (
              <div key={role} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: 'var(--gm-text-3)' }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: color, flexShrink: 0 }} />
                {role}
              </div>
            ))}
          </div>
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 14 }}>
          {messages.map((msg, i) => (
            <div key={i} className="fade-up">
              <div style={{ fontSize: 10, fontWeight: 700, color: msg.color, letterSpacing: '0.06em', marginBottom: 5 }}>
                {msg.role}
              </div>
              <div style={{
                padding: '11px 14px', borderRadius: '4px 14px 14px 14px',
                background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)',
                fontSize: 13, color: '#e2e8f0', lineHeight: 1.65,
              }}>
                {msg.text}
              </div>
            </div>
          ))}

          {/* Typing indicator while more turns pending */}
          {turn < script.current.length && !resolved && (
            <div style={{ display: 'flex', gap: 4, paddingLeft: 4 }}>
              {[0,150,300].map(d => (
                <span key={d} className="dot-bounce" style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--gm-text-3)', display: 'block', animationDelay: `${d}ms` }} />
              ))}
            </div>
          )}

          {/* Resolution banner */}
          {resolved && (
            <div className="fade-up" style={{
              padding: '16px 18px', borderRadius: 12, textAlign: 'center',
              background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)',
            }}>
              <div style={{ fontSize: 22, marginBottom: 6 }}>✅</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#6ee7b7' }}>Incident Contained</div>
              <div style={{ fontSize: 12, color: 'var(--gm-text-3)', marginTop: 4 }}>The team contained the breach before the reporter published.</div>
            </div>
          )}

          {/* Leak banner */}
          {leaked && (
            <div className="fade-up" style={{
              padding: '16px 18px', borderRadius: 12, textAlign: 'center',
              background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
            }}>
              <div style={{ fontSize: 22, marginBottom: 6 }}>📰</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#fca5a5' }}>BREAKING: Reporter Published</div>
              <div style={{ fontSize: 12, color: 'var(--gm-text-3)', marginTop: 4 }}>The team failed to contain the incident in time. The story is live.</div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Footer */}
        <div style={{ padding: '12px 20px', borderTop: '1px solid rgba(255,255,255,0.06)', flexShrink: 0 }}>
          <button onClick={onClose} style={{
            width: '100%', padding: '10px', borderRadius: 10,
            background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)',
            color: 'var(--gm-text-2)', fontSize: 13, fontWeight: 500,
            transition: 'all 0.15s',
          }}
            onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.09)'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; }}
          >
            Close Crisis Room
          </button>
        </div>
      </div>
    </div>
  );
}
