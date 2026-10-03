#!/usr/bin/env python3
"""
feed_reader.py - Curated Tech & Systems Engineering Feed Aggregator & Dashboard Generator

Fetches RSS/Atom feeds from top engineering blogs, distributed systems builders, and tech researchers.
Extracts clean summaries, reading times, and topic tags, and compiles a fast, interactive single-file UI dashboard.
"""

import concurrent.futures
import datetime
import email.utils
import html
import json
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

TECH_TAG_PATTERNS = {
    "Distributed Systems": ["DISTRIBUTED", "CONSENSUS", "RAFT", "PAXOS", "REPLICATION", "PARTITION", "CONSISTENCY", "FAULT TOLERANT", "SHARDING", "CAP THEOREM"],
    "Architecture": ["ARCHITECTURE", "MICROSERVICES", "EVENT-DRIVEN", "SYSTEM DESIGN", "DECOUPLING", "MONOLITH", "MIGRATION", "SCALE"],
    "Performance": ["LATENCY", "THROUGHPUT", "BENCHMARK", "OPTIMIZATION", "PROFILING", "EBPF", "MEMORY", "CPU", "P99", "ALLOCATION"],
    "Databases & Storage": ["POSTGRES", "SQL", "DATABASE", "REDIS", "VALKEY", "KAFKA", "STORAGE", "ROCKSDB", "INDEX", "TRANSACTION", "ACID", "LSM"],
    "Networking & Infra": ["NETWORKING", "BGP", "DNS", "TCP", "HTTP/3", "QUIC", "LOAD BALANCER", "ROUTING", "CDN", "FIREWALL"],
    "Cloud & Kubernetes": ["KUBERNETES", "K8S", "DOCKER", "CONTAINER", "AWS", "CLOUD", "TERRAFORM", "SERVERLESS"],
    "AI & LLMs": ["LLM", "LLMS", "AI", "GPT", "TRANSFORMER", "PROMPT", "INFERENCE", "EMBEDDINGS", "VECTOR", "RAG", "NEURAL", "AGENT", "AGENTIC", "CLAUDE", "GEMINI", "FINE-TUNING", "PRETRAINING", "DIFFUSION", "REASONING", "KIMI", "DEEPSEEK", "MCP", "ADK", "SEMANTIC SEARCH"],
    "Linux & Low-Level": ["LINUX", "KERNEL", "SYSCALL", "ZIG", "RUST", "C++", "COMPILER", "HARDWARE", "POSIX"],
    "Observability": ["OBSERVABILITY", "METRICS", "TRACING", "LOGGING", "PROMETHEUS", "GRAFANA", "DATADOG", "TELEMETRY", "OTEL"],
    "Reliability": ["CHAOS", "RESILIENCE", "OUTAGE", "POST-MORTEM", "FAILOVER", "RATE LIMIT", "CIRCUIT BREAKER", "SRE"],
    "Leadership & Culture": ["LEADERSHIP", "MANAGEMENT", "CULTURE", "HIRING", "MENTORSHIP", "STARTUP", "TEAM", "ORGANIZATION", "GOJEK"]
}


def clean_html(raw_html):
    if not raw_html:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', raw_html)
    clean = html.unescape(clean)
    clean = re.sub(r'Continue reading on .*?»', '', clean)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()


def parse_date(date_str):
    if not date_str:
        return datetime.datetime.now(), int(time.time())
    date_str = date_str.strip()

    # Try RFC 822 (RSS)
    try:
        parsed_tuple = email.utils.parsedate_tz(date_str)
        if parsed_tuple:
            ts = email.utils.mktime_tz(parsed_tuple)
            return datetime.datetime.fromtimestamp(ts), int(ts)
    except Exception:
        pass

    # Try ISO 8601 (Atom)
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            dt = datetime.datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
            return dt, int(dt.timestamp())
        except Exception:
            pass

    now = datetime.datetime.now()
    return now, int(now.timestamp())


def detect_topics(text):
    found = []
    text_upper = text.upper()
    for topic, keywords in TECH_TAG_PATTERNS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_upper):
                if topic not in found:
                    found.append(topic)
                break
    return found[:3]


def fetch_single_feed(feed_config, timeout=12):
    feed_url = feed_config["feed_url"]
    feed_id = feed_config["id"]
    ctx = ssl._create_unverified_context()

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
    }

    print(f"Fetching: {feed_config['name']} ({feed_url})...")
    req = urllib.request.Request(feed_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
            content = response.read()
    except Exception as e:
        print(f"  [ERROR] {feed_config['name']}: {e}", file=sys.stderr)
        return []

    articles = []
    try:
        root = ET.fromstring(content)
    except Exception as e:
        print(f"  [XML PARSE ERROR] {feed_config['name']}: {e}", file=sys.stderr)
        return []

    # Detect RSS vs Atom
    tag_clean = root.tag.lower()
    channel_el = root.find("channel")
    if "rss" in tag_clean or channel_el is not None:
        channel = channel_el if channel_el is not None else root
        items = channel.findall("item")
        for item in items[:15]:
            title_el = item.find("title")
            link_el = item.find("link")
            desc_el = item.find("description")
            content_el = item.find("{http://purl.org/rss/1.0/modules/content/}encoded")
            pub_date_el = item.find("pubDate")
            if pub_date_el is None:
                pub_date_el = item.find("{http://purl.org/dc/elements/1.1/}date")

            title = clean_html(title_el.text if (title_el is not None and title_el.text) else "Untitled")
            link = (link_el.text if (link_el is not None and link_el.text) else "").strip()
            if not link and link_el is not None:
                link = link_el.attrib.get("href", "").strip()

            body_html = ""
            if content_el is not None and content_el.text:
                body_html = content_el.text
            elif desc_el is not None and desc_el.text:
                body_html = desc_el.text

            summary = clean_html(body_html)
            word_count = len(summary.split())
            read_time = max(2, round(word_count / 180))

            if len(summary) > 280:
                summary = summary[:277] + "..."

            pub_str = pub_date_el.text if (pub_date_el is not None and pub_date_el.text) else ""
            dt, timestamp = parse_date(pub_str)

            topics = detect_topics(title + " " + summary)
            if not topics:
                topics = [feed_config.get("category", "Engineering").split("&")[0].strip()]

            articles.append({
                "id": f"{feed_id}_{abs(hash(link or title))}",
                "title": title,
                "link": link,
                "pub_date": dt.strftime("%d %b %Y"),
                "timestamp": timestamp,
                "summary": summary or f"Read full technical engineering analysis from {feed_config['name']}.",
                "read_time_mins": read_time,
                "source_id": feed_id,
                "source_name": feed_config["name"],
                "source_color": feed_config.get("color", "#0284c7"),
                "author": feed_config.get("author", feed_config["name"]),
                "category": feed_config.get("category", "Systems Engineering"),
                "topics": topics
            })

    elif "feed" in tag_clean:
        # Atom feed
        ns = "{http://www.w3.org/2005/Atom}"
        entries = root.findall(f"{ns}entry")
        if not entries:
            entries = root.findall("entry")
        for entry in entries[:15]:
            title_el = entry.find(f"{ns}title")
            if title_el is None:
                title_el = entry.find("title")
            title = clean_html(title_el.text if (title_el is not None and title_el.text) else "Untitled")

            link = ""
            link_candidates = entry.findall(f"{ns}link")
            if not link_candidates:
                link_candidates = entry.findall("link")
            for l in link_candidates:
                rel = l.attrib.get("rel", "alternate")
                if rel in ("alternate", ""):
                    link = l.attrib.get("href", "").strip()
                    break

            summary_el = entry.find(f"{ns}summary")
            if summary_el is None:
                summary_el = entry.find("summary")
            content_el = entry.find(f"{ns}content")
            if content_el is None:
                content_el = entry.find("content")

            raw_body = ""
            if content_el is not None and content_el.text:
                raw_body = content_el.text
            elif summary_el is not None and summary_el.text:
                raw_body = summary_el.text

            summary = clean_html(raw_body)
            word_count = len(summary.split())
            read_time = max(2, round(word_count / 180))

            if len(summary) > 280:
                summary = summary[:277] + "..."

            updated_el = entry.find(f"{ns}published")
            if updated_el is None:
                updated_el = entry.find(f"{ns}updated")
            if updated_el is None:
                updated_el = entry.find("published")
            if updated_el is None:
                updated_el = entry.find("updated")

            dt, timestamp = parse_date(updated_el.text if (updated_el is not None and updated_el.text) else "")

            topics = detect_topics(title + " " + summary)
            if not topics:
                topics = [feed_config.get("category", "Engineering").split("&")[0].strip()]

            articles.append({
                "id": f"{feed_id}_{abs(hash(link or title))}",
                "title": title,
                "link": link,
                "pub_date": dt.strftime("%d %b %Y"),
                "timestamp": timestamp,
                "summary": summary or f"Read full technical engineering analysis from {feed_config['name']}.",
                "read_time_mins": read_time,
                "source_id": feed_id,
                "source_name": feed_config["name"],
                "source_color": feed_config.get("color", "#0284c7"),
                "author": feed_config.get("author", feed_config["name"]),
                "category": feed_config.get("category", "Systems Engineering"),
                "topics": topics
            })

    print(f"  -> Extracted {len(articles)} articles from {feed_config['name']}")
    return articles


def build_dashboard_html(articles, feed_sources, output_file):
    articles_json = json.dumps(articles, ensure_ascii=False)
    sources_json = json.dumps(feed_sources, ensure_ascii=False)
    total_articles = len(articles)
    total_sources = len(feed_sources)
    build_time_str = datetime.datetime.now(datetime.timezone.utc).strftime("%d %b %Y, %H:%M UTC")

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Curated Tech & Systems Engineering Feeds | High-Signal Terminal</title>
  <link rel="canonical" href="https://aravind1998.github.io/curated-tech-feeds/">
  <meta name="description" content="Curated high-signal engineering blogs, systems architecture deep dives, and technical teardowns from world-class builders.">
  <meta property="og:title" content="Curated Tech & Systems Engineering Feeds">
  <meta property="og:description" content="Zero-noise engineering dashboard aggregating Netflix, Cloudflare, GitHub, Martin Fowler, Dan Luu, ByteByteGo, and top systems thinkers.">
  <meta property="og:url" content="https://aravind1998.github.io/curated-tech-feeds/">
  <style>
    :root {{
      --bg-primary: #0b0f19;
      --bg-secondary: #111827;
      --bg-card: #161f30;
      --bg-card-hover: #1e293f;
      --border-color: #27354f;
      --text-primary: #f8fafc;
      --text-secondary: #94a3b8;
      --text-muted: #64748b;
      --accent-blue: #0284c7;
      --accent-cyan: #38bdf8;
      --accent-green: #10b981;
      --accent-amber: #f59e0b;
      --accent-purple: #8b5cf6;
      --accent-red: #ef4444;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background-color: var(--bg-primary);
      color: var(--text-primary);
      line-height: 1.5;
      min-height: 100vh;
    }}
    header {{
      background: linear-gradient(180deg, #162033 0%, var(--bg-primary) 100%);
      border-bottom: 1px solid var(--border-color);
      padding: 30px 40px 20px 40px;
      position: sticky;
      top: 0;
      z-index: 100;
      backdrop-filter: blur(12px);
    }}
    .header-top {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      margin-bottom: 16px;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .brand-icon {{
      font-size: 26px;
      background: rgba(56, 189, 248, 0.12);
      border: 1px solid var(--accent-cyan);
      border-radius: 8px;
      padding: 6px 10px;
    }}
    .brand h1 {{
      font-size: 22px;
      font-weight: 700;
      letter-spacing: -0.02em;
    }}
    .brand p {{
      font-size: 13px;
      color: var(--text-secondary);
      margin-top: 2px;
    }}
    .header-actions {{
      display: flex;
      gap: 12px;
      align-items: center;
    }}
    .action-btn {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 14px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 600;
      text-decoration: none;
      transition: all 0.15s ease;
      cursor: pointer;
    }}
    .btn-opml {{
      background: rgba(14, 165, 233, 0.15);
      color: var(--accent-cyan);
      border: 1px solid rgba(14, 165, 233, 0.4);
    }}
    .btn-opml:hover {{
      background: rgba(14, 165, 233, 0.25);
    }}
    .btn-github {{
      background: #1f2937;
      color: var(--text-primary);
      border: 1px solid var(--border-color);
    }}
    .btn-github:hover {{
      background: #374151;
    }}
    .search-bar-wrap {{
      position: relative;
      margin-top: 10px;
    }}
    .search-input {{
      width: 100%;
      padding: 12px 16px 12px 42px;
      background-color: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      color: var(--text-primary);
      font-size: 14px;
      outline: none;
      transition: border-color 0.2s;
    }}
    .search-input:focus {{
      border-color: var(--accent-cyan);
      box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
    }}
    .search-icon {{
      position: absolute;
      left: 14px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-muted);
      font-size: 16px;
    }}
    .filter-pills {{
      display: flex;
      gap: 8px;
      overflow-x: auto;
      padding-top: 14px;
      padding-bottom: 4px;
      scrollbar-width: none;
    }}
    .filter-pills::-webkit-scrollbar {{
      display: none;
    }}
    .pill {{
      padding: 5px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 500;
      white-space: nowrap;
      cursor: pointer;
      background-color: var(--bg-card);
      border: 1px solid var(--border-color);
      color: var(--text-secondary);
      transition: all 0.15s ease;
    }}
    .pill:hover {{
      background-color: var(--bg-card-hover);
      color: var(--text-primary);
    }}
    .pill.active {{
      background-color: var(--accent-blue);
      border-color: var(--accent-blue);
      color: #ffffff;
      font-weight: 600;
    }}
    main {{
      max-width: 1440px;
      margin: 0 auto;
      padding: 24px 40px;
    }}
    .meta-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      font-size: 13px;
      color: var(--text-muted);
      flex-wrap: wrap;
      gap: 10px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
      gap: 20px;
    }}
    .card {{
      background-color: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
    }}
    .card:hover {{
      transform: translateY(-2px);
      border-color: #3b5074;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
      background-color: var(--bg-card-hover);
    }}
    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      gap: 8px;
    }}
    .source-tag {{
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 3px 8px;
      border-radius: 4px;
      color: #ffffff;
    }}
    .date-text {{
      font-size: 12px;
      color: var(--text-muted);
    }}
    .card-title {{
      font-size: 16px;
      font-weight: 600;
      line-height: 1.4;
      margin-bottom: 10px;
    }}
    .card-title a {{
      color: var(--text-primary);
      text-decoration: none;
      transition: color 0.15s ease;
    }}
    .card-title a:hover {{
      color: var(--accent-cyan);
    }}
    .card-summary {{
      font-size: 13px;
      color: var(--text-secondary);
      line-height: 1.6;
      margin-bottom: 16px;
      word-break: break-word;
    }}
    .card-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 12px;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      margin-top: auto;
    }}
    .topic-tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .topic-badge {{
      font-size: 11px;
      font-weight: 600;
      color: var(--accent-cyan);
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.25);
      border-radius: 4px;
      padding: 2px 7px;
      cursor: pointer;
    }}
    .topic-badge:hover {{
      background: rgba(56, 189, 248, 0.2);
    }}
    .read-btn {{
      font-size: 12px;
      font-weight: 600;
      color: var(--accent-cyan);
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      white-space: nowrap;
    }}
    .read-btn:hover {{
      text-decoration: underline;
    }}
    .empty-state {{
      grid-column: 1 / -1;
      text-align: center;
      padding: 60px 20px;
      color: var(--text-muted);
    }}
    footer {{
      text-align: center;
      padding: 40px 20px;
      border-top: 1px solid var(--border-color);
      color: var(--text-muted);
      font-size: 13px;
      margin-top: 40px;
    }}
    footer a {{
      color: var(--accent-cyan);
      text-decoration: none;
    }}
    @media (max-width: 768px) {{
      header {{
        padding: 20px;
      }}
      main {{
        padding: 16px;
      }}
      .grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>

  <header>
    <div class="header-top">
      <div class="brand">
        <div class="brand-icon">⚡</div>
        <div>
          <h1>Curated Tech & Systems Engineering Terminal</h1>
          <p>High-signal technical deep dives from Netflix, Cloudflare, Martin Fowler, Fareed Khan, ByteByteGo & world-class builders</p>
        </div>
      </div>
      <div class="header-actions">
        <a href="feeds.opml" download class="action-btn btn-opml" title="Download OPML for Feedly, NetNewsWire, Inoreader">
          📥 Download OPML
        </a>
        <a href="https://github.com/Aravind1998/curated-tech-feeds" target="_blank" rel="noopener noreferrer" class="action-btn btn-github">
          🐙 GitHub
        </a>
      </div>
    </div>

    <div class="search-bar-wrap">
      <span class="search-icon">🔍</span>
      <input type="text" id="searchInput" class="search-input" placeholder="Search architecture, distributed systems, caching, databases, or authors... (Press '/' to focus)" autofocus>
    </div>

    <div class="filter-pills" id="sourceFilters">
      <!-- Injected by JavaScript -->
    </div>
  </header>

  <main>
    <div class="meta-bar">
      <div id="resultCount">Loading articles...</div>
      <div>Last updated: {build_time_str} • {total_sources} Publications Tracked</div>
    </div>

    <div class="grid" id="articlesGrid">
      <!-- Article cards injected by JavaScript -->
    </div>
  </main>

  <footer>
    <p>Curated with passion by <a href="https://aravind1998.github.io/" target="_blank">Aravind Suresh</a> • Hosted on GitHub Pages</p>
  </footer>

  <script>
    const rawArticles = {articles_json};
    const feedSources = {sources_json};

    let activeSource = "all";
    let activeTopic = "all";
    let searchQuery = "";

    // Init UI
    function init() {{
      renderFilterPills();
      filterAndRender();

      document.getElementById('searchInput').addEventListener('input', (e) => {{
        searchQuery = e.target.value.toLowerCase().trim();
        filterAndRender();
      }});

      window.addEventListener('keydown', (e) => {{
        if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {{
          e.preventDefault();
          document.getElementById('searchInput').focus();
        }}
        if (e.key === 'Escape') {{
          document.getElementById('searchInput').value = '';
          searchQuery = '';
          activeSource = 'all';
          activeTopic = 'all';
          renderFilterPills();
          filterAndRender();
        }}
      }});
    }}

    function renderFilterPills() {{
      const container = document.getElementById('sourceFilters');
      let html = `<div class="pill ${{activeSource === 'all' && activeTopic === 'all' ? 'active' : ''}}" onclick="setSourceFilter('all')">All Sources (${{rawArticles.length}})</div>`;

      feedSources.forEach(s => {{
        const count = rawArticles.filter(a => a.source_id === s.id).length;
        const isActive = activeSource === s.id;
        html += `<div class="pill ${{isActive ? 'active' : ''}}" onclick="setSourceFilter('${{s.id}}')">${{s.name}} (${{count}})</div>`;
      }});

      container.innerHTML = html;
    }}

    function setSourceFilter(sourceId) {{
      activeSource = sourceId;
      activeTopic = "all";
      renderFilterPills();
      filterAndRender();
    }}

    function filterByTopic(topic, event) {{
      if (event) event.stopPropagation();
      activeTopic = topic;
      activeSource = "all";
      renderFilterPills();
      filterAndRender();
    }}

    function filterAndRender() {{
      let filtered = rawArticles;

      if (activeSource !== "all") {{
        filtered = filtered.filter(a => a.source_id === activeSource);
      }}

      if (activeTopic !== "all") {{
        filtered = filtered.filter(a => (a.topics || []).includes(activeTopic));
      }}

      if (searchQuery) {{
        filtered = filtered.filter(a => 
          (a.title && a.title.toLowerCase().includes(searchQuery)) ||
          (a.summary && a.summary.toLowerCase().includes(searchQuery)) ||
          (a.author && a.author.toLowerCase().includes(searchQuery)) ||
          (a.source_name && a.source_name.toLowerCase().includes(searchQuery)) ||
          (a.topics && a.topics.some(t => t.toLowerCase().includes(searchQuery)))
        );
      }}

      // Sort by publication timestamp descending
      filtered.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));

      renderArticles(filtered);
    }}

    function renderArticles(list) {{
      const grid = document.getElementById('articlesGrid');
      const countEl = document.getElementById('resultCount');

      countEl.innerText = `Showing ${{list.length}} technical articles`;

      if (list.length === 0) {{
        grid.innerHTML = `
          <div class="empty-state">
            <div style="font-size: 40px; margin-bottom: 12px;">🔍</div>
            <h3>No articles match your search or filter</h3>
            <p style="margin-top: 6px;">Try adjusting your keyword or clearing filters.</p>
          </div>
        `;
        return;
      }}

      grid.innerHTML = list.map(art => {{
        const topicBadges = (art.topics || []).map(t => `<span class="topic-badge" onclick="filterByTopic('${{t}}', event)">#${{t}}</span>`).join('');
        return `
          <div class="card">
            <div>
              <div class="card-header">
                <span class="source-tag" style="background-color: ${{art.source_color || '#0284c7'}};">
                  ${{art.source_name}}
                </span>
                <span class="date-text">${{art.pub_date}} • ${{art.read_time_mins}} min read</span>
              </div>
              <h2 class="card-title">
                <a href="${{art.link}}" target="_blank" rel="noopener noreferrer">${{art.title}}</a>
              </h2>
              <div class="card-summary">${{art.summary}}</div>
            </div>
            <div class="card-footer">
              <div class="topic-tags">${{topicBadges}}</div>
              <a href="${{art.link}}" target="_blank" rel="noopener noreferrer" class="read-btn">
                Read Article <span>↗</span>
              </a>
            </div>
          </div>
        `;
      }}).join('');
    }}

    init();
  </script>
</body>
</html>
"""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"Compiled interactive dashboard to: {output_file} ({os.path.getsize(output_file)} bytes)")


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_file = os.path.join(base_dir, "config", "curated_tech_feeds.json")
    data_dir = os.path.join(base_dir, "data")
    output_html = os.path.join(base_dir, "index.html")
    output_json = os.path.join(data_dir, "curated_tech_feed_data.json")

    os.makedirs(data_dir, exist_ok=True)

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    feeds = config.get("feeds", [])
    print(f"Found {len(feeds)} curated feeds in config. Fetching concurrently...")

    all_articles = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_feed = {executor.submit(fetch_single_feed, feed): feed for feed in feeds}
        for future in concurrent.futures.as_completed(future_to_feed):
            articles = future.result()
            all_articles.extend(articles)

    # Sort descending by timestamp
    all_articles.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    print(f"Total articles aggregated: {len(all_articles)}")

    # Save JSON cache
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, indent=2, ensure_ascii=False)
    print(f"Saved aggregated data to: {output_json}")

    # Build index.html
    build_dashboard_html(all_articles, feeds, output_html)


if __name__ == "__main__":
    main()
