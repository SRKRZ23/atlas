"""Generate ATLAS architecture SVG."""
import textwrap

W, H = 1200, 720
BG = "#0d1117"
CARD = "#161b22"
BORDER = "#30363d"
ACCENT = "#58a6ff"
GREEN = "#3fb950"
GOLD = "#d29922"
PURPLE = "#bc8cff"
RED = "#f85149"
TEAL = "#39d353"
TEXT = "#e6edf3"
MUTED = "#8b949e"

svg = f'''<svg width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg" font-family="'Segoe UI',system-ui,sans-serif">
  <defs>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
    <marker id="arrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="{MUTED}"/>
    </marker>
    <marker id="arrow-green" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="{GREEN}"/>
    </marker>
  </defs>

  <!-- Background -->
  <rect width="{W}" height="{H}" fill="{BG}"/>

  <!-- Title -->
  <text x="600" y="42" text-anchor="middle" font-size="22" font-weight="700" fill="{TEXT}">ATLAS — Enterprise Multi-Agent System with Governance</text>
  <text x="600" y="64" text-anchor="middle" font-size="13" fill="{MUTED}">Every agentic decision is inspected, signed, and auditable · AI Agent Olympics 2026</text>

  <!-- ── Row 1: Voice Input ── -->
  <!-- Voice box -->
  <rect x="30" y="90" width="160" height="70" rx="8" fill="{CARD}" stroke="{ACCENT}" stroke-width="1.5"/>
  <text x="110" y="118" text-anchor="middle" font-size="13" font-weight="600" fill="{ACCENT}">🎙️ Voice Input</text>
  <text x="110" y="136" text-anchor="middle" font-size="11" fill="{MUTED}">WAV / MP3 / M4A</text>
  <text x="110" y="151" text-anchor="middle" font-size="10" fill="{MUTED}">or typed text</text>

  <!-- Arrow Voice → Speechmatics -->
  <line x1="190" y1="125" x2="230" y2="125" stroke="{MUTED}" stroke-width="1.5" marker-end="url(#arrow)"/>

  <!-- Speechmatics box -->
  <rect x="230" y="90" width="185" height="70" rx="8" fill="{CARD}" stroke="{PURPLE}" stroke-width="1.5"/>
  <text x="322" y="115" text-anchor="middle" font-size="13" font-weight="600" fill="{PURPLE}">🎵 Speechmatics RT</text>
  <text x="322" y="133" text-anchor="middle" font-size="11" fill="{MUTED}">Real-time transcription</text>
  <text x="322" y="150" text-anchor="middle" font-size="10" fill="{PURPLE}">&lt; 200ms · enhanced model</text>

  <!-- Arrow Speechmatics → SOUF AI -->
  <line x1="415" y1="125" x2="455" y2="125" stroke="{MUTED}" stroke-width="1.5" marker-end="url(#arrow)"/>

  <!-- SOUF AI DPI box -->
  <rect x="455" y="90" width="200" height="70" rx="8" fill="{CARD}" stroke="{RED}" stroke-width="2"/>
  <text x="555" y="115" text-anchor="middle" font-size="13" font-weight="600" fill="{RED}">🛡️ SOUF AI DPI</text>
  <text x="555" y="133" text-anchor="middle" font-size="11" fill="{MUTED}">Adversarial prompt inspection</text>
  <text x="555" y="150" text-anchor="middle" font-size="10" fill="{RED}">&lt; 1ms · OWASP LLM Top 10</text>

  <!-- ALLOW arrow SOUF AI → Gemini -->
  <line x1="655" y1="125" x2="695" y2="125" stroke="{GREEN}" stroke-width="2" marker-end="url(#arrow-green)"/>
  <text x="675" y="119" text-anchor="middle" font-size="9" fill="{GREEN}">ALLOW</text>

  <!-- DENY label going down -->
  <line x1="555" y1="160" x2="555" y2="195" stroke="{RED}" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#arrow)"/>
  <text x="572" y="182" font-size="9" fill="{RED}">DENY→403</text>

  <!-- Gemini Orchestrator -->
  <rect x="695" y="90" width="200" height="70" rx="8" fill="{CARD}" stroke="{GOLD}" stroke-width="1.5"/>
  <text x="795" y="115" text-anchor="middle" font-size="13" font-weight="600" fill="{GOLD}">🧠 Gemini 2.0 Flash</text>
  <text x="795" y="133" text-anchor="middle" font-size="11" fill="{MUTED}">Orchestrator + task planner</text>
  <text x="795" y="150" text-anchor="middle" font-size="10" fill="{GOLD}">multi-step decomposition</text>

  <!-- Arrow Gemini → Featherless -->
  <line x1="795" y1="160" x2="795" y2="200" stroke="{MUTED}" stroke-width="1.5" marker-end="url(#arrow)"/>

  <!-- ── Row 2: Featherless Router ── -->
  <rect x="595" y="200" width="400" height="80" rx="8" fill="{CARD}" stroke="{ACCENT}" stroke-width="1.5"/>
  <text x="795" y="225" text-anchor="middle" font-size="13" font-weight="600" fill="{ACCENT}">⚡ Featherless Router</text>
  <text x="795" y="243" text-anchor="middle" font-size="11" fill="{MUTED}">Selects best open-source model per subtask type</text>
  <!-- Model labels -->
  <text x="635" y="268" text-anchor="middle" font-size="9" fill="{MUTED}">🏥 medical</text>
  <text x="700" y="268" text-anchor="middle" font-size="9" fill="{MUTED}">💻 code</text>
  <text x="795" y="268" text-anchor="middle" font-size="9" fill="{MUTED}">🌍 multilingual</text>
  <text x="895" y="268" text-anchor="middle" font-size="9" fill="{MUTED}">💰 financial</text>
  <text x="965" y="268" text-anchor="middle" font-size="9" fill="{MUTED}">⚙️ general</text>

  <!-- ── Row 3: Tool Execution Layer ── -->
  <line x1="795" y1="280" x2="795" y2="320" stroke="{MUTED}" stroke-width="1.5" marker-end="url(#arrow)"/>

  <!-- Tool layer header -->
  <rect x="30" y="320" width="1140" height="36" rx="4" fill="#1c2128" stroke="{BORDER}" stroke-width="1"/>
  <text x="600" y="343" text-anchor="middle" font-size="12" font-weight="600" fill="{MUTED}">Tool Execution Layer</text>

  <!-- 4 tool boxes -->
  <!-- Search -->
  <rect x="30" y="368" width="255" height="80" rx="8" fill="{CARD}" stroke="{BORDER}" stroke-width="1"/>
  <text x="157" y="395" text-anchor="middle" font-size="14">🔍</text>
  <text x="157" y="412" text-anchor="middle" font-size="13" font-weight="600" fill="{TEXT}">Search</text>
  <text x="157" y="430" text-anchor="middle" font-size="10" fill="{MUTED}">Web + internal KB</text>
  <text x="157" y="445" text-anchor="middle" font-size="10" fill="{MUTED}">DuckDuckGo API</text>

  <!-- Database -->
  <rect x="303" y="368" width="255" height="80" rx="8" fill="{CARD}" stroke="{BORDER}" stroke-width="1"/>
  <text x="430" y="395" text-anchor="middle" font-size="14">🗄️</text>
  <text x="430" y="412" text-anchor="middle" font-size="13" font-weight="600" fill="{TEXT}">Database</text>
  <text x="430" y="430" text-anchor="middle" font-size="10" fill="{MUTED}">Read-only sandbox queries</text>
  <text x="430" y="445" text-anchor="middle" font-size="10" fill="{MUTED}">users · transactions · policies</text>

  <!-- Kraken -->
  <rect x="576" y="368" width="255" height="80" rx="8" fill="{CARD}" stroke="{ACCENT}" stroke-width="1.5"/>
  <text x="703" y="395" text-anchor="middle" font-size="14">🌊</text>
  <text x="703" y="412" text-anchor="middle" font-size="13" font-weight="600" fill="{ACCENT}">Kraken</text>
  <text x="703" y="430" text-anchor="middle" font-size="10" fill="{MUTED}">Market data + order book</text>
  <text x="703" y="445" text-anchor="middle" font-size="10" fill="{ACCENT}">BTC · ETH · SOL · ADA</text>

  <!-- Vultr -->
  <rect x="849" y="368" width="321" height="80" rx="8" fill="{CARD}" stroke="{TEAL}" stroke-width="1.5"/>
  <text x="1009" y="395" text-anchor="middle" font-size="14">☁️</text>
  <text x="1009" y="412" text-anchor="middle" font-size="13" font-weight="600" fill="{TEAL}">Vultr</text>
  <text x="1009" y="430" text-anchor="middle" font-size="10" fill="{MUTED}">Infrastructure queries + actions</text>
  <text x="1009" y="445" text-anchor="middle" font-size="10" fill="{TEAL}">instances · regions · plans</text>

  <!-- Arrow tools → audit -->
  <line x1="600" y1="448" x2="600" y2="488" stroke="{MUTED}" stroke-width="1.5" marker-end="url(#arrow)"/>

  <!-- ── Row 4: Ed25519 Audit Trail ── -->
  <rect x="150" y="488" width="900" height="72" rx="8" fill="{CARD}" stroke="{GOLD}" stroke-width="2"/>
  <text x="600" y="513" text-anchor="middle" font-size="14" font-weight="600" fill="{GOLD}">🔏 Ed25519 Audit Trail</text>
  <text x="600" y="533" text-anchor="middle" font-size="11" fill="{MUTED}">Every action: ingress → planning → tool_call → subtask → synthesis · SHA-256 hash-chained</text>
  <text x="600" y="551" text-anchor="middle" font-size="10" fill="{GOLD}">Tamper any record → verify_chain() fails · NACL Ed25519 · deterministic JCS canonical JSON</text>

  <!-- Arrow audit → response -->
  <line x1="600" y1="560" x2="600" y2="598" stroke="{GREEN}" stroke-width="2" marker-end="url(#arrow-green)"/>

  <!-- ── Row 5: Response ── -->
  <rect x="300" y="598" width="600" height="58" rx="8" fill="{CARD}" stroke="{GREEN}" stroke-width="1.5"/>
  <text x="600" y="623" text-anchor="middle" font-size="13" font-weight="600" fill="{GREEN}">✅ Verified Response to User</text>
  <text x="600" y="643" text-anchor="middle" font-size="11" fill="{MUTED}">Gemini Pro synthesis · signed chain exported · citation if DENY</text>

  <!-- ── Stats bar ── -->
  <rect x="0" y="680" width="{W}" height="40" fill="#161b22"/>
  <line x1="0" y1="680" x2="{W}" y2="680" stroke="{BORDER}" stroke-width="1"/>

  <text x="120" y="705" text-anchor="middle" font-size="12" font-weight="600" fill="{ACCENT}">SPEECHMATICS</text>
  <text x="120" y="717" text-anchor="middle" font-size="10" fill="{MUTED}">&lt; 200ms RT voice</text>

  <text x="320" y="705" text-anchor="middle" font-size="12" font-weight="600" fill="{RED}">SOUF AI DPI</text>
  <text x="320" y="717" text-anchor="middle" font-size="10" fill="{MUTED}">&lt; 1ms · 0 FP</text>

  <text x="520" y="705" text-anchor="middle" font-size="12" font-weight="600" fill="{GOLD}">GEMINI 2.0</text>
  <text x="520" y="717" text-anchor="middle" font-size="10" fill="{MUTED}">orchestrator + review</text>

  <text x="720" y="705" text-anchor="middle" font-size="12" font-weight="600" fill="{PURPLE}">FEATHERLESS</text>
  <text x="720" y="717" text-anchor="middle" font-size="10" fill="{MUTED}">5 OSS models routed</text>

  <text x="900" y="705" text-anchor="middle" font-size="12" font-weight="600" fill="{TEAL}">VULTR + KRAKEN</text>
  <text x="900" y="717" text-anchor="middle" font-size="10" fill="{MUTED}">infra + financial layer</text>

  <text x="1090" y="705" text-anchor="middle" font-size="12" font-weight="600" fill="{GOLD}">ED25519 AUDIT</text>
  <text x="1090" y="717" text-anchor="middle" font-size="10" fill="{MUTED}">every action signed</text>
</svg>'''

out = "/Users/sardorrazikov1/Alish/competitions/aiagentolympics/atlas/docs/architecture.svg"
with open(out, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"Written {len(svg)} chars → {out}")
