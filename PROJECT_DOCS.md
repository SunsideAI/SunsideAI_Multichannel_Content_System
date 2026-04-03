# Sunside AI Content Autopilot — Projektdokumentation

## Was ist das?

Der Content Autopilot ist eine vollautomatische, datengetriebene Content-Pipeline für Sunside AI (sunsideai.de). Das System analysiert die eigene Website, zieht SEO-Daten aus der Google Search Console, identifiziert Keyword-Lücken, recherchiert passende Studien und Trends, erstellt SEO-optimierte Blogbeiträge und promotet sie automatisch auf LinkedIn.

Im Kern macht der Autopilot drei Dinge: Er versteht was auf der Website fehlt (SEO Intelligence), findet passende Inhalte dafür (Research), und produziert den Content automatisch (Blog + LinkedIn).

Das System läuft ohne menschliches Eingreifen, bietet aber jederzeit die Möglichkeit, einzelne Posts vor Veröffentlichung zu reviewen oder die Pipeline zu pausieren.

---

## Warum bauen wir das?

Sunside AI positioniert sich als KI-Experte für Immobilienmakler. Um diese Positionierung zu untermauern, brauchen wir konstant hochwertigen Content der zeigt, dass wir die Branche verstehen und technisch an der Spitze sind.

Manuelles Bloggen skaliert nicht. 3-5 Posts pro Woche konsistent zu produzieren — jeder recherchiert, SEO-optimiert, mit Infografik, auf LinkedIn geteilt — wäre ein Vollzeitjob. Der Autopilot erledigt das in unter 30 Minuten Rechenzeit pro Tag, bei geschätzten Kosten von 20-35€/Monat.

---

## Wie funktioniert es?

### Stream A: SEO Intelligence (wöchentlich, Sonntag)

```
Sonntag 18:00 → Content Crawler läuft
                 ├── sunsideai.de Sitemap abrufen
                 ├── Jede Seite crawlen (Title, H1, H2s, Wortanzahl, Links)
                 └── Content Inventory in Supabase aktualisieren

Sonntag 19:00 → Keyword Researcher läuft
                 ├── Google Search Console API: letzte 28 Tage
                 │    └── Jedes Keyword: Impressions, Clicks, CTR, Position
                 ├── Google Autocomplete: Long-Tail Erweiterungen
                 ├── Claude: Keyword-Clustering nach Themen
                 └── Keywords in Supabase speichern

Sonntag 19:30 → Content Strategist läuft
                 ├── Content Inventory + Keywords vergleichen
                 ├── Claude identifiziert Opportunities:
                 │    ├── Keyword Gaps (viel Nachfrage, kein Content)
                 │    ├── Low-Hanging Fruits (Position 5-15, Push möglich)
                 │    ├── CTR-Optimierungen (nur Meta-Update nötig)
                 │    ├── Content Refreshes (alte Posts updaten)
                 │    └── Themen-Cluster (Long-Tail bündeln)
                 └── Top 10 Opportunities → Supabase
```

### Stream B: Research + Blog-Erstellung (wöchentlich + täglich)

```
Sonntag 20:00 → Research Agent läuft
                 ├── Content Opportunities laden (gezielter Modus)
                 ├── 20+ RSS-Feeds abrufen (Immobilien-News, Tech, Studien)
                 ├── Semantic Scholar API abfragen
                 ├── Google Alerts Feeds einlesen
                 ├── ~50-100 neue Artikel sammeln
                 ├── Claude filtert auf Relevanz + verknüpft mit Opportunities
                 └── Top-Findings in Supabase speichern

Mo-Fr 06:00   → Blog Writer Agent läuft
                 ├── Nächstes Finding laden (Opportunity-verknüpfte bevorzugt)
                 ├── Content Inventory laden → interne Link-Ziele identifizieren
                 ├── Claude erstellt SEO-Blogbeitrag (1.500-2.000 Wörter)
                 │    └── Mit Keyword-Fokus + internen Links + Differenzierung
                 ├── Quality Gate: Zweiter Claude-Call bewertet 1-10
                 │    ├── Score ≥ 7.5 → Automatisch freigegeben
                 │    └── Score < 7.5 → Zurückgehalten, Notification
                 ├── Morning Digest an Slack/E-Mail (07:00)
                 ├── 2h Review-Fenster (optional eingreifen)
                 └── Auto-Publish um 09:00
                      ├── Git Push ins Website-Repo
                      └── Netlify deployed automatisch
```

### Stream C: LinkedIn Distribution (täglich)

```
Mo-Fr 10:00   → LinkedIn Agent läuft
                 ├── Neue PUBLISHED Blog-Posts laden
                 ├── Claude erstellt LinkedIn-Post-Text
                 ├── Infografik generieren (1200x1200 PNG)
                 │    ├── Blog-Header als Hintergrund
                 │    ├── Titel + 3 Key Bullets
                 │    └── Sunside AI Branding
                 ├── Bild auf LinkedIn hochladen
                 └── Post veröffentlichen
```

### Der strategische Unterschied

Ohne SEO Intelligence: Agent findet Studie über "KI in der Immobilienbewertung" → schreibt darüber.

Mit SEO Intelligence: GSC zeigt, dass "immobilienbewertung ki" 800 Impressions hat aber auf Position 14 rankt → Content Strategist markiert es als Low-Hanging Fruit → Research Agent sucht gezielt nach Studien zu diesem Thema → Blog Writer erstellt Post mit exakt diesem Keyword-Fokus und verlinkt auf bestehende Seiten → Position steigt auf Seite 1.

---

## Kontrollmechanismen

### Automatisch (Default)

Der Quality Gate Agent bewertet jeden Blogbeitrag anhand von fünf Kriterien: Faktische Korrektheit, SEO-Qualität, Lesbarkeit, Relevanz und Brand-Konsistenz. Nur Posts über dem konfigurierbaren Threshold (default 7.5/10) werden automatisch veröffentlicht.

### Morning Digest

Jeden Morgen um 07:00 erhaltet ihr eine Benachrichtigung:

```
📝 Content Autopilot — Heute geplant:

Blog: "KI-gestützte Immobilienbewertung: Was Makler wissen müssen"
QA-Score: 8.7/10
Keyword: ki immobilienbewertung
Auto-Publish: 09:00 Uhr

LinkedIn-Post vorbereitet. Preview: [Link]

⏸ "hold" antworten um zu pausieren
```

Wenn alles gut aussieht: ignorieren, es läuft durch. Wenn nicht: "hold" antworten.

### Manuelle Kontrolle

Drei Hebel, alle über Supabase oder Slack steuerbar:

| Aktion | Wie | Effekt |
|--------|-----|--------|
| Einzelnen Post stoppen | Post auf `REVIEW_HOLD` setzen | Agent überspringt diesen Post |
| Pipeline pausieren | `paused: true` in Config | Alle Agents stoppen |
| Threshold ändern | `qa_threshold: 9.0` in Config | Strengere Qualitätsprüfung |
| Thema sperren | `hold_topics: ["datenschutz"]` | Themen-basierter Filter |
| Max Posts reduzieren | `max_posts_per_week: 3` | Weniger Output |

### Empfohlener Ramp-Up

| Phase | Zeitraum | Threshold | Review |
|-------|----------|-----------|--------|
| Kalibrierung | Woche 1-2 | 10.0 | Alles manuell prüfen |
| Vertrauen aufbauen | Woche 3-4 | 8.5 | Nur Digest checken |
| Autopilot | Ab Woche 5 | 7.5 | Gelegentlich reinschauen |
| Optimiert | Ab Monat 3 | Dynamisch | Basierend auf LinkedIn-Performance |

---

## Tech Stack & Kosten

### Technologie

| Komponente | Technologie | Warum |
|------------|-------------|-------|
| Agent Runtime | Python 3.11 auf Railway | Einfach, ihr kennt den Stack, günstig |
| Content-KI | Claude API (Sonnet) | Qualität, deutsch, günstig bei Masse |
| Datenbank | Supabase | Habt ihr schon, PostgreSQL, kostenloser Tier |
| SEO-Daten | Google Search Console API | Echte Keyword-Daten, kostenlos, schon eingerichtet |
| Keyword-Research | Google Autocomplete | Kostenlos, keine API-Keys nötig |
| Content-Crawling | BeautifulSoup + requests | Eigene Seite crawlen, kein Overhead |
| Blog-Deploy | GitHub API → Netlify | Bestehendes Setup, Zero Config |
| LinkedIn | LinkedIn API v2 | Offiziell, kein Scraping |
| Research | RSS + Semantic Scholar | Kostenlos, zuverlässig, keine Rate-Limits |
| Infografiken | Pillow + wkhtmltoimage | Lokal, keine API-Kosten |
| Notifications | Slack Webhook | Kostenlos, schnell |

### Monatliche Kosten (geschätzt)

| Posten | Kosten |
|--------|--------|
| Claude API (Sonnet, ~20 Posts + QA + LinkedIn + Research + Strategist) | 20-30€ |
| Railway (Agent Hosting) | 5-10€ |
| Supabase | 0€ (Free Tier reicht) |
| Google Search Console API | 0€ |
| Google Autocomplete | 0€ |
| Semantic Scholar API | 0€ |
| LinkedIn API | 0€ |
| RSS Feeds | 0€ |
| **Gesamt** | **~25-40€/Monat** |

---

## Prompt-Management

### Source of Truth: Das Repo

Die System Prompts für alle Agents liegen als Markdown-Dateien im `prompts/` Verzeichnis. Dort werden sie editiert und versioniert. Git-History zeigt welche Prompt-Version welche Ergebnisse produziert hat.

### Migration aus Claude Projects

Paul und Niklas haben bereits funktionierende Claude Projects (Web-UI) mit ausgereiften Instructions für SEO-Blog-Writing und LinkedIn-Post-Erstellung. Diese Instructions werden 1:1 in die entsprechenden Markdown-Dateien kopiert:

| Claude Project | → Prompt-Datei |
|----------------|----------------|
| SEO Blog Projekt | `prompts/seo-blog-writer.md` |
| LinkedIn Projekt | `prompts/linkedin-creator.md` |
| (Neu erstellt) | `prompts/research-agent.md` |
| (Neu erstellt) | `prompts/quality-gate.md` |
| (Neu erstellt) | `prompts/content-strategist.md` |

Wenn ihr im Claude Project einen Prompt verbessert, updated ihr die MD-Datei im Repo. Umgekehrt: Wenn ihr im Repo iteriert und die Ergebnisse besser werden, spiegelt ihr das ins Claude Project zurück.

---

## RSS-Feed Quellen

### Immobilienbranche (DE)

| Quelle | Typ | Relevanz |
|--------|-----|----------|
| IZ Immobilien Zeitung | RSS | Marktdaten, Transaktionen |
| Haufe Immobilien | RSS | Recht, Verwaltung, Trends |
| ImmoCompact | RSS | Makler-News, Produkte |
| AIZ Immobilienmagazin | RSS | IVD-News, Branchen-Events |
| IVD Pressemitteilungen | Scrape | Verbandsnews, Studien |
| ZIA Presse | Scrape | Gewerbeimmobilien, Politik |

### KI & Digitalisierung

| Quelle | Typ | Filter |
|--------|-----|--------|
| t3n | RSS | KI, AI, Immobilien, Automatisierung |
| Heise | RSS | KI, Digitalisierung |
| Bitkom Presse | RSS | Digitalisierung, Mittelstand |

### Studien & Research

| Quelle | Typ | Fokus |
|--------|-----|-------|
| Semantic Scholar | API | PropTech, Real Estate AI |
| Google Alerts | Atom | "Immobilien KI", "PropTech DE" |

---

## Supabase-Tabellen

| Tabelle | Zweck | Wichtige Felder |
|---------|-------|-----------------|
| `content_inventory` | Alle Seiten auf sunsideai.de | url, title, h1, h2s, word_count, primary_keyword, content_age_days |
| `keywords` | GSC-Daten + Autocomplete + Clustering | keyword, impressions, clicks, ctr, avg_position, cluster_name, search_intent |
| `content_opportunities` | Priorisierte SEO-Opportunities | type, priority, target_keyword, action, suggested_title, research_query |
| `findings` | Recherche-Ergebnisse aus RSS/Scholar | title, source, relevance_score, opportunity_id, status |
| `blog_posts` | Blog-Content + Status + QA-Score | title, slug, content, qa_score, target_keyword, internal_links_used |
| `linkedin_posts` | LinkedIn-Posts + Performance-Tracking | post_text, image_url, linkedin_post_id, impressions, clicks |
| `pipeline_config` | Steuerung des Systems | key-value (threshold, paused, hold_topics, etc.) |

---

## Infografik-Design

Jede LinkedIn-Infografik folgt diesem Layout (1200x1200px):

```
┌─────────────────────────────────┐
│                                 │
│     (Dark Purple Background)    │
│     (Dot Grid Pattern)          │
│                                 │
│          ┌─────────┐            │
│          │  Icon   │            │
│          │  + Glow │            │
│          └─────────┘            │
│                                 │
│  ┌─ Kategorie-Tag ─┐           │  ← Gradient Overlay beginnt
│                                 │
│  Blog-Titel in Poppins Bold    │
│  (max 3 Zeilen)                │
│                                 │
│  • Bullet Point 1              │
│  • Bullet Point 2              │
│  • Bullet Point 3              │
│                                 │
│  ─────────────────────────     │
│  SUNSIDE AI    sunsideai.de >> │
└─────────────────────────────────┘
```

20 verschiedene Icons stehen bereit:

| Dateiname | Icon | Thema |
|-----------|------|-------|
| blog-chatbot | 🤖 | Chatbots |
| blog-immobilie | 🏠 | Immobilien |
| blog-telefon | 📱 | Telefonassistenz |
| blog-seo | 🔍 | SEO |
| blog-analytics | 📊 | Daten & Analytics |
| blog-ki | 🧠 | Künstliche Intelligenz |
| blog-automatisierung | ⚙️ | Automatisierung |
| blog-email | ✉️ | E-Mail Marketing |
| blog-website | 🌐 | Webdesign |
| blog-datenschutz | 🛡️ | Datenschutz |
| blog-speed | ⚡ | Geschwindigkeit |
| blog-team | 👥 | Team & HR |
| blog-schluessel | 🔑 | Prozesse |
| blog-zeit | 🕐 | Zeitmanagement |
| blog-umsatz | 💶 | Umsatz & Finanzen |
| blog-marketing | 📣 | Marketing |
| blog-expose | 📄 | Dokumente |
| blog-bewertung | ⭐ | Bewertungen |
| blog-zielgruppe | 🎯 | Zielgruppen |
| blog-vernetzung | 🔗 | Integration |

---

## Implementierungsreihenfolge

### Phase 1: Foundation (Tag 1-2)
- [ ] Repo aufsetzen mit Verzeichnisstruktur
- [ ] Supabase-Schema deployen (6 Tabellen + Config)
- [ ] Core-Module: Config, Supabase Client, Claude Client
- [ ] .env Template und Railway Setup
- [ ] GSC Service Account einrichten (Google Cloud Console)

### Phase 2: SEO Intelligence (Tag 3-5)
- [ ] GSC Client implementieren (Search Console API)
- [ ] Autocomplete Client implementieren
- [ ] Content Crawler: sunsideai.de crawlen, Inventory aufbauen
- [ ] Einmaliger Komplett-Crawl ausführen (scripts/initial_crawl.py)
- [ ] Keyword Researcher: GSC-Daten + Autocomplete + Clustering
- [ ] Content Strategist: Opportunities identifizieren
- [ ] Test: Strategist findet realistische Keyword-Gaps

### Phase 3: Research Agent (Tag 6-7)
- [ ] RSS-Feed Liste validieren (welche URLs leben?)
- [ ] feedparser Integration
- [ ] Semantic Scholar API Integration
- [ ] Research Prompt finalisieren (mit Opportunity-Input)
- [ ] Test: Findet gezielt Studien zu identifizierten Keyword-Gaps

### Phase 4: Blog Writer (Tag 8-10)
- [ ] SEO-Prompt aus bestehendem Claude Project migrieren
- [ ] Blog Writer Agent mit Content-Awareness implementieren
- [ ] Interne-Link-Logik: Content Inventory → Link-Vorschläge
- [ ] Quality Gate Prompt + Agent
- [ ] GitHub API Integration (Auto-Commit)
- [ ] Test: Erstellt Blog-Post mit korrektem Keyword-Fokus + internen Links

### Phase 5: LinkedIn Distribution (Tag 11-12)
- [ ] LinkedIn-Prompt aus bestehendem Claude Project migrieren
- [ ] Infografik-Generator integrieren
- [ ] LinkedIn API Setup (OAuth, Token)
- [ ] LinkedIn Poster Agent
- [ ] Test: Erstellt und postet LinkedIn-Beitrag

### Phase 6: Orchestrierung & Monitoring (Tag 13-15)
- [ ] main.py Orchestrator mit Scheduling (alle 5 Agents + Timing)
- [ ] Morning Digest Notifications
- [ ] Review-Hold Mechanismus
- [ ] Dockerfile + Railway Deployment
- [ ] End-to-End Test: Vom GSC-Keyword über Research bis zum LinkedIn-Post

### Phase 7: Ramp-Up (Woche 3-6)
- [ ] Threshold auf 10 setzen, alle Posts manuell reviewen
- [ ] Prompt-Qualität iterieren basierend auf Output
- [ ] Threshold schrittweise senken
- [ ] SEO-Impact messen: Rankings tracken für autopilot-erstellte Posts
- [ ] Performance-Feedback-Loop einrichten

---

## Offene Entscheidungen

| Frage | Optionen | Status |
|-------|----------|--------|
| Notification-Kanal | Slack vs. E-Mail vs. beides | Offen |
| LinkedIn-Account | Pauls Profil vs. Sunside AI Company Page | Empfehlung: Pauls Profil |
| Blog-Bildformat | PNG (fertig) vs. WebP (kleiner) | PNG vorerst |
| Scheduling | Railway Cron vs. GitHub Actions | Empfehlung: Railway |
| Review-Dashboard | Supabase Studio vs. Custom UI vs. Slack | Slack für MVP |
| GSC Property Type | Domain Property vs. URL Prefix | Domain Property empfohlen |
| Keyword-Threshold | Ab wie vielen Impressions wird ein Keyword relevant? | Start: 10 Impressions |
| Content Refresh Strategie | Neuen Post oder bestehenden updaten? | Beides, je nach Case |

---

## Risiken & Mitigationen

| Risiko | Wahrscheinlichkeit | Mitigation |
|--------|---------------------|------------|
| Halluzinierte Statistiken | Mittel | Quality Gate prüft Fakten, Quellen werden verlinkt |
| LinkedIn Token abgelaufen | Sicher (alle 60 Tage) | Automatischer Reminder 7 Tage vorher |
| RSS-Feed geht offline | Niedrig | Agent loggt Fehler, überspringt, nutzt andere Quellen |
| SEO-Qualität sinkt | Niedrig | QA-Score Tracking, Threshold anpassbar |
| Google Penalty für AI-Content | Sehr niedrig | Menschlicher Review möglich, einzigartige Studien-Daten |
| Kosten explodieren | Sehr niedrig | Rate Limits konfiguriert, Max 5 Posts/Woche |
| GSC API Quota erschöpft | Sehr niedrig | 1.200 Queries/Minute, wir brauchen ~5 pro Woche |
| Google Autocomplete IP-Block | Niedrig | Throttling auf 10 Req/Minute, Fallback auf GSC-only |
| Keyword-Kannibalisierung | Mittel | Content Strategist prüft auf bestehenden Content, Blog Writer differenziert |
| Veraltetes Content Inventory | Niedrig | Wöchentlicher Recrawl, Sitemap als Source of Truth |

---

## SEO Feedback Loop

Langfristig entsteht ein sich selbst verbessernder Kreislauf:

```
Woche 1: GSC zeigt "ki makler" auf Position 18
         → Strategist: Keyword Gap erkannt
         → Research: Studie zu KI im Maklerbüro gefunden
         → Blog Writer: Post mit Keyword-Fokus erstellt
         
Woche 4: GSC zeigt "ki makler" jetzt auf Position 9
         → Strategist: Low-Hanging Fruit erkannt
         → Blog Writer: Zweiten Beitrag mit verwandtem Keyword erstellt
         → Interner Link vom neuen zum alten Post
         
Woche 8: GSC zeigt "ki makler" auf Position 4
         → Strategist: Content Cluster aufbauen
         → Pillar Page + Supporting Content Strategie

Woche 12: Cluster dominiert Seite 1 für 15 verwandte Keywords
```

Jede Woche liefern die GSC-Daten Feedback darüber, was funktioniert hat. Der Strategist lernt daraus (über die Prompt-Instructions) und priorisiert ähnliche Opportunities höher.
