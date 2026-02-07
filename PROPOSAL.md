# AI-OS: Project Proposal & Product Vision

> For the research foundations behind this project, see [RESEARCH.md](RESEARCH.md).

## 1. Vision Statement

AI-OS is an open-source, local-first AI layer for desktop operating systems. It is not a chatbot. It is not an app. It is a background intelligence that observes how you use your computer, learns your preferences over time, and quietly helps — organizing files, surfacing information, automating routines — without requiring you to become an expert in the tools you use. Think of it as the accessibility layer that comes after the GUI: one that removes the knowledge barrier between what you want to do and how to do it.

---

## 2. Problem

Computers are extraordinarily powerful and extraordinarily difficult to use well. Every generation of interface technology — CLI, GUI, mobile touch — expanded the user base by removing a specific barrier (syntax, visual metaphor, context). But one barrier remains: **the knowledge barrier**. Users must still know *what to do* — which tool to use, which settings to configure, which workflow to follow.

AI is positioned to remove this barrier. A system that can perceive your files, understand your intent, and act on your behalf can bridge the gap between "I want my photos organized" and the dozen steps required to make it happen.

But the current generation of AI assistants has critical limitations:

- **Platform lock-in.** Apple Intelligence, Google Gemini, and Microsoft Copilot are ecosystem weapons, not universal tools. Your AI context doesn't travel with you.
- **Cloud dependency.** Your files, emails, and habits are routed through remote servers. No internet means no AI. Sensitive data means no AI.
- **Opacity.** You can't see what the AI has learned about you, can't correct its mistakes, and can't predict what it will do next.
- **Monolithic design.** Fixed capabilities, no user extensibility, no composability.

There is no open, local-first, transparent, extensible AI layer for operating systems. That's the gap.

---

## 3. Solution: AI-OS

AI-OS is an ambient AI layer that sits between the operating system and the user. It is built on three primitives:

### Perception

The system observes the computing environment — file system state, file contents (including images via vision models), metadata, user behavior patterns — without requiring the user to describe or configure what it should pay attention to.

### Memory

A persistent, transparent, editable **user model** records learned preferences, past decisions, and behavioral patterns. Inspired by General User Model (GUM) research, this model is:
- **Cross-skill**: Preferences learned in file organization inform search and automation.
- **Observable**: The user can inspect exactly what the system has learned.
- **Correctable**: The user can edit or delete any learned preference.
- **Incremental**: The model updates with each interaction, converging on accurate representations over time.

### Action

The system prepares actions based on perception and memory, then presents them for user confirmation. Following calm technology principles, it operates in the background and surfaces results at natural transition points — never interrupting, always providing opt-out and undo mechanisms.

---

## 4. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                           │
│              (CLI / Tray App / System Notifications)             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                      Action Layer                               │
│         Execute · Confirm · Dry-Run · Undo · Learn              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    Skill / Plugin System                         │
│              (LangGraph Pipelines — Composable)                  │
│                                                                  │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│   │    File       │  │   Search     │  │   Automation         │  │
│   │  Organizer    │  │   (v0.2)     │  │    (v0.3)            │  │
│   │   (v0.1) ✓   │  │              │  │                      │  │
│   └──────────────┘  └──────────────┘  └──────────────────────┘  │
│   ┌──────────────┐  ┌──────────────┐                            │
│   │ Intelligent  │  │   Custom     │                            │
│   │    Shell     │  │   Skills     │                            │
│   │   (v0.4)     │  │  (user-built)│                            │
│   └──────────────┘  └──────────────┘                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    Perception Layer                              │
│       File System · Vision · Metadata · Context Awareness       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                 User Model (Memory)                              │
│     Preference Store · Learned Patterns · History · Stats       │
│                  (~/.ai_os/preferences.json)                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    LLM Providers                                │
│              Ollama (local) · Future: API fallback              │
└─────────────────────────────────────────────────────────────────┘
```

### Key Architectural Decisions

- **LangGraph for orchestration.** Each skill is a directed graph of processing nodes with shared state. This provides composability (nodes are reusable), observability (state is inspectable at every step), and reliability (conditional routing, error handling at each node).
- **Pydantic for data modeling.** Strict type validation ensures that data flowing between nodes is well-structured. The LLM is constrained to output valid JSON matching Pydantic schemas.
- **Ollama for local inference.** All LLM calls go to a local Ollama instance, supporting both language models (Llama 3.2) and vision models (LLaVA). No cloud dependency.
- **Persistent preference store.** User preferences are stored as human-readable JSON at `~/.ai_os/preferences.json`, making the user model fully transparent and editable.

---

## 5. Proof of Concept: v0.1 — Smart File Organizer

The v0.1 implementation validates the AI-OS architecture end-to-end. It is a fully functional, content-aware file organizer that demonstrates all three primitives (perception, memory, action) working together.

### Pipeline

The file organizer is implemented as a 10-node LangGraph pipeline:

```
Input Paths
    │
    ▼
[validate_input] ─── Check paths exist and are accessible
    │
    ▼
[scan_files] ─────── Recursively discover files, skip system dirs
    │
    ▼
[extract_metadata] ── File info, MIME type, content preview
    │
    ▼
[classify_files] ──── Route to specialized analyzers
    │
    ├─► [analyze_images] ── Vision LLM + EXIF extraction
    ├─► [analyze_text] ──── Text content analysis
    └─► [analyze_other] ─── Document metadata extraction
         │
         ▼
[aggregate_results] ─ Combine analysis, detect patterns
    │
    ▼
[analyze_with_llm] ── Generate 2-3 organization strategies
    │
    ▼
[confirm_selection] ── Interactive user choice
    │
    ▼
[learn_from_choice] ── Record preference for future use
```

### What It Demonstrates

| AI-OS Primitive | v0.1 Implementation |
|---|---|
| **Perception** | File scanning with recursive discovery, EXIF metadata extraction, vision LLM analysis (scene detection, object recognition, people counting), text content preview, MIME type classification |
| **Memory** | Persistent preference store at `~/.ai_os/preferences.json` tracking strategy preferences, folder name preferences, usage history, and aggregate statistics. Preferences are applied to reorder and boost future suggestions. |
| **Action** | Multi-strategy suggestion generation (content-based, activity-based, setting-based), interactive confirmation UI with preview, dry-run mode, copy-or-move execution, conflict resolution via timestamp suffixes |
| **User Control** | Multiple organization options presented (never a single "take it or leave it"), dry-run previews, explicit confirmation before any file movement, cancel at any point |
| **Transparency** | Each suggestion includes confidence scores and reasoning. The user model is a human-readable JSON file. The pipeline state is inspectable at every node. |
| **Local-First** | All processing via local Ollama instance. No data leaves the machine. Works offline. |

### Technical Stack

| Component | Technology |
|---|---|
| Orchestration | LangGraph (directed state graph) |
| Data Models | Pydantic (strict validation) |
| Language LLM | Ollama + Llama 3.2 (local) |
| Vision LLM | Ollama + LLaVA (local) |
| Image Metadata | Pillow + piexif (EXIF extraction) |
| CLI | Python argparse |

### Usage

```bash
# Analyze and suggest organization (default — no file movement)
python v0.1/main.py ~/Photos

# Execute with confirmation
python v0.1/main.py ~/Downloads --execute

# Dry run — preview what would happen
python v0.1/main.py ~/Documents --dry-run

# Auto-accept first suggestion (scripting)
python v0.1/main.py ~/Photos --execute --yes

# Copy instead of move, custom output directory
python v0.1/main.py ~/Messy --execute --copy --output ~/Organized
```

---

## 6. Roadmap

### v0.1: File Organization (complete)

Content-aware file organizer with vision analysis, multi-strategy suggestions, preference learning, and interactive confirmation. Validates the core architecture.

### v0.2: Natural Language File Search

Search your files using natural language queries instead of exact filenames. "Find the presentation I worked on last Tuesday" or "Show me photos from the beach trip." Leverages the perception layer (file metadata, content preview, image analysis) and user model (access patterns, project associations) to rank results by relevance.

### v0.3: Context-Aware Automation

Event-driven triggers that respond to file system changes. "When a new screenshot appears on my desktop, move it to Screenshots and rename it based on content." "When I download a PDF, file it into the appropriate project folder." Each automation is a LangGraph pipeline activated by a file system watcher, with user-defined rules augmented by learned preferences.

### v0.4: Intelligent Shell

Natural language to shell commands. "Compress all the logs older than 30 days" translates to the appropriate `tar` + `find` pipeline. The system explains what it will do before executing, learns which commands the user is comfortable auto-approving, and builds a library of user-specific command patterns.

### v1.0: Unified Ambient Layer

The full vision: a background daemon with a system tray interface that integrates all skills into a cohesive ambient layer. Composable skill marketplace. Cross-skill user model. System-wide context awareness. Event-driven architecture. Plugin SDK for third-party developers.

---

## 7. Differentiation

| Capability | AI-OS | Apple Intelligence | Google Gemini | Microsoft Copilot |
|---|---|---|---|---|
| **Open Source** | Yes (MIT) | No | No | No |
| **Local-First** | Yes — all inference on-device | Partial — some on-device, some cloud | No — cloud-dependent | No — cloud-dependent |
| **OS-Agnostic** | Yes — Linux, macOS, Windows | Apple only | Chrome OS / Android primary | Windows / M365 primary |
| **Extensible** | Yes — LangGraph skill plugins | No | Limited (Gems/Extensions) | Limited (Copilot plugins) |
| **Transparent User Model** | Yes — inspectable, editable JSON | No | No | No |
| **Privacy** | No data leaves the device | Data processed by Apple | Data processed by Google | Data processed by Microsoft |
| **Offline Support** | Full functionality | Partial | No | No |
| **Composable Skills** | Yes — independent pipelines | No — monolithic | No — monolithic | No — monolithic |
| **User Control** | Confirm/deny every action | Limited | Limited | Limited |
| **Cost** | Free (requires local hardware) | Included with Apple devices | Subscription | Subscription |

---

## 8. Market Context

The ambient intelligence market is projected to grow from **$29.4 billion (2023) to $172.3 billion by 2032**, at a CAGR of 21.7% (Fortune Business Insights, 2024). This growth is driven by advances in edge computing, local AI inference, and increasing privacy concerns with cloud-dependent solutions.

Within this market, there is a conspicuous gap: **there is no open-source, OS-agnostic ambient AI layer**. The three dominant players (Apple, Google, Microsoft) are building proprietary, ecosystem-locked solutions. The open-source AI community has produced exceptional models (Llama, Mistral, Phi) and inference engines (Ollama, llama.cpp, vLLM) but has not yet assembled these into a coherent ambient computing experience.

**Key market dynamics:**

- **Local inference is now practical.** Models like Llama 3.2 3B run comfortably on consumer hardware. Vision models like LLaVA enable multimodal perception without cloud APIs. The hardware barrier to local AI is falling rapidly.
- **Privacy regulation is accelerating.** GDPR, CCPA, and emerging AI regulations create legal friction for cloud-dependent AI systems. Local-first architectures sidestep these concerns entirely.
- **Developer ecosystem is ready.** LangGraph, Ollama, Pydantic, and the broader Python AI ecosystem provide the building blocks. What's missing is the integration layer — the "operating system" for AI skills.
- **Users are underserved.** Linux users have no ambient AI option at all. macOS and Windows users are locked into their vendor's vision. Power users who want control and transparency have nowhere to go.

---

## 9. Call to Action

AI-OS is an open-source project seeking contributors, research collaborators, and supporters.

### For Developers

The codebase is designed for contribution. Each skill is an independent LangGraph pipeline. The node architecture means you can add a new processing step (a new analyzer, a new action type, a new data source) without touching the rest of the system. If you've ever wanted to build the AI layer that operating systems *should* have, this is where to start.

**Areas needing help:**
- v0.2 natural language search implementation
- File system event watchers for v0.3 automation triggers
- macOS and Windows compatibility testing
- Additional LLM provider integrations (Anthropic, OpenAI as optional cloud fallbacks)
- System tray / desktop notification interface

### For Researchers

The architecture is built on real research foundations (see [RESEARCH.md](RESEARCH.md)). We're interested in collaboration on:
- User model design and evaluation (GUM-inspired preference learning)
- Proactive assistance interaction patterns (when and how to surface suggestions)
- Adaptive interface design for AI-augmented workflows
- Privacy-preserving local inference optimization
- Longitudinal studies on AI-assisted file management behavior

### For Organizations

If your team, lab, or fund is interested in open-source ambient AI, local-first computing, or accessible human-computer interaction, we'd like to talk. AI-OS is looking for:
- Research partnerships
- Open-source funding / grants
- Early adopter feedback from teams with specific file management pain points
- Hardware partnerships for local inference optimization

---

**AI-OS is MIT licensed. The code is on GitHub. The conversation is open.**

*Built with LangGraph, Ollama, and the conviction that AI should make computers work for people — not the other way around.*
