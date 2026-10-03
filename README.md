# ⚡ Curated Tech & Systems Engineering Feed Terminal

> **Live Deployments:**  
> * 🌐 **Cloudflare Workers:** [https://curated-tech-feeds.indian-equity-feeds.workers.dev](https://curated-tech-feeds.indian-equity-feeds.workers.dev)
> * 🐙 **GitHub Pages:** [https://aravind1998.github.io/curated-tech-feeds/](https://aravind1998.github.io/curated-tech-feeds/)

A fast, curated, zero-dependency engineering dashboard aggregating high-signal systems architecture deep dives, distributed systems post-mortems, performance benchmarks, and software design principles from world-class builders.

---

## 🎯 Curated Publications Tracked

| Publication | Author / Team | Primary Focus Area |
| :--- | :--- | :--- |
| **Netflix TechBlog** | Netflix Engineering | Large-scale streaming infrastructure, chaos engineering, data platforms, microservices |
| **Cloudflare Blog** | Cloudflare Team | Edge compute, DDoS mitigation, Rust networking primitives, BGP, CDN routing |
| **GitHub Engineering** | GitHub Engineering | High-availability Git hosting, CI/CD scale, database sharding, developer tooling |
| **Meta Engineering** | Meta Engineering Team | Billion-user infrastructure, AI hardware clusters, kernel tuning, custom silicon |
| **ByteByteGo** | Alex Xu | Visual system design blueprints, distributed consensus, caching patterns, databases |
| **The Pragmatic Engineer**| Gergely Orosz | In-depth engineering case studies, tech architecture, software leadership |
| **Martin Fowler** | Martin Fowler & ThoughtWorks | Microservices, event-driven architectures, domain-driven design, refactoring |
| **Dan Luu** | Dan Luu | Empirical hardware benchmarks, SSD/NVMe latency, CPU caching, post-mortems |
| **Julia Evans** | Julia Evans (Wizard Zines) | DNS, packet sniffers, Linux syscalls, Git internals, network debugging |
| **Fareed Khan (Medium)** | Fareed Khan | Visual guides, RAG pipeline architectures, transformer internals, agentic workflows |
| **Fareed Khan (GitHub)** | Fareed Khan | Open-source AI repositories, LLM implementation benchmarks, systems code |
| **Simon Willison** | Simon Willison | Practical LLM engineering, prompt injection defenses, modern Python web systems |
| **Mitchell Hashimoto** | Mitchell Hashimoto | Systems programming in Zig, terminal emulators, macOS graphics engines |
| **Antirez** | Salvatore Sanfilippo | Redis internals, low-level C programming, generative AI architectures |
| **AWS Architecture Blog**| AWS Solutions Architects | Well-Architected frameworks, multi-region failover, serverless orchestration |
| **Stripe Engineering** | Stripe Engineering | Zero-downtime database migrations, idempotent payment APIs, Sorbet Ruby |
| **Dropbox Tech** | Dropbox Engineering | Exabyte-scale custom storage (Magic Pocket), Rust sync engine rewrites |
| **Datadog Engineering** | Datadog Engineering | Trillion-event streaming pipelines, eBPF tracing, Kafka tuning, metrics |

---

## ⚡ Key Features

- **Instant Real-Time Search**: Sub-millisecond client-side filtering across 200+ articles by title, summary, author, or keyword (press `/` to search anytime).
- **Source Filtering Pills**: Single-click pills to isolate articles from individual engineering teams or authors.
- **Topic Tags**: Automatic topic categorization (`#DistributedSystems`, `#Architecture`, `#Performance`, `#Databases`, `#Cloud`, `#Linux`, `#AI`).
- **One-Click RSS Import**: Download [`feeds.opml`](./feeds.opml) to import all curated feeds directly into NetNewsWire, Feedly, Inoreader, or Readwise Reader.
- **Automated Refresh**: GitHub Actions workflow (`.github/workflows/update-feeds.yml`) continuously updates feed data and republishes to GitHub Pages.
- **Pure Static Architecture**: Zero external runtime dependencies, zero trackers, fast client-side rendering.

---

## 🚀 Local Development & Manual Refresh

To pull the latest feeds and rebuild the dashboard locally:

```bash
# Clone the repository
git clone https://github.com/Aravind1998/curated-tech-feeds.git
cd curated-tech-feeds

# Run the feed aggregator pipeline
python3 pull_feeds.py

# Open the dashboard in your browser
open index.html
```

---

### Author
Curated by [Aravind Suresh](https://aravind1998.github.io/).
