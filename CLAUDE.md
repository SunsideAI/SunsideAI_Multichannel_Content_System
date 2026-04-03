# CLAUDE.md — Sunside AI Content Autopilot

## Projektübersicht

Dieses Projekt ist eine vollautomatische Content-Pipeline für Sunside AI (sunsideai.de). Es kombiniert SEO-Keyword-Research, bestehende Content-Analyse und Trend-Research zu einer datengetriebenen Content-Strategie. Das System identifiziert Keyword-Lücken, recherchiert passende Studien und Trends, erstellt SEO-optimierte Blogbeiträge, generiert LinkedIn-Infografiken und postet automatisch — alles ohne menschliches Eingreifen, aber mit optionalem Review-Fenster.

**Unternehmen:** Sunside AI GbR (Braunschweig) — KI-Chatbots, Automatisierung & Webdesign für Immobilienmakler
**Zielgruppe der Inhalte:** Deutsche Immobilienmakler, Sachverständige, PropTech-Interessierte (25-45 Jahre)
**Sprache aller Inhalte:** Deutsch
**Website:** sunsideai.de (Next.js 14, Netlify)
**Blog-Repo:** github.com/SunsideAI/SunsideAI_Website

---

## Tech Stack

- **Runtime:** Python 3.11+
- **Hosting:** Railway (Agent-Service) oder GitHub Actions (Scheduler)
- **Datenbank:** Supabase (PostgreSQL) — State Management, Findings, Keywords, Config
- **Content-API:** Anthropic Claude API (claude-sonnet-4-20250514)
- **Blog-Deployment:** GitHub API → Push ins Website-Repo → Netlify auto-deploy
- **LinkedIn:** LinkedIn API v2 (OAuth 2.0, UGC Posts)
- **Research-Quellen:** RSS Feeds (feedparser), Semantic Scholar API, Google Alerts Atom Feeds
- **SEO-Daten:** Google Search Console API (Performance-Daten, Keywords, Impressions, CTR, Position)
- **Keyword-Research:** Google Autocomplete API (kostenlos), SERP-Scraping für "Ähnliche Fragen"
- **Content-Crawling:** BeautifulSoup + requests für sunsideai.de Site-Crawl
- **Bildgenerierung:** Pillow (PIL) + wkhtmltoimage für Infografiken
- **Benachrichtigung:** Slack Webhook oder Brevo E-Mail API

---

## Architektur

### Fünf Agents, zwei Streams

```
STREAM A: SEO Intelligence (wöchentlich)
CONTENT CRAWLER → KEYWORD RESEARCHER → CONTENT STRATEGIST
(Sonntag 18:00)   (Sonntag 19:00)      (Sonntag 19:30)

STREAM B: Content Production (täglich)  
RESEARCH AGENT → BLOG WRITER AGENT → DISTRIBUTION AGENT
(Sonntag 20:00)   (Mo-Fr 06:00)       (Mo-Fr 10:00)
```

Stream A liefert die strategische Richtung: Welche Keywords haben Potenzial? Wo sind Content-Lücken? Welche bestehenden Posts brauchen ein Update?

Stream B nutzt diese Intelligence: Der Research Agent sucht nicht mehr blind nach Studien, sondern gezielt nach Quellen die eine identifizierte Keyword-Lücke füllen können.

Alle Agents kommunizieren über Supabase als zentralen State Store. Es gibt keine direkte Agent-zu-Agent-Kommunikation.

### State Machine

Jeder Content-Eintrag durchläuft diesen Lifecycle:

```
OPPORTUNITY → RESEARCHED → DRAFTED → QA_PASSED → SCHEDULED → PUBLISHED → DISTRIBUTED
                              ↓           ↓
                          DRAFT_FAILED  REVIEW_HOLD
```

- `OPPORTUNITY`: Content Strategist hat eine Keyword-Lücke identifiziert
- Default: Alles läuft automatisch durch
- `REVIEW_HOLD`: Manuell gesetzt per Dashboard/Slack — Agent überspringt diesen Eintrag
- `DRAFT_FAILED` / QA-Score < Threshold: Wird nicht veröffentlicht, Notification an Team
- 2-Stunden-Delay zwischen QA_PASSED und PUBLISHED als Review-Fenster

### Erweiterter Datenfluss

```
┌──────────────────────────────────────────────────────────────────────┐
│                     SUPABASE (Central State Store)                   │
│                                                                      │
│  content_inventory │ Alle Seiten auf sunsideai.de mit Metadata       │
│  keywords          │ GSC-Daten + Autocomplete + Clustering           │
│  opportunities     │ Priorisierte Keyword-Lücken & Update-Kandidaten │
│  findings          │ Recherche-Ergebnisse aus RSS/Scholar            │
│  blog_posts        │ Content + Status + QA-Score                     │
│  linkedin_posts    │ Post-Text + Performance-Tracking                │
│  pipeline_config   │ Systemsteuerung                                 │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Verzeichnisstruktur

```
sunside-autopilot/
├── CLAUDE.md                      ← Diese Datei
├── PROJECT_DOCS.md                ← Projektdokumentation
├── requirements.txt               ← Python Dependencies
├── .env.example                   ← Env-Variablen Template
│
├── prompts/                       ← System Prompts (Source of Truth)
│   ├── research-agent.md          ← Prompt: Relevanzfilterung & Themenauswahl
│   ├── seo-blog-writer.md         ← Prompt: SEO-Blogbeiträge (aus Claude SEO-Projekt)
│   ├── linkedin-creator.md        ← Prompt: LinkedIn-Posts (aus Claude LinkedIn-Projekt)
│   ├── quality-gate.md            ← Prompt: Qualitätsprüfung & Scoring
│   ├── content-strategist.md      ← Prompt: Keyword-Gap-Analyse & Content-Priorisierung
│   └── CHANGELOG.md               ← Prompt-Versionshistorie
│
├── knowledge/                     ← Kontext-Dateien für die Agents (READ-ONLY Referenz)
│   ├── content-map.md             ← Alle 28+ bestehenden Blog-Posts mit Keywords & Slugs
│   ├── quellensammlung.md         ← Geprüfte Quellen, Studien, Branchenberichte
│   ├── fallstudien.md             ← Echte Kundenergebnisse (E-E-A-T Signale)
│   ├── wettbewerber-analyse.md    ← Keyword-Datenbank: 1.725 Keywords, Gaps, Wettbewerber
│   ├── design-system.md           ← Sunside AI Design System (Farben, Fonts, Spacing)
│   └── seo-heist/                 ← 20 vorbereitete Pillar-Artikel (C1-C20)
│       ├── artikel-c1-immobilienmakler-website.md
│       ├── artikel-c2-webdesign-immobilienmakler.md
│       └── ... (20 Artikel)
│
├── feeds/
│   ├── sources.yaml               ← RSS-Feeds & Scrape-Targets
│   └── used_topics.yaml           ← Bereits behandelte Themen (Deduplizierung)
│
├── agents/
│   ├── __init__.py
│   ├── content_crawler.py         ← SEO: Website-Crawl & Content-Inventur
│   ├── keyword_researcher.py      ← SEO: GSC-Daten + Autocomplete + Clustering
│   ├── content_strategist.py      ← SEO: Keyword-Lücken & Opportunities identifizieren
│   ├── researcher.py              ← Phase 1: Studien & Trends finden (mit Keyword-Fokus)
│   ├── blog_writer.py             ← Phase 2: Blog erstellen + Quality Gate
│   ├── linkedin_poster.py         ← Phase 3: LinkedIn Distribution
│   └── image_generator.py         ← Infografik-Generierung
│
├── core/
│   ├── __init__.py
│   ├── config.py                  ← Settings, Env-Variablen
│   ├── supabase_client.py         ← Supabase CRUD Operations
│   ├── claude_client.py           ← Anthropic API Wrapper
│   ├── github_client.py           ← GitHub API (Blog-Commits)
│   ├── linkedin_client.py         ← LinkedIn API v2
│   ├── gsc_client.py              ← Google Search Console API
│   ├── autocomplete_client.py     ← Google Autocomplete für Keyword-Ideen
│   └── notifier.py                ← Slack/E-Mail Notifications
│
├── templates/
│   ├── blog-post.md               ← Next.js Blog-Post Markdown Template
│   └── linkedin-post.txt          ← LinkedIn-Post Textstruktur
│
├── assets/
│   ├── blog-images/               ← SVG Blog-Header (20 Icons)
│   └── fonts/                     ← Poppins für Infografiken
│
├── scripts/
│   ├── setup_supabase.sql         ← Datenbank-Schema
│   ├── seed_feeds.py              ← Initiale Feed-Liste importieren
│   ├── initial_crawl.py           ← Einmaliger Website-Crawl zum Setup
│   └── manual_trigger.py          ← Manuelles Auslösen einzelner Agents
│
├── tests/
│   ├── test_content_crawler.py
│   ├── test_keyword_researcher.py
│   ├── test_content_strategist.py
│   ├── test_researcher.py
│   ├── test_blog_writer.py
│   ├── test_linkedin_poster.py
│   └── test_quality_gate.py
│
├── main.py                        ← Orchestrator / Entry Point
└── Dockerfile                     ← Railway Deployment
```

---

## Prompt-Dateien (prompts/)

### Warum Prompts als Dateien?

Die System Prompts sind das Herzstück der Content-Qualität. Sie stammen aus bestehenden Claude Projects (Web-UI) und werden hier als Markdown-Dateien versioniert. Das Repo ist die Source of Truth — Änderungen hier, dann in die Claude Projects zurückspiegeln.

### prompts/research-agent.md

Dieser Prompt steuert den Research Agent. Er bewertet eingehende Artikel/Studien auf Relevanz für die Zielgruppe.

**Aufgabe:** Bewerte eine Liste von Artikeln/Studien und filtere die Top-Findings heraus.

**Input:** JSON-Array von Artikeln mit Titel, Abstract/Snippet, Quelle, Datum.

**Output:** JSON-Array der Top 10-15 Findings, jeweils mit:
- `title`: Artikeltitel
- `source`: Quellenname + URL
- `key_insight`: Kernaussage in 1-2 Sätzen (Deutsch)
- `stats`: Relevante Zahlen/Statistiken (falls vorhanden)
- `relevance_score`: 1-10 (wie relevant für deutsche Immobilienmakler)
- `blog_angle`: Vorgeschlagener Blog-Winkel
- `target_keyword`: SEO-Keyword-Vorschlag

**Filterkriterien:**
- Nur Inhalte die für deutsche Immobilienmakler, Sachverständige oder PropTech relevant sind
- Bevorzuge Studien mit konkreten Zahlen und Statistiken
- Themen: KI/Automatisierung, Digitalisierung, Immobilienmarkt, Kundengewinnung, SEO, Marketing
- Ignoriere rein US/UK-spezifische Inhalte ohne Übertragbarkeit auf DE-Markt
- Prüfe Deduplizierung gegen bereits behandelte Themen

**Wichtig:** Der Output muss valides JSON sein, kein Markdown, keine Codeblöcke.

---

### prompts/seo-blog-writer.md

**PLATZHALTER — Hier die Instructions aus dem bestehenden Claude SEO-Projekt einfügen.**

Dieser Prompt enthält alle Regeln für die Blog-Erstellung. Der Blog Writer Agent lädt zusätzlich folgende Knowledge-Base-Dateien als Kontext:

- `knowledge/content-map.md` → Interne Verlinkung: Welche Posts existieren mit welchen Slugs?
- `knowledge/quellensammlung.md` → Welche Studien/Quellen sollen bevorzugt zitiert werden?
- `knowledge/fallstudien.md` → Welche Kundenergebnisse können als Praxisbelege dienen?
- `knowledge/wettbewerber-analyse.md` → Auf welche Keywords zielen Wettbewerber? (Differenzierung)

**Der Agent sendet NICHT alle Dateien auf einmal** (zu viele Tokens). Stattdessen:
1. Aus `content-map.md`: Nur die 5-8 thematisch passenden Posts für interne Links
2. Aus `quellensammlung.md`: Nur die 2-3 relevantesten Quellen für das Thema
3. Aus `fallstudien.md`: Nur die passende Fallstudie (oder keine, wenn nicht thematisch)
4. Aus `wettbewerber-analyse.md`: Nur die Keywords der Kategorie + Wettbewerber-Positionen
- Tonalität und Ansprache (Du-Form, professionell aber nahbar)
- SEO-Struktur (H1, H2, H3, Meta-Description, Slug)
- Interne Verlinkung auf andere sunsideai.de Seiten
- CTA-Platzierung (Kontaktformular, Leistungsseite)
- Mindestlänge (1.500-2.000 Wörter)
- Keyword-Dichte und semantische Varianten
- Bildplatzierung und Alt-Tags
- Sunside AI Brand Voice

**Erwarteter Input vom Agent:**
```
Thema: {finding.title}
Kernaussage: {finding.key_insight}
Statistiken: {finding.stats}
Quelle: {finding.source}
Ziel-Keyword: {finding.target_keyword}
Blog-Winkel: {finding.blog_angle}
```

**Erwarteter Output:** Vollständiger Blogbeitrag als Markdown mit Frontmatter:
```markdown
---
title: "..."
description: "..."
slug: "..."
date: "YYYY-MM-DD"
author: "Paul Probodziak"
category: "..."
image: "/images/blog/blog-{icon}.png"
readingTime: "X Min Lesezeit"
---

# Blogtitel

Inhalt...
```

---

### prompts/linkedin-creator.md

**PLATZHALTER — Hier die Instructions aus dem bestehenden Claude LinkedIn-Projekt einfügen.**

Dieser Prompt generiert LinkedIn-Post-Texte basierend auf einem veröffentlichten Blogbeitrag.

**Richtlinien:**
- LinkedIn-optimierte Textlänge (1.200-1.800 Zeichen)
- Hook in den ersten 2 Zeilen (vor "...mehr anzeigen")
- Storytelling-Ansatz: Problem → Lösung → CTA
- 3-5 relevante Hashtags (#Immobilien #KI #PropTech etc.)
- Emoji-Einsatz: sparsam, professionell
- CTA: Link zum Blogbeitrag am Ende
- Verfasser-Perspektive: Paul Probodziak, Co-Founder Sunside AI
- Zielgruppe: Immobilienmakler & Unternehmer auf LinkedIn

**Erwarteter Input:**
```
Blog-Titel: {blog.title}
Blog-URL: https://sunsideai.de/blog/{blog.slug}
Kernaussagen: {blog.key_points}
Statistiken: {blog.stats}
```

**Erwarteter Output:** Reiner Text (kein Markdown), bereit zum Posten.

---

### prompts/quality-gate.md

Dieser Prompt prüft einen erstellten Blogbeitrag auf Qualität.

**Aufgabe:** Bewerte den Blogbeitrag anhand folgender Kriterien und vergib einen Score von 1-10.

**Prüfkriterien:**
1. **Faktische Korrektheit (0-2 Punkte):** Sind Zahlen/Aussagen plausibel? Keine Halluzinationen?
2. **SEO-Qualität (0-2 Punkte):** Keyword im Titel, H2s, Meta-Description? Interne Links vorhanden?
3. **Lesbarkeit (0-2 Punkte):** Flüssiger Text, keine KI-typischen Phrasen ("In der heutigen Zeit...", "Es ist wichtig zu beachten...")?
4. **Relevanz (0-2 Punkte):** Mehrwert für Immobilienmakler erkennbar? Praxisbezug?
5. **Brand-Konsistenz (0-2 Punkte):** Sunside AI Tonalität? CTA vorhanden? Richtige Ansprache?

**Typische KI-Phrasen die zu Punktabzug führen:**
- "In der heutigen digitalen Welt..."
- "Es lässt sich festhalten, dass..."
- "Nicht zuletzt sei erwähnt..."
- "Es ist wichtig zu beachten..."
- "Zusammenfassend lässt sich sagen..."
- Übermäßiger Gebrauch von "darüber hinaus", "grundsätzlich", "letztendlich"

**Output:** Valides JSON:
```json
{
  "score": 8.5,
  "passed": true,
  "feedback": {
    "factual": {"score": 2, "notes": "..."},
    "seo": {"score": 1.5, "notes": "..."},
    "readability": {"score": 2, "notes": "..."},
    "relevance": {"score": 1.5, "notes": "..."},
    "brand": {"score": 1.5, "notes": "..."}
  },
  "suggestions": ["...", "..."],
  "critical_issues": []
}
```

---

### prompts/content-strategist.md

Dieser Prompt analysiert die SEO-Daten und identifiziert Content-Opportunities.

**Aufgabe:** Analysiere das Content Inventory und die Keyword-Daten und erstelle eine priorisierte Liste von Content-Opportunities.

**Input:**
- Content Inventory (alle bestehenden Seiten mit Keywords, Wortanzahl, Datum)
- GSC Keyword-Daten (Impressions, Clicks, CTR, Position)
- Google Autocomplete Keyword-Vorschläge
- Bereits geplante/erstellte Themen aus der Pipeline

**Opportunity-Typen die erkannt werden sollen:**

1. **Keyword Gap (Priorität: HOCH):** Keywords mit >100 Impressions/Monat in GSC aber kein dedizierter Beitrag. Beispiel: "ki telefonassistent immobilienmakler" hat 500 Impressions, rankt auf Position 15, aber es gibt keinen spezifischen Post dazu.

2. **Low-Hanging Fruit (Priorität: HOCH):** Keywords auf Position 5-15 mit hohen Impressions. Ein gezielter Blogbeitrag oder Content-Update kann diese auf Seite 1 bringen.

3. **CTR-Optimierung (Priorität: MITTEL):** Seiten mit hohen Impressions aber CTR < 3%. Hier muss kein neuer Content erstellt werden — nur Meta-Title und Meta-Description optimiert werden.

4. **Content Refresh (Priorität: MITTEL):** Bestehende Beiträge älter als 6 Monate die noch Traffic bringen. Update mit aktuellen Zahlen und neuen Studien.

5. **Themen-Cluster (Priorität: NIEDRIG):** Long-Tail Keywords die sich zu einem neuen Pillar-Content bündeln lassen.

**Output:** Valides JSON-Array, sortiert nach Priorität:
```json
[
  {
    "type": "keyword_gap",
    "priority": "HIGH",
    "target_keyword": "ki telefonassistent immobilienmakler",
    "search_volume_indicator": "high",
    "current_position": 15,
    "impressions": 500,
    "action": "NEW_POST",
    "suggested_title": "KI-Telefonassistent für Immobilienmakler: So verlierst du keinen Anruf mehr",
    "related_keywords": ["anrufbeantworter ki makler", "telefonassistenz immobilien"],
    "existing_content_to_link": ["/blog/ki-immobilienmakler", "/leistungen"],
    "research_query": "AI phone assistant real estate agent study"
  },
  {
    "type": "ctr_optimization",
    "priority": "MEDIUM",
    "target_url": "/blog/chatbot-immobilienmakler",
    "current_ctr": 2.1,
    "impressions": 1200,
    "action": "UPDATE_META",
    "suggested_title": "...",
    "suggested_description": "..."
  }
]
```

**Wichtige Regeln:**
- Maximal 10 Opportunities pro Woche generieren
- Nie mehr als 2 Content Refreshes pro Woche (Fokus auf neuen Content)
- CTR-Optimierungen als separate Aufgaben behandeln (kein neuer Blog nötig)
- Immer prüfen ob ein ähnliches Thema in den letzten 30 Tagen behandelt wurde
- Keyword-Clustering: Ähnliche Keywords zu einer Opportunity bündeln, nicht einzeln behandeln

---

## Knowledge Base (knowledge/)

Diese Dateien enthalten den gesamten Unternehmens- und SEO-Kontext. Agents laden sie als Referenzmaterial — sie werden NICHT an die Claude API als System Prompt geschickt (zu groß), sondern selektiv als User-Kontext je nach Bedarf.

### knowledge/content-map.md

**Quelle:** Claude SEO-Projekt
**Inhalt:** Vollständige Übersicht aller 28+ bestehenden Blog-Posts mit Haupt-Keywords, Neben-Keywords, Slugs, Zusammenfassungen und Kategorien.
**Genutzt von:** Content Strategist (Duplikat-Check), Blog Writer (interne Verlinkung), Content Crawler (Abgleich mit Live-Daten)

**Beispiel-Eintrag:**
```
Artikel 1:
- Titel: KI Telefonassistenz für Immobilienmakler
- Slug: ki-telefonassistenz-immobilienmakler
- Haupt-Keyword: KI Telefonassistenz Immobilienmakler
- Neben-Keywords: Telefonassistenz Makler, KI Erreichbarkeit Immobilien, Voicebot Makler
```

### knowledge/quellensammlung.md

**Quelle:** Claude SEO-Projekt
**Inhalt:** Kuratierte Quellen für Research — Branchenberichte (VDIV, ZIA/EY), Fachmedien (Haufe, OMR), wissenschaftliche Studien (ScienceDirect), Praxisbeispiele (SWR), Wettbewerber-Referenzen.
**Genutzt von:** Research Agent (Quellen-Priorisierung), Blog Writer (Quellenangaben im Text)

**Regeln aus der Quellensammlung:**
- IMMER Primärquellen bevorzugen (Studien, Verbände, offizielle Berichte)
- Keine vagen "Studien zeigen" — konkret nennen woher Zahlen stammen
- Bei neuen Quellen: Am Ende des Artikels Vorschlag für Aufnahme in die Quellensammlung

### knowledge/fallstudien.md

**Quelle:** Claude SEO-Projekt
**Inhalt:** Echte Kundenergebnisse als E-E-A-T Signale (Experience). Streil Immobilien (19 Leads/4 Wochen, 15,8% Konversion), Werneburg Immobilien (30+ Leads/4 Wochen, 12% Konversion).
**Genutzt von:** Blog Writer (Praxisbelege in Artikeln)

**Regeln:**
- NICHT in jedem Artikel verwenden — nur wo thematisch passend
- Variieren welche Fallstudie genutzt wird
- KEINE Preise nennen (Unternehmensrichtlinie)
- Natürlich einbauen, nicht als Werbe-Liste

### knowledge/wettbewerber-analyse.md

**Quelle:** Sistrix Domain-History-Export (März 2026)
**Inhalt:** 1.725 relevante Keywords, aufgeteilt in Kategorien (Website/Webdesign 62 KW, Marketing/SEO 31 KW, Leads/Akquise 50 KW, Software/CRM 87 KW, etc.). Pro Keyword: Suchvolumen, beste Position, rankende Wettbewerber.
**Genutzt von:** Content Strategist (Keyword-Gaps identifizieren), Research Agent (Suchqueries ableiten)

**Schlüsselzahlen:**
- Sunside AI rankt aktuell für 41 Keywords
- 206 Keyword-Gaps mit SV ≥ 100 (Wettbewerber in Top 10, Sunside nicht)
- Stärkste Wettbewerber: immoxxl.de (5.000 KW), onoffice.com (5.000 KW), propstack.de (4.973 KW)
- Sunside AI's stärkste Position: Pos. 3 ("wie können makler ihre prozesse digitalisieren?")

**Die 6 Wettbewerber:**
| Wettbewerber | Keywords | Fokus |
|---|---|---|
| immoxxl.de | 5.000 | Makler-Website, Marketing, Ausbildung, Software |
| onoffice.com | 5.000 | CRM/Software, Regulierung, Maklerrecht |
| propstack.de | 4.973 | CRM, Software, Immobilien-Tech |
| wordliner.com | 1.501 | Webdesign, Homepage, SEO für Makler |
| bottimmo.com | 901 | Marketing, Leads, Lead-Generierung |
| screenwork.de | 617 | Webdesign, CMS, Makler-Websites |

**Größte Chancen (Content Strategist soll hier priorisieren):**
1. Website/Webdesign — SV 590+ Keywords, Wettbewerber mit altem Content
2. Marketing/Leads — bottimmo + immoxxl teilen den Markt
3. Software/CRM — onOffice + Propstack führen, neutrale Alternative möglich
4. KI & Automatisierung — Nur 5 Keywords bei Wettbewerbern, Sunside AI's Kernthema

### knowledge/design-system.md

**Inhalt:** Sunside AI Design System für konsistente visuelle Outputs.
**Genutzt von:** Image Generator (Blog-Header, LinkedIn-Infografiken)

**Kernwerte:**
- Primary: `#7B3ABF`
- Secondary: `#5E2C8C`
- Tertiary: `#9A40C9`
- Neutral/Background: `#0F0A15`
- Font: Inter (Headlines, Body, Labels)
- Theme: "Fidelity", Dark Mode

### knowledge/seo-heist/ (20 Artikel)

**Quelle:** Claude SEO-Projekt, "Competitive Research"
**Inhalt:** 20 vorbereitete Pillar-Artikel (C1-C20) die gezielt auf Wettbewerber-Keywords abzielen. Frontmatter mit Keywords, Slugs, Meta-Descriptions. Vollständig geschrieben, bereit zum Deployment.
**Genutzt von:** Blog Writer (als Vorlagen/Referenz für Stil und Struktur), Content Strategist (diese Keywords als "planned" markieren)

**Themen-Mapping:**
| Artikel | Keyword | SV |
|---|---|---|
| C1 | Immobilienmakler Website | 590 |
| C2 | Webdesign Immobilienmakler | 320 |
| C3 | Immobilienmakler Homepage erstellen | 110 |
| C4 | Beste Immobilienmakler Website | 90 |
| C5 | Landingpage Immobilienmakler | 90 |
| C6 | Online Marketing Immobilienmakler | 170 |
| C7 | Akquise Immobilienmakler | 320 |
| C8 | Immobilien Leads | 110 |
| C9 | Immobilien Leads kaufen | 90 |
| C10 | Marketing für Immobilien | 320 |
| C11 | Immobilienmakler Software | 390 |
| C12 | CRM Immobilienmakler | 170 |
| C13 | Maklersoftware Vergleich | 320 |
| C14 | Immobilienbewertung Software | 210 |
| C15 | Immobilienmakler Kundengewinnung | 170 |
| C16 | Alleinauftrag Makler | 480 |
| C17 | Immobilienmakler Wettbewerbsvorteil | 110 |
| C18 | Immobilienmakler Kundenservice | 170 |
| C19 | Immobilienmakler Selbstständig | 390 |
| C20 | Diskrete Immobilienvermarktung | 140 |

**Wichtig:** Diese Artikel sind als SEO-Heist-Strategie konzipiert — sie greifen direkt Keywords an, für die Wettbewerber ranken. Der Content Strategist soll diese als "PLANNED" kennen und nicht erneut als Opportunity vorschlagen.

---

## Agent-Implementierung

### agents/content_crawler.py

**Zeitplan:** Sonntag 18:00 Uhr (erster Agent im Zyklus)
**Dauer:** ca. 2-3 Minuten

**Aufgabe:** Crawlt sunsideai.de und erstellt/aktualisiert ein vollständiges Content Inventory in Supabase.

**Ablauf:**
1. Starte bei `https://sunsideai.de/sitemap.xml` (oder `/sitemap-0.xml` je nach Next.js Config)
2. Extrahiere alle URLs aus der Sitemap
3. Für jede URL die seit dem letzten Crawl neu oder geändert ist:
   a. HTTP GET auf die Seite
   b. Parse HTML mit BeautifulSoup
   c. Extrahiere: Title-Tag, Meta-Description, H1, alle H2s, Wortanzahl des Body-Texts, interne Links, Bilder (Alt-Tags), Canonical URL, Veröffentlichungsdatum (aus Frontmatter oder Schema)
4. Speichere/Update in Supabase `content_inventory`-Tabelle
5. Markiere Seiten die aus der Sitemap verschwunden sind als `deleted`
6. Berechne Content-Alter (Tage seit Veröffentlichung) für Refresh-Kandidaten

**Spezialbehandlung für Blog-Posts:**
- Erkenne Blog-Posts an URL-Pattern `/blog/{slug}`
- Extrahiere zusätzlich: Kategorie, Lesezeit, Autor
- Identifiziere das Haupt-Keyword aus Title + H1 + erster H2

**Erstmaliger Crawl (Setup):**
- `scripts/initial_crawl.py` führt einen vollständigen Crawl durch
- Danach nur noch inkrementelle Updates (neue/geänderte Seiten)

**Fehlerbehandlung:**
- 404/500 auf einer Seite → Loggen, als `error` markieren
- Sitemap nicht erreichbar → Fallback auf letzte bekannte URL-Liste
- Rate Limiting: Max 2 Requests/Sekunde gegen eigene Seite

---

### agents/keyword_researcher.py

**Zeitplan:** Sonntag 19:00 Uhr (nach Content Crawler)
**Dauer:** ca. 5-8 Minuten

**Aufgabe:** Sammelt Keyword-Daten aus Google Search Console und ergänzt sie mit Autocomplete-Vorschlägen.

**Ablauf:**

**Schritt 1 — Google Search Console Daten abrufen:**
1. Authentifiziere via Google Service Account (JSON Key)
2. API-Call: `searchAnalytics.query` für die letzten 28 Tage
3. Dimensionen: `query`, `page`
4. Für jedes Keyword erfassen: Impressions, Clicks, CTR, durchschnittliche Position
5. Filter: Nur Keywords mit >= 10 Impressions (Noise entfernen)
6. Speichere in Supabase `keywords`-Tabelle mit Timestamp

```python
# GSC API Call Beispiel
from googleapiclient.discovery import build
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    'gsc-credentials.json',
    scopes=['https://www.googleapis.com/auth/webmasters.readonly']
)
service = build('searchconsole', 'v1', credentials=credentials)

response = service.searchanalytics().query(
    siteUrl='sc-domain:sunsideai.de',
    body={
        'startDate': '2026-03-06',
        'endDate': '2026-04-03',
        'dimensions': ['query', 'page'],
        'rowLimit': 1000
    }
).execute()
```

**Schritt 2 — Google Autocomplete erweitern:**
1. Nimm die Top-20 performenden Keywords aus GSC
2. Für jedes Keyword: Autocomplete-Anfrage an `https://suggestqueries.google.com/complete/search?client=firefox&hl=de&q={keyword}`
3. Sammle verwandte Long-Tail Vorschläge
4. Zusätzliche Seed-Keywords abfragen:
   - "immobilienmakler ki"
   - "chatbot immobilien"
   - "ki für makler"
   - "immobilien automatisierung"
   - "seo immobilienmakler"
   - "telefonassistent immobilien"
5. Speichere neue Keywords in Supabase (merge, keine Duplikate)

**Schritt 3 — Keyword-Clustering via Claude:**
1. Sende alle Keywords an Claude API
2. Claude gruppiert sie in thematische Cluster
3. Pro Cluster: Haupt-Keyword + Related Keywords identifizieren
4. Suchintent bestimmen: informational, transactional, navigational

**Rate Limits:**
- GSC API: 1.200 Queries/Minute (kein Problem)
- Google Autocomplete: Max 10 Requests/Minute (Throttle!)

---

### agents/content_strategist.py

**Zeitplan:** Sonntag 19:30 Uhr (nach Keyword Researcher)
**Dauer:** ca. 3-5 Minuten

**Aufgabe:** Vergleicht Keyword-Daten mit Content Inventory und identifiziert die besten Content-Opportunities für die kommende Woche.

**Ablauf:**
1. Lade Content Inventory aus Supabase (`content_inventory`)
2. Lade Keyword-Daten aus Supabase (`keywords`)
3. Lade bereits geplante Themen (`blog_posts` mit Status != PUBLISHED)
4. Lade historische Themen der letzten 30 Tage
5. Erstelle Mapping: Welches Keyword → Welche Seite rankt dafür?
6. Sende alles an Claude API mit `prompts/content-strategist.md` als System Prompt
7. Claude identifiziert und priorisiert Opportunities:
   - **Keyword Gaps:** Impressions vorhanden, kein Content
   - **Low-Hanging Fruits:** Position 5-15, ein Push könnte auf Seite 1 bringen
   - **CTR-Optimierungen:** Hohe Impressions, niedrige CTR (nur Meta-Update nötig)
   - **Content Refreshes:** Alte Posts mit Traffic-Potenzial
8. Speichere Top-10 Opportunities in Supabase `content_opportunities`
9. Für jede `NEW_POST` Opportunity: Erstelle einen `research_query` der dem Research Agent sagt wonach er suchen soll

**Priorisierungs-Logik:**
```
Score = (Impressions × 0.4) + (Position_Potenzial × 0.3) + (Wettbewerb_niedrig × 0.2) + (Brand_Fit × 0.1)
```

- `Impressions`: Normalisiert 0-10 basierend auf relativem Volumen
- `Position_Potenzial`: Keywords auf Pos 5-15 bekommen höchsten Score
- `Wettbewerb_niedrig`: Long-Tail Keywords > Short-Tail
- `Brand_Fit`: Passt das Thema zu Sunside AI's Kernleistungen?

**CTR-Optimierungen als Sofort-Maßnahme:**
Wenn der Strategist CTR-Probleme findet, erstellt er direkt optimierte Meta-Titles und Descriptions. Diese werden als separater Task in `content_opportunities` mit `action: UPDATE_META` gespeichert. Der Blog Writer Agent kann diese ohne neuen Blogpost direkt umsetzen (Git Push nur für Frontmatter-Update).

---

### agents/researcher.py (erweitert)

**Zeitplan:** Sonntag 20:00 Uhr
**Dauer:** ca. 5-10 Minuten

**Erweiterung gegenüber Basis-Version:**
Der Research Agent bekommt jetzt zusätzlich die Content Opportunities als Input. Er sucht nicht mehr blind, sondern gezielt.

**Ablauf:**
1. Lade offene Opportunities mit `action: NEW_POST` aus Supabase
2. Lade `feeds/sources.yaml` — enthält alle RSS-URLs und Scrape-Targets
3. **Gezielter Modus:** Für jede Opportunity:
   a. Nutze den `research_query` als Suchterm für Semantic Scholar
   b. Durchsuche RSS-Feed-Archive nach passenden Artikeln
   c. Finde Studien die das Keyword-Thema mit Zahlen untermauern
4. **Ungezielter Modus:** Parallel dazu normales Feed-Scraping für Trend-Themen die nicht in den GSC-Daten auftauchen (z.B. brandneue Technologien)
5. Sende beides an Claude API mit `prompts/research-agent.md` als System Prompt
6. Claude bewertet Relevanz und verknüpft Findings mit Opportunities
7. Für Top-Findings: `web_fetch` auf Original-Artikel für Volltext-Extraktion
8. Speichere Findings in Supabase `findings`-Tabelle mit:
   - Status `RESEARCHED`
   - `opportunity_id` (falls mit einer Opportunity verknüpft)
   - `target_keyword` (aus Opportunity übernommen)
9. Aktualisiere `feeds/used_topics.yaml` für Deduplizierung

**Fehlerbehandlung:**
- Feed nicht erreichbar → Loggen, überspringen, nächste Woche erneut versuchen
- Keine relevanten Findings → Notification an Team, keine Blog-Erstellung diese Woche
- API-Fehler → 3x Retry mit exponential Backoff

**Rate Limits beachten:**
- Semantic Scholar: 100 Requests/Sekunde (großzügig)
- Claude API: Je nach Plan, Batching wenn nötig
- RSS Feeds: 1 Request pro Feed, kein Throttling nötig

---

### agents/blog_writer.py

**Zeitplan:** Mo-Fr, 06:00 Uhr
**Dauer:** ca. 3-5 Minuten pro Post

**Ablauf:**
1. Lade nächstes Finding mit Status `RESEARCHED` aus Supabase (ältestes zuerst, Opportunity-verknüpfte bevorzugt)
2. Prüfe `pipeline_config`: Ist `auto_publish` aktiv? Ist die Pipeline pausiert?
3. Prüfe ob Thema auf `hold_topics` steht → Falls ja, überspringen
4. **NEU — Content-Kontext laden:**
   a. Lade Content Inventory aus Supabase (alle bestehenden Seiten)
   b. Identifiziere 3-5 passende interne Link-Ziele für das Thema
   c. Lade verknüpfte Opportunity (falls vorhanden) mit target_keyword + related_keywords
   d. Prüfe ob ähnlicher Content existiert → Falls ja, differenzierenden Winkel sicherstellen
5. Erstelle Blog-Post via Claude API mit `prompts/seo-blog-writer.md` als System Prompt
   - **Zusätzlich im User-Prompt:** Content Inventory Kontext + Link-Ziele + Keyword-Daten
6. Parse den Output: Frontmatter extrahieren, Markdown validieren
7. **Interne Links verifizieren:** Prüfe ob alle internen Links im Content Inventory existieren
8. Wähle passendes Blog-Header-Image aus `assets/blog-images/` basierend auf Kategorie
9. **Quality Gate:** Zweiter Claude-Call mit `prompts/quality-gate.md`
   - Score ≥ Threshold (default 7.5) → Status `QA_PASSED`
   - Score < Threshold → Status `QA_FAILED`, Notification an Team
10. Speichere Blog-Content und QA-Ergebnis in Supabase `blog_posts`-Tabelle
11. Setze `scheduled_at` = jetzt + 2 Stunden (Review-Fenster)
12. Sende Morning Digest Notification

**Erweiterter User-Prompt an Claude:**
```
Thema: {finding.title}
Kernaussage: {finding.key_insight}
Statistiken: {finding.stats}
Quelle: {finding.source}
Ziel-Keyword: {opportunity.target_keyword}
Verwandte Keywords (natürlich einbauen): {opportunity.related_keywords}
Blog-Winkel: {finding.blog_angle}

INTERNE VERLINKUNG — Baue 3-5 dieser Links natürlich in den Text ein:
{content_inventory_links}

BESTEHENDER CONTENT ZU DIESEM THEMA — Stelle sicher, dass dein Beitrag einen 
neuen Winkel bietet und nicht redundant ist:
{existing_similar_content}
```

**Nach Ablauf des Review-Fensters (08:00):**
1. Prüfe ob Post noch `QA_PASSED` ist (nicht manuell auf `REVIEW_HOLD` gesetzt)
2. Git-Commit: Erstelle Markdown-Datei im Blog-Repo via GitHub API
3. Push triggert Netlify-Deploy automatisch
4. Status → `PUBLISHED`, `published_at` setzen

**Blog-Post Dateiformat im Repo:**
```
src/content/blog/{slug}.md
```

**Kategorie → Icon Mapping:**
```yaml
KI & Automatisierung: blog-ki
Chatbot: blog-chatbot
Telefonassistenz: blog-telefon
SEO & Sichtbarkeit: blog-seo
Immobilienmarketing: blog-immobilie
Analytics & Daten: blog-analytics
Automatisierung: blog-automatisierung
E-Mail Marketing: blog-email
Webdesign: blog-website
Datenschutz & Recht: blog-datenschutz
Effizienz: blog-speed
Teameffizienz: blog-team
Prozessoptimierung: blog-schluessel
Zeitmanagement: blog-zeit
Umsatz & Wachstum: blog-umsatz
Marketing: blog-marketing
Exposé & Content: blog-expose
Bewertung: blog-bewertung
Zielgruppen: blog-zielgruppe
Integration: blog-vernetzung
```

---

### agents/linkedin_poster.py

**Zeitplan:** Mo-Fr, 10:00 Uhr (nach Auto-Publish des Blogs)
**Dauer:** ca. 2-3 Minuten

**Ablauf:**
1. Lade alle Blog-Posts mit Status `PUBLISHED` die noch nicht `DISTRIBUTED` sind
2. Für jeden Post:
   a. Generiere LinkedIn-Text via Claude API mit `prompts/linkedin-creator.md`
   b. Generiere Infografik via `image_generator.py`
   c. Lade Infografik hoch via LinkedIn Image API
   d. Erstelle LinkedIn UGC Post mit Text + Bild + Link
   e. Status → `DISTRIBUTED`
3. Speichere LinkedIn-Post-ID in Supabase für späteres Performance-Tracking

**LinkedIn API Setup:**
- OAuth 2.0 App in LinkedIn Developer Portal
- Scopes: `w_member_social`, `r_liteprofile`
- Access Token muss alle 60 Tage erneuert werden → Reminder einbauen
- Posten auf Pauls persönlichem Profil (mehr Reichweite als Company Page)

**LinkedIn API Post-Struktur:**
```json
{
  "author": "urn:li:person:{PERSON_ID}",
  "lifecycleState": "PUBLISHED",
  "specificContent": {
    "com.linkedin.ugc.ShareContent": {
      "shareCommentary": {"text": "{generierter_text}"},
      "shareMediaCategory": "IMAGE",
      "media": [{
        "status": "READY",
        "media": "{uploaded_image_urn}",
        "title": {"text": "{blog_title}"}
      }]
    }
  },
  "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
}
```

---

### agents/image_generator.py

Generiert LinkedIn-Infografiken im Sunside AI Stil.

**Input:** Blog-Titel, Kategorie, 3 Key Bullets, Blog-URL
**Output:** PNG 1200x1200px

**Design-Specs (aus knowledge/design-system.md):**
- Hintergrund: Blog-Header-Image (Neutral `#0F0A15`, Dot Grid, Glow Icon)
- Glow-Farbe: Primary `#7B3ABF` / Tertiary `#9A40C9`
- Gradient-Overlay im unteren Bereich (60% des Bildes)
- Kategorie-Tag (Secondary `#5E2C8C`, Roundedness 2)
- Titel in Inter Bold (oder Poppins als Fallback), 48px, Weiß
- 3 Bullet Points in Inter Regular, 30px, Weiß 80% Opacity
- Bottom Bar: "SUNSIDE AI" links, "sunsideai.de/blog >>" rechts
- Separator Line in Primary 15% Opacity
- Theme: Dark Mode, "Fidelity"

**Fonts:** Inter bevorzugt (Design System), Poppins als Fallback (lokal in `assets/fonts/`)

---

## Datenbank-Schema (Supabase)

### Tabelle: content_inventory

```sql
CREATE TABLE content_inventory (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  url TEXT UNIQUE NOT NULL,
  page_type TEXT CHECK (page_type IN ('blog', 'landing', 'service', 'legal', 'other')),
  title TEXT,
  meta_description TEXT,
  h1 TEXT,
  h2s JSONB DEFAULT '[]',
  word_count INT,
  internal_links JSONB DEFAULT '[]',
  primary_keyword TEXT,
  category TEXT,
  published_at TIMESTAMPTZ,
  last_crawled_at TIMESTAMPTZ DEFAULT now(),
  content_age_days INT GENERATED ALWAYS AS (
    EXTRACT(DAY FROM now() - published_at)
  ) STORED,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'deleted', 'error')),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_content_inventory_type ON content_inventory(page_type);
CREATE INDEX idx_content_inventory_keyword ON content_inventory(primary_keyword);
```

### Tabelle: keywords

```sql
CREATE TABLE keywords (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  keyword TEXT NOT NULL,
  source TEXT CHECK (source IN ('gsc', 'autocomplete', 'manual', 'clustering')),
  impressions INT DEFAULT 0,
  clicks INT DEFAULT 0,
  ctr FLOAT DEFAULT 0,
  avg_position FLOAT,
  ranking_page TEXT,
  cluster_name TEXT,
  search_intent TEXT CHECK (search_intent IN ('informational', 'transactional', 'navigational')),
  period_start DATE,
  period_end DATE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(keyword, period_start)
);

CREATE INDEX idx_keywords_impressions ON keywords(impressions DESC);
CREATE INDEX idx_keywords_position ON keywords(avg_position);
CREATE INDEX idx_keywords_cluster ON keywords(cluster_name);
```

### Tabelle: content_opportunities

```sql
CREATE TABLE content_opportunities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  status TEXT DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'IN_PROGRESS', 'COMPLETED', 'SKIPPED')),
  type TEXT CHECK (type IN ('keyword_gap', 'low_hanging_fruit', 'ctr_optimization', 'content_refresh', 'topic_cluster')),
  priority TEXT CHECK (priority IN ('HIGH', 'MEDIUM', 'LOW')),
  priority_score FLOAT,
  target_keyword TEXT,
  related_keywords JSONB DEFAULT '[]',
  action TEXT CHECK (action IN ('NEW_POST', 'UPDATE_META', 'REFRESH_CONTENT', 'CREATE_CLUSTER')),
  suggested_title TEXT,
  research_query TEXT,
  existing_url TEXT,
  current_position FLOAT,
  impressions INT,
  current_ctr FLOAT,
  suggested_meta_title TEXT,
  suggested_meta_description TEXT,
  existing_content_to_link JSONB DEFAULT '[]',
  week_of DATE,
  created_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);

CREATE INDEX idx_opportunities_status ON content_opportunities(status);
CREATE INDEX idx_opportunities_priority ON content_opportunities(priority_score DESC);
CREATE INDEX idx_opportunities_week ON content_opportunities(week_of);
```

### Tabelle: findings

```sql
CREATE TABLE findings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  status TEXT DEFAULT 'RESEARCHED' CHECK (status IN ('RESEARCHED', 'USED', 'SKIPPED')),
  opportunity_id UUID REFERENCES content_opportunities(id),
  title TEXT NOT NULL,
  source_name TEXT,
  source_url TEXT,
  key_insight TEXT,
  stats TEXT,
  relevance_score FLOAT,
  blog_angle TEXT,
  target_keyword TEXT,
  raw_content TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  used_at TIMESTAMPTZ
);
```

### Tabelle: blog_posts

```sql
CREATE TABLE blog_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  status TEXT DEFAULT 'DRAFTED' CHECK (status IN (
    'DRAFTED', 'QA_PASSED', 'QA_FAILED', 'REVIEW_HOLD', 'SCHEDULED', 'PUBLISHED'
  )),
  finding_id UUID REFERENCES findings(id),
  opportunity_id UUID REFERENCES content_opportunities(id),
  title TEXT,
  slug TEXT UNIQUE,
  meta_description TEXT,
  content TEXT,
  category TEXT,
  image_filename TEXT,
  target_keyword TEXT,
  related_keywords JSONB DEFAULT '[]',
  internal_links_used JSONB DEFAULT '[]',
  qa_score FLOAT,
  qa_feedback JSONB,
  scheduled_at TIMESTAMPTZ,
  published_at TIMESTAMPTZ,
  github_commit_sha TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

### Tabelle: linkedin_posts

```sql
CREATE TABLE linkedin_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  status TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'POSTED', 'FAILED')),
  blog_post_id UUID REFERENCES blog_posts(id),
  post_text TEXT,
  image_url TEXT,
  linkedin_post_id TEXT,
  posted_at TIMESTAMPTZ,
  impressions INT,
  clicks INT,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

### Tabelle: pipeline_config

```sql
CREATE TABLE pipeline_config (
  key TEXT PRIMARY KEY,
  value JSONB NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Default Config einfügen:
INSERT INTO pipeline_config (key, value) VALUES
  ('qa_threshold', '7.5'),
  ('auto_publish', 'true'),
  ('delay_hours', '2'),
  ('paused', 'false'),
  ('hold_topics', '[]'),
  ('max_posts_per_week', '5'),
  ('linkedin_auto_post', 'true'),
  ('notification_channel', '"slack"');
```

---

## Umgebungsvariablen (.env)

```bash
# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...

# GitHub (Blog Repo)
GITHUB_TOKEN=ghp_...
GITHUB_REPO=SunsideAI/SunsideAI_Website
GITHUB_BRANCH=main

# LinkedIn
LINKEDIN_ACCESS_TOKEN=AQ...
LINKEDIN_PERSON_ID=...

# Google Search Console
GSC_SERVICE_ACCOUNT_JSON=gsc-credentials.json
GSC_SITE_URL=sc-domain:sunsideai.de

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
# oder
BREVO_API_KEY=...
NOTIFICATION_EMAIL=paul@sunsideai.de

# Config
TIMEZONE=Europe/Berlin
```

---

## RSS-Feed Quellen (feeds/sources.yaml)

```yaml
feeds:
  # --- Immobilienbranche DE ---
  - name: "IZ Immobilien Zeitung"
    url: "https://www.iz.de/rss/feed.xml"
    category: "immobilien"
    
  - name: "Haufe Immobilien"
    url: "https://www.haufe.de/immobilien/rss_332.xml"
    category: "immobilien"

  - name: "ImmoCompact"
    url: "https://www.immocompact.de/rss.xml"
    category: "immobilien"

  - name: "AIZ Immobilienmagazin"
    url: "https://www.aiz.de/feed"
    category: "immobilien"

  # --- KI & Tech DE ---
  - name: "t3n"
    url: "https://t3n.de/rss.xml"
    category: "tech"
    filter_keywords: ["KI", "AI", "Immobilien", "Automatisierung", "ChatGPT", "Chatbot"]

  - name: "Heise"
    url: "https://www.heise.de/rss/heise-atom.xml"
    category: "tech"
    filter_keywords: ["KI", "künstliche Intelligenz", "Immobilien", "Digitalisierung"]

  # --- Studien & Research ---
  - name: "Bitkom Presse"
    url: "https://www.bitkom.org/rss.xml"
    category: "studien"
    filter_keywords: ["Digitalisierung", "KI", "Mittelstand"]

  - name: "Statista Trend Reports"
    type: "scrape"
    url: "https://de.statista.com/statistik/kategorien/"
    category: "studien"

  # --- Google Alerts (Atom Feeds) ---
  - name: "Google Alert: Immobilien KI"
    url: "GOOGLE_ALERT_ATOM_FEED_URL_HIER"
    category: "alerts"

  - name: "Google Alert: PropTech Deutschland"
    url: "GOOGLE_ALERT_ATOM_FEED_URL_HIER"
    category: "alerts"

  # --- Semantic Scholar ---
  - name: "Semantic Scholar"
    type: "api"
    keywords:
      - "real estate artificial intelligence"
      - "PropTech digital transformation"
      - "AI chatbot customer service"
      - "real estate automation"
    max_results: 20
    category: "academic"

scrape_targets:
  - name: "IVD Pressemitteilungen"
    url: "https://www.ivd.net/presse/pressemitteilungen"
    selector: "article.press-release"
    category: "verband"

  - name: "ZIA Zentraler Immobilien Ausschuss"
    url: "https://www.zia-deutschland.de/presse/"
    selector: ".news-item"
    category: "verband"
```

---

## Coding-Konventionen

- **Sprache im Code:** Englisch (Variablen, Funktionen, Kommentare)
- **Sprache im Content:** Deutsch (Prompts, Blog-Texte, LinkedIn-Texte)
- **Type Hints:** Überall verwenden (Python 3.11+ Syntax)
- **Error Handling:** Jeder Agent fängt seine Fehler, loggt sie, und benachrichtigt das Team
- **Logging:** `structlog` mit JSON-Output für Railway
- **Tests:** Pytest, mindestens Happy-Path + Fehlerfall pro Agent
- **Secrets:** Niemals hartcodiert, immer über .env / Railway Env Vars
- **Prompts:** Nie inline im Code, immer aus `prompts/` Dateien laden
- **Daten:** Kein lokaler State — alles in Supabase

---

## Reihenfolge der Implementierung

### Phase 1: Foundation (Tag 1-2)
1. **core/config.py** — Settings, Env-Variablen, Timezone
2. **core/supabase_client.py** — CRUD Operations für alle Tabellen
3. **core/claude_client.py** — Anthropic API Wrapper mit Retry-Logik
4. **scripts/setup_supabase.sql** — Alle 6 Tabellen deployen

### Phase 2: SEO Intelligence (Tag 3-5)
5. **core/gsc_client.py** — Google Search Console API Wrapper
6. **core/autocomplete_client.py** — Google Autocomplete Abfragen
7. **agents/content_crawler.py** — Website-Crawl + Content Inventory
8. **scripts/initial_crawl.py** — Einmaliger Komplett-Crawl von sunsideai.de
9. **agents/keyword_researcher.py** — GSC-Daten + Autocomplete + Clustering
10. **prompts/content-strategist.md** — Prompt für Opportunity-Erkennung
11. **agents/content_strategist.py** — Keyword-Gaps & Opportunities

### Phase 3: Research Agent (Tag 6-7)
12. **feeds/sources.yaml** — RSS-Feed-Liste validieren (welche URLs funktionieren?)
13. **prompts/research-agent.md** — Prompt für Relevanzfilterung
14. **agents/researcher.py** — Research Agent (mit Opportunity-Input)

### Phase 4: Blog Writer (Tag 8-10)
15. **prompts/seo-blog-writer.md** — Aus bestehendem Claude SEO-Project übernehmen
16. **prompts/quality-gate.md** — QA-Prompt finalisieren
17. **agents/blog_writer.py** — Blog Writer + Quality Gate + Content-Awareness
18. **core/github_client.py** — GitHub API (Auto-Commit ins Blog-Repo)

### Phase 5: LinkedIn Distribution (Tag 11-12)
19. **prompts/linkedin-creator.md** — Aus bestehendem Claude LinkedIn-Project übernehmen
20. **agents/image_generator.py** — Infografik-Generator
21. **core/linkedin_client.py** — LinkedIn API v2 Wrapper
22. **agents/linkedin_poster.py** — LinkedIn Distribution Agent

### Phase 6: Orchestrierung (Tag 13-15)
23. **core/notifier.py** — Slack/E-Mail Notifications
24. **main.py** — Orchestrator mit Scheduling (alle Agents + Timing)
25. **Dockerfile** — Railway Deployment
26. **End-to-End Test** — Vom Crawl über Research bis zum LinkedIn-Post

### Phase 7: Ramp-Up & Optimierung (Woche 3+)
27. QA-Threshold auf 10.0 setzen, alle Posts manuell reviewen
28. Prompt-Qualität iterieren basierend auf Output
29. Threshold schrittweise senken
30. Performance-Feedback-Loop: LinkedIn-Daten → Prompt-Optimierung

---

## Wichtige Hinweise

- **Claude Model:** `claude-sonnet-4-20250514` für alle Content-Calls (gutes Preis-Leistungs-Verhältnis bei 3-5 Posts/Woche)
- **Prompt-Temperatur:** 0.7 für Blog-Texte (kreativ aber konsistent), 0.3 für Quality Gate und Strategist (deterministisch)
- **LinkedIn Token Refresh:** Access Token läuft nach 60 Tagen ab — Agent soll 7 Tage vorher warnen
- **GSC Setup:** Service Account in Google Cloud Console erstellen, Search Console API aktivieren, Service Account als Nutzer in GSC Property hinzufügen (Leserechte reichen)
- **Deduplizierung:** Vor Blog-Erstellung prüfen ob ein ähnliches Thema in den letzten 30 Tagen behandelt wurde
- **Bilder:** Die 20 Blog-Header-SVGs/PNGs sind bereits erstellt (Dark Purple Sunside AI Stil mit verschiedenen Icons)
- **Rate Limiting:** Max 1 Blog-Post pro Tag, max 5 pro Woche (konfigurierbar)
- **Autocomplete Throttling:** Google Autocomplete max 10 Requests/Minute, sonst IP-Block
- **Content Inventory Crawl:** Nur eigene Domain crawlen (sunsideai.de), max 2 Req/Sek
- **Keyword-Daten:** GSC liefert Daten mit 2-3 Tagen Verzögerung — bei der Analyse berücksichtigen
- **CTR-Optimierungen:** Können ohne neuen Blogpost umgesetzt werden (nur Frontmatter-Update im Repo)
- **Fallback:** Wenn keine Findings vorhanden, keinen Content erzwingen — lieber eine Woche aussetzen als schlechten Content posten
- **Interne Links:** Blog Writer soll nur auf URLs verlinken die im Content Inventory als `active` markiert sind
