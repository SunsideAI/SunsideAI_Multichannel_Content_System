# Sunside AI — Content Autopilot: Gesamtübersicht

## 1. Vision

Ein vollautomatisiertes Content-System das wöchentlich 3-5 SEO-optimierte Blogbeiträge für sunsideai.de erstellt und über LinkedIn distribuiert — basierend auf aktuellen Branchenstudien und Trends aus der Immobilien- und KI-Welt.

**Prinzip:** Full Autopilot mit optionalem Kill-Switch ("Publish Unless Flagged")

---

## 2. Systemarchitektur

```
┌──────────────────────────────────────────────────────────────────┐
│                        CRON SCHEDULER                            │
│              Railway Cron / GitHub Actions                        │
│                                                                  │
│  So 20:00 → Research    Mo-Fr 06:00 → Blog    +2h → LinkedIn    │
└──────────┬──────────────────┬─────────────────────┬──────────────┘
           │                  │                     │
    ┌──────▼──────┐    ┌──────▼──────┐      ┌──────▼──────┐
    │  RESEARCH   │    │   BLOG      │      │  LINKEDIN   │
    │   AGENT     │    │   AGENT     │      │   AGENT     │
    │             │    │             │      │             │
    │ RSS Feeds   │    │ Claude API  │      │ Claude API  │
    │ Scholar API │──▶ │ SEO Prompt  │──▶   │ LI Prompt   │
    │ Web Scrape  │    │ Quality Gate│      │ Image Gen   │
    │ Claude:     │    │ Git Push    │      │ LI API Post │
    │  Relevanz   │    │ Netlify     │      │             │
    └──────┬──────┘    └──────┬──────┘      └──────┬──────┘
           │                  │                     │
           └──────────────────┼─────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │     SUPABASE      │
                    │                   │
                    │ posts             │
                    │ findings          │
                    │ feed_sources      │
                    │ publish_log       │
                    │ weekly_reports    │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │   NOTIFICATION    │
                    │                   │
                    │ Daily Summary     │
                    │ Hold Alerts       │
                    │ Weekly Report     │
                    │ (Slack / E-Mail)  │
                    └───────────────────┘
```

---

## 3. Datenbank-Schema (Supabase)

### Tabelle: `feed_sources`
| Feld | Typ | Beschreibung |
|------|-----|-------------|
| id | uuid | Primary Key |
| name | text | "Immobilienzeitung", "t3n" etc. |
| url | text | RSS Feed URL oder Scrape-Target |
| type | text | "rss" / "scrape" / "scholar" |
| category | text | "immobilien" / "ki" / "digitalisierung" / "studien" |
| scrape_selector | text | CSS-Selector für Scraping (nullable) |
| active | boolean | Feed aktiv/inaktiv |
| last_fetched_at | timestamptz | Letzter erfolgreicher Fetch |

### Tabelle: `findings`
| Feld | Typ | Beschreibung |
|------|-----|-------------|
| id | uuid | Primary Key |
| source_id | uuid | FK → feed_sources |
| title | text | Titel des Artikels/Studie |
| url | text | Original-URL |
| summary | text | KI-generierte Zusammenfassung |
| key_stats | jsonb | Extrahierte Statistiken/Zahlen |
| relevance_score | float | 1-10, von Claude bewertet |
| target_keyword | text | Vorgeschlagenes SEO-Keyword |
| used | boolean | Bereits in Blog verwendet? |
| created_at | timestamptz | Wann gefunden |

### Tabelle: `posts`
| Feld | Typ | Beschreibung |
|------|-----|-------------|
| id | uuid | Primary Key |
| finding_id | uuid | FK → findings |
| status | text | researched / drafted / reviewed / published / distributed / rejected |
| blog_markdown | text | Vollständiger Blog-Post |
| blog_slug | text | URL-Slug für sunsideai.de |
| blog_meta | jsonb | {title, description, keywords, category, readingTime} |
| linkedin_text | text | LinkedIn-Post-Text |
| linkedin_image_key | text | Welches Icon-Template verwendet |
| linkedin_post_id | text | LinkedIn API Response ID |
| quality_score | float | 1-10 vom Quality Gate |
| quality_issues | text[] | Liste der Probleme |
| auto_approved | boolean | Score ≥ 7? |
| manually_reviewed | boolean | Wurde manuell geprüft? |
| reviewer_notes | text | Anmerkungen vom Review |
| scheduled_publish_at | timestamptz | Geplanter Publish-Zeitpunkt |
| published_at | timestamptz | Tatsächlich published |
| distributed_at | timestamptz | LinkedIn gepostet |
| git_commit_sha | text | Commit-Hash im Blog-Repo |
| created_at | timestamptz | Erstellt |

### Tabelle: `publish_log`
| Feld | Typ | Beschreibung |
|------|-----|-------------|
| id | uuid | Primary Key |
| post_id | uuid | FK → posts |
| action | text | "published" / "distributed" / "held" / "rejected" / "retried" |
| details | jsonb | Kontext-Infos |
| created_at | timestamptz | Zeitstempel |

---

## 4. Agent-Details

### 4.1 Research Agent

**Trigger:** Jeden Sonntag 20:00 Uhr
**Dauer:** ca. 5-10 Minuten
**Kosten:** ~0.50€ pro Run (Claude API für Relevanzfilterung)

**Ablauf:**
1. Alle aktiven Feeds aus `feed_sources` laden
2. RSS-Feeds via `feedparser` pullen — nur Artikel seit letztem Run
3. Scrape-Targets via `requests` + `BeautifulSoup` scrapen
4. Semantic Scholar API für akademische Papers (Keywords: "real estate technology", "PropTech", "Immobilien Digitalisierung")
5. Duplikate entfernen (URL-basiert + Titel-Ähnlichkeit)
6. Alle neuen Artikel (typisch 50-100) an Claude senden:
   - Batch-Prompt: "Bewerte diese Artikel auf Relevanz für deutsche Immobilienmakler (1-10). Nur Artikel ≥ 6 weiterverwenden."
7. Top 10-15 Findings in Supabase speichern
8. Für die Top 5: `web_fetch` für Volltexte, Claude extrahiert Key Stats und schlägt Target Keywords vor
9. Content-Plan für die Woche erstellen: 5 Findings den Wochentagen zuordnen, `scheduled_publish_at` setzen

**RSS Feed Quellen (Initial):**

Immobilienbranche:
- iz.de/rss (Immobilienzeitung)
- haufe.de/immobilien (RSS)
- ivd.net/presse (Scrape)
- immocompact.de/rss
- immobilien-aktuell.net/feed

KI & Tech:
- t3n.de/rss.xml
- heise.de/rss/heise-atom.xml
- golem.de/rss.php
- the-decoder.de/feed (KI-News DE)

Studien & Reports:
- bitkom.org/Presse (Scrape)
- Google Alerts Atom Feeds (Keywords konfigurierbar)
- Semantic Scholar API (Keywords konfigurierbar)

PropTech:
- proptech.de/feed
- gewerbe-quadrat.de/feed

### 4.2 Blog Agent

**Trigger:** Mo-Fr um 06:00 Uhr (oder nachdem Research Agent fertig ist)
**Dauer:** ca. 2-3 Minuten pro Post
**Kosten:** ~0.10-0.15€ pro Post (Claude Sonnet)

**Ablauf:**
1. Nächsten Post mit Status `researched` und `scheduled_publish_at ≤ heute` aus Supabase laden
2. Finding-Daten zusammenstellen (Titel, Stats, Quelle, Keyword)
3. System Prompt aus `prompts/seo-blog-writer.md` laden
4. Claude API Call → Blog-Markdown generieren
5. Quality Gate: Zweiter Claude Call mit `prompts/quality-gate.md`
   - Score ≥ 7 → `auto_approved = true`, weiter
   - Score 4-7 → `auto_approved = false`, Status `hold`, Notification senden
   - Score < 4 → Status `rejected`, Retry mit anderem Finding
6. Blog-Markdown in Next.js-Format bringen (Frontmatter + Content)
7. Git Push ins Blog-Repo (GitHub API: Create File)
   - Pfad: `src/content/blog/{slug}.md`
   - Branch: `main` (Auto-Deploy via Netlify)
8. Post-Status auf `published` setzen, `published_at` + `git_commit_sha` speichern

**Blog-Markdown Format (Next.js):**
```markdown
---
title: "KI-Chatbots für Immobilienmakler: Alle Vorteile"
description: "So helfen KI-Technologien Immobilienmaklern..."
date: "2026-04-07"
author: "Paul Probodziak"
category: "KI & Automatisierung"
image: "/images/blog/blog-chatbot.png"
readingTime: "7 Min"
keywords: ["ki chatbot immobilienmakler", "chatbot makler", ...]
---

# KI-Chatbots für Immobilienmakler: Alle Vorteile

Blog-Inhalt hier...
```

### 4.3 LinkedIn Agent

**Trigger:** 2 Stunden nach Blog-Publish (oder 08:00 Uhr)
**Dauer:** ca. 1-2 Minuten pro Post
**Kosten:** ~0.05€ pro Post (Claude Sonnet, kurzer Text)

**Ablauf:**
1. Alle Posts mit Status `published` und `distributed_at IS NULL` laden
2. System Prompt aus `prompts/linkedin-creator.md` laden
3. Claude API Call → LinkedIn-Post-Text generieren
   - Enthält: Hook, Key Insight, 3 Bullet Points, CTA mit Blog-Link
   - Format: LinkedIn-optimiert (Zeilenumbrüche, Emojis sparsam, Hashtags)
4. Infografik generieren (SVG → PNG via image_generator.py)
   - Passendes Icon-Template basierend auf Kategorie auswählen
   - Titel + Bullets + Branding overlay
5. LinkedIn API: Bild hochladen → Image URN erhalten
6. LinkedIn API: Post erstellen mit Text + Bild + Blog-Link
7. Post-Status auf `distributed` setzen, `linkedin_post_id` speichern

**LinkedIn API Flow:**
```
POST /v2/assets?action=registerUpload → Upload-URL
PUT {upload-url} → Bild hochladen → Asset URN
POST /v2/ugcPosts → Post erstellen mit Asset URN + Text
```

### 4.4 Quality Gate

**Kein eigener Agent** — wird inline vom Blog Agent aufgerufen.

**Prüfkriterien (in quality-gate.md definiert):**
1. Faktentreue: Stimmen zitierte Zahlen mit der Quelle überein?
2. SEO: Ist das Target Keyword in H1, erster Paragraph, Meta Description?
3. Tonalität: Passt der Stil zum Sunside AI Branding?
4. Struktur: Hat der Post H2s, Listen, CTA, interne Links?
5. Länge: Mindestens 800 Wörter, maximal 2000?
6. Originalität: Kein Copy-Paste aus der Quelle?
7. Rechtschreibung/Grammatik: Offensichtliche Fehler?
8. Call-to-Action: Verlinkt auf Sunside AI Leistungen?

**Output-Format:**
```json
{
  "score": 8.5,
  "auto_publish": true,
  "issues": [],
  "suggestions": ["Internen Link zu /leistungen/chatbot ergänzen"]
}
```

---

## 5. Notification System

### Daily Summary (Mo-Fr, 07:00)
```
📬 Sunside Content Autopilot — Montag, 7. April 2026

Heute geplant:
✅ "KI-Chatbots für Makler" — Score 8.2 (auto-approved)
   Blog: 10:00 | LinkedIn: 12:00

In der Hold-Queue: 0 Posts
Rejected diese Woche: 0 Posts

→ Dashboard: https://supabase.com/dashboard/...
→ Antwort mit STOP um heutigen Post zu pausieren
```

### Hold Alert (sofort bei Score < 7)
```
⚠️ Post braucht Review

"DSGVO-Update für Immobilienmakler 2026"
Score: 5.8/10

Probleme:
- Zitierte Statistik (43%) nicht in Quelle verifizierbar
- Meta Description fehlt Keyword

→ Review: https://supabase.com/dashboard/.../posts/{id}
→ Antwort APPROVE oder REJECT
```

### Weekly Report (Sonntag, 19:00)
```
📊 Wochenreport — KW 15/2026

Published:  4 Posts
Held:       1 Post (manuell approved)
Rejected:   0 Posts
Avg Score:  8.1/10

Top Finding: "Studie: 67% der Makler planen KI-Einsatz"
Quelle:     IVD Digitalbarometer 2026

LinkedIn Performance:
- 1.340 Impressions (↑ 23%)
- 47 Engagements
- 12 Link-Clicks

Nächste Woche: 5 Posts geplant
Research läuft um 20:00...
```

**Kanal:** Slack Webhook (empfohlen) oder Brevo E-Mail API (habt ihr schon).

---

## 6. Kosten pro Monat

| Posten | Kosten |
|--------|--------|
| Claude API (Sonnet) — ~25 Blog-Posts + Research + QA + LinkedIn | ~15-25€ |
| Railway Hosting (1 Service, Cron) | ~5-10€ |
| Supabase (Free Tier reicht) | 0€ |
| Semantic Scholar API | 0€ |
| LinkedIn API | 0€ |
| RSS Feeds / Scraping | 0€ |
| **Gesamt** | **~20-35€/Monat** |

---

## 7. Repo-Struktur

```
sunside-autopilot/
├── CLAUDE.md                      ← Claude Code Instructions
├── README.md
├── requirements.txt
├── .env.example
├── config.py                      ← Zentrale Konfiguration
│
├── prompts/                       ← Source of Truth für alle Prompts
│   ├── research-agent.md          ← Research & Relevanzfilterung
│   ├── seo-blog-writer.md         ← Blog-Erstellung (aus Claude SEO-Projekt)
│   ├── linkedin-creator.md        ← LinkedIn-Posts (aus Claude LI-Projekt)
│   ├── quality-gate.md            ← Qualitätsprüfung
│   └── CHANGELOG.md               ← Prompt-Versionshistorie
│
├── feeds/
│   ├── sources.yaml               ← Alle Feed-Quellen
│   └── keywords.yaml              ← Scholar/Alerts Keywords
│
├── agents/
│   ├── __init__.py
│   ├── researcher.py              ← Phase 1: Studien finden & filtern
│   ├── blog_writer.py             ← Phase 2: Blog erstellen & publishen
│   ├── linkedin_poster.py         ← Phase 3: LinkedIn Distribution
│   ├── image_generator.py         ← Infografik-Erstellung
│   ├── quality_gate.py            ← Qualitätsprüfung
│   └── notifier.py                ← Slack/E-Mail Notifications
│
├── services/
│   ├── __init__.py
│   ├── feed_fetcher.py            ← RSS + Scraping + Scholar
│   ├── supabase_client.py         ← DB-Operationen
│   ├── github_client.py           ← Git Push ins Blog-Repo
│   ├── linkedin_client.py         ← LinkedIn API Wrapper
│   └── claude_client.py           ← Anthropic API Wrapper
│
├── templates/
│   ├── blog-post.md               ← Next.js Blog Frontmatter Template
│   ├── linkedin-post.txt          ← LinkedIn Text Template
│   └── notification-templates/
│       ├── daily-summary.md
│       ├── hold-alert.md
│       └── weekly-report.md
│
├── assets/
│   ├── blog-icons/                ← Die 20 SVG Blog-Icons
│   └── fonts/
│
├── tests/
│   ├── test_researcher.py
│   ├── test_blog_writer.py
│   ├── test_quality_gate.py
│   └── test_linkedin_poster.py
│
├── scripts/
│   ├── setup_supabase.sql         ← DB-Schema Setup
│   ├── seed_feeds.py              ← Initial Feed-Quellen laden
│   └── test_pipeline.py           ← Einmal manuell durchlaufen
│
├── main.py                        ← Orchestrator / Entry Point
└── Dockerfile                     ← Railway Deployment
```

---

## 8. Technischer Stack

| Komponente | Technologie |
|------------|-------------|
| Runtime | Python 3.12 |
| KI | Claude Sonnet (Anthropic API) |
| Datenbank | Supabase (PostgreSQL) |
| Hosting | Railway (Docker) |
| Blog Repo | GitHub API → SunsideAI/SunsideAI_Website |
| Blog Deploy | Netlify (Auto-Deploy on Push) |
| LinkedIn | LinkedIn Marketing API (OAuth 2.0) |
| RSS | feedparser (Python) |
| Scraping | requests + BeautifulSoup4 |
| Studien | Semantic Scholar API (kostenlos) |
| Bilder | Pillow + SVG Templates |
| Notifications | Slack Webhook oder Brevo API |
| Scheduler | Railway Cron oder APScheduler |

---

## 9. Setup-Reihenfolge

### Phase 1: Foundation (Tag 1-2)
- [ ] Repo `sunside-autopilot` erstellen
- [ ] Supabase Schema aufsetzen (setup_supabase.sql)
- [ ] .env mit API Keys konfigurieren
- [ ] Prompt-Files aus Claude Projects übernehmen
- [ ] Feed-Quellen in sources.yaml definieren
- [ ] claude_client.py + supabase_client.py bauen

### Phase 2: Research Agent (Tag 3-4)
- [ ] feed_fetcher.py (RSS + Scraping + Scholar)
- [ ] researcher.py (Relevanzfilterung + Keyword-Vorschlag)
- [ ] seed_feeds.py ausführen
- [ ] Ersten Research-Run manuell testen

### Phase 3: Blog Agent (Tag 5-7)
- [ ] blog_writer.py (Claude API + Markdown Generation)
- [ ] quality_gate.py (Score-System)
- [ ] github_client.py (Auto-Commit ins Blog-Repo)
- [ ] Ersten Blog-Post manuell testen (Draft → Publish)

### Phase 4: LinkedIn Agent (Tag 8-9)
- [ ] LinkedIn App registrieren + OAuth Setup
- [ ] linkedin_client.py (Auth + Post + Image Upload)
- [ ] image_generator.py (Infografik-Pipeline)
- [ ] linkedin_poster.py (Text + Bild + Post)
- [ ] Ersten LinkedIn-Post manuell testen

### Phase 5: Automation & Monitoring (Tag 10-12)
- [ ] main.py Orchestrator mit Scheduling
- [ ] notifier.py (Daily Summary + Alerts)
- [ ] Dockerfile + Railway Deployment
- [ ] Cron-Jobs konfigurieren
- [ ] Eine volle Woche im Testbetrieb laufen lassen

### Phase 6: Go Live (Tag 13+)
- [ ] Review der ersten Auto-Posts
- [ ] Prompt-Feintuning basierend auf Qualität
- [ ] Quality Gate Threshold kalibrieren
- [ ] Full Autopilot aktivieren

---

## 10. Benötigte API Keys & Zugänge

```env
# .env
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
GITHUB_TOKEN=ghp_...                    # Repo-Zugriff SunsideAI_Website
GITHUB_REPO=SunsideAI/SunsideAI_Website
GITHUB_BRANCH=main
LINKEDIN_CLIENT_ID=...
LINKEDIN_CLIENT_SECRET=...
LINKEDIN_ACCESS_TOKEN=...               # OAuth 2.0 Token
LINKEDIN_AUTHOR_URN=urn:li:person:...   # oder urn:li:organization:...
SLACK_WEBHOOK_URL=https://hooks.slack.com/...  # Optional
BREVO_API_KEY=...                       # Optional, falls E-Mail statt Slack
SEMANTIC_SCHOLAR_API_KEY=...            # Optional, erhöht Rate Limit
```

---

## 11. Risiken & Mitigations

| Risiko | Mitigation |
|--------|-----------|
| LinkedIn API Token läuft ab (60 Tage) | Token-Refresh in linkedin_client.py, Alert bei 401 |
| RSS Feed geht offline | Fehlertoleranz: Skip + Log, Weekly Alert wenn Feed > 7 Tage nicht erreichbar |
| Blog-Qualität sinkt | Quality Gate mit Score-Tracking über Zeit, Alert bei Avg < 7 |
| Duplicate Content | URL-Dedup in findings + Themen-Ähnlichkeit via Embedding-Vergleich |
| Netlify Deploy schlägt fehl | GitHub Webhook Status Check, Retry nach 5 Min |
| Rate Limits (Claude API) | Batching, Retry mit Exponential Backoff |
| Faktenfehler in Posts | Quality Gate prüft Stats gegen Quelle, Hold bei Unsicherheit |
