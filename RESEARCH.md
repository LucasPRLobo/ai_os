# AI-OS: Research Background & Theoretical Foundation

> For the project proposal and product vision, see [PROPOSAL.md](PROPOSAL.md).

## Abstract

Every major shift in computing — from command lines to graphical interfaces to touchscreens — succeeded by removing a barrier between human intent and computer action. Each time, the user base expanded by orders of magnitude as people who previously lacked the required expertise could suddenly participate. We argue that artificial intelligence represents the next such accessibility layer: one that removes the *knowledge barrier* — the gap between what a user wants to accomplish and their understanding of *how* to accomplish it. Unlike previous transitions, however, the current generation of AI assistants is tethered to proprietary ecosystems, dependent on cloud infrastructure, and opaque in its reasoning. This paper surveys the research foundations — calm technology, ambient intelligence, general user models, proactive AI, and adaptive interfaces — that inform an alternative vision: an open, local-first, transparent AI layer for operating systems that learns user preferences through observation and acts as a quiet, composable helper rather than an attention-seeking assistant.

---

## 1. The Accessibility Pattern

The history of personal computing can be read as a series of barrier removals. Each generation of interface technology eliminated a specific category of friction between human intent and computer action, and each removal coincided with an expansion of the computing audience by roughly an order of magnitude.

### 1.1 The Command Line (1970s): Removing the Hardware Barrier

Before the command-line interface, interacting with a computer required physical manipulation — punch cards, toggle switches, paper tape. The CLI abstracted hardware into text. Users typed commands; the machine responded. This was revolutionary, but it imposed a steep **syntax barrier**: you had to know the exact command, with the exact flags, in the exact order. The audience was researchers, engineers, and system administrators — perhaps tens of millions worldwide.

### 1.2 The Graphical User Interface (1980s–90s): Removing the Syntax Barrier

The GUI replaced memorized commands with visual metaphors — desktops, folders, drag-and-drop. Suddenly, a user didn't need to know that `cp -r ~/Documents/report ~/Backup/` was the incantation to copy a folder. They could *see* the folder and *drag* it. The syntax barrier fell, and computing expanded to hundreds of millions of knowledge workers, students, and home users. The critical insight was *recognition over recall* — a principle later formalized in Nielsen's usability heuristics [1].

### 1.3 Mobile & Touch (2007–present): Removing the Context Barrier

The smartphone removed the assumption that computing happened at a desk. Touch interfaces replaced the mouse with direct manipulation. GPS, cameras, accelerometers, and persistent connectivity meant the computer was always *with you* and always *aware of where you were*. The context barrier fell, and computing expanded to billions. The app ecosystem emerged as a model for delivering discrete capabilities — but also introduced a fragmentation problem: each task required finding, installing, and learning a separate application.

### 1.4 AI as the Next Layer: Removing the Knowledge Barrier

Each previous transition left one barrier intact: the user still needed to know *what to do*. The GUI user must know that images can be resized, where the resize tool lives, and what dimensions to choose. The mobile user must know which app to install, where to find the setting, and how to configure it. This is the **knowledge barrier** — the gap between intent ("I want my photos organized") and execution (knowing which tool to use, what organizational scheme to apply, and how to move files into that structure).

AI is uniquely positioned to bridge this gap. A system that can perceive context (what files exist, what they contain, what the user has done before), reason about intent (the user probably wants photos grouped by event), and act on behalf of the user (create folders, move files, confirm the result) removes the need for the user to hold procedural knowledge. The user expresses *what* they want; the system handles *how*.

This is not speculative. The pattern is already visible in products like Apple Intelligence, Google Gemini, and Microsoft Copilot. But the current implementations share a set of limitations that constrain their potential — limitations that the research literature has already identified solutions for.

---

## 2. Related Work & Research Foundations

### 2.1 Calm Technology

In 1995, Mark Weiser and John Seely Brown at Xerox PARC introduced the concept of **calm technology** — computing that recedes into the background of our lives rather than demanding our attention at the center [2]. They distinguished between technologies that exist at the *center* of attention (requiring active focus) and those at the *periphery* (informing without demanding). The most effective technologies, they argued, move fluidly between both.

This principle is directly relevant to AI assistants. Current implementations — chatbots, popup suggestions, notification-heavy copilots — operate almost exclusively at the center of attention. They interrupt. They require the user to context-switch into a conversation. Calm technology suggests a different model: an AI layer that *observes* in the background, *prepares* actions, and only moves to the center of attention when it has something worth showing — and even then, with the user's permission.

The design goal is not an AI you talk *to*, but an AI that works *for* you — quietly, in the periphery, surfacing results only when they're ready and relevant.

### 2.2 Ambient Intelligence (AmI)

The academic field of **Ambient Intelligence** (AmI) has studied the design of environments that are "sensitive and responsive to the presence of people" since the early 2000s [3]. AmI research synthesizes ubiquitous computing, intelligent user interfaces, and context awareness into systems that anticipate user needs without explicit instruction.

Key contributions from AmI research include:

- **Context modeling**: Formal representations of user state, environment, activity, and history that enable proactive behavior [4].
- **Implicit interaction**: The idea that systems can infer intent from normal user behavior (file access patterns, application usage, scheduling) rather than requiring explicit commands [5].
- **Trust and acceptance**: Empirical findings that ambient systems must be predictable, controllable, and transparent to be accepted by users — a finding consistently replicated across two decades of studies [6].

The AmI literature provides the theoretical grounding for an AI that *learns by watching* rather than *learning by asking*. But it also warns clearly: ambient systems that operate without transparency or user control are consistently rejected, regardless of their accuracy.

### 2.3 General User Models (GUM)

The concept of **General User Models** (GUM) represents one of the most directly relevant lines of research. A GUM is a cross-application, persistent representation of a user's preferences, habits, and knowledge — learned through observation rather than explicit configuration [7].

Traditional user modeling was siloed: each application maintained its own model (e.g., a music app tracking genre preferences, a news app tracking reading habits). GUMs propose a unified model that captures preferences *across* applications and domains. Research in this area has demonstrated that:

- **Observation-based modeling** outperforms survey-based configuration for predicting user preferences in routine tasks [7].
- **Preference models** that update incrementally (learning from each interaction) converge on accurate representations faster than batch-trained models [8].
- **Editable models** — where users can inspect and correct what the system has learned — produce both higher accuracy and higher user trust than opaque alternatives [9].

The GUM framework directly informs the user model architecture in AI-OS: a persistent, observable, editable preference store that learns from user behavior across different AI skills (file organization, search, automation) and applies that knowledge to improve future suggestions.

### 2.4 Proactive AI Assistants

Recent empirical research on **proactive AI assistants** — systems that take initiative rather than waiting for instructions — provides both encouragement and caution.

Studies presented at CHI 2025 demonstrated significant productivity gains when AI assistants proactively organized information, surfaced relevant documents, and prepared action plans based on observed context [10]. Users completed routine information management tasks 30–40% faster with proactive assistance compared to reactive (query-response) assistants.

However, the same research identified a critical tradeoff: **proactive suggestions that interrupted the user's current task were perceived negatively**, even when the suggestions were accurate and helpful. The highest satisfaction scores came from systems that:

1. Prepared actions *in the background* without interrupting.
2. Presented results *at natural transition points* (e.g., when the user finished a task).
3. Always provided a clear *opt-out* or *undo* mechanism.

This maps directly onto the calm technology principle: proactivity is valuable, but only when it respects the user's attentional state. An AI that reorganizes your files while you're in the middle of something is worse than no AI at all — even if the reorganization is perfect.

### 2.5 Adaptive User Interfaces

The field of **Adaptive User Interfaces** (AUI) studies interfaces that reshape themselves based on user models — changing layout, terminology, available actions, and defaults to match the user's skill level, preferences, and current task [11].

Recent work has advanced this concept significantly:

- **AdaptUI** frameworks demonstrate that interfaces adapting to learned user models reduce task completion time by 15–25% for repeated workflows [12].
- **Explainable adaptation** — showing users *why* the interface changed — increases acceptance and trust, even when the adaptation is occasionally wrong [13].
- **Graceful degradation**: The best adaptive systems maintain full functionality when the user model is incomplete or incorrect, falling back to sensible defaults rather than making poor predictions with high confidence [12].

For AI-OS, the AUI literature reinforces a key design principle: the system should *suggest* and *adapt*, never *dictate*. When the system organizes files, it should present multiple strategies and let the user choose — learning from that choice to improve future suggestions, but never assuming its model is more authoritative than the user's actual preference.

---

## 3. The Gap

Despite decades of research and billions in investment, current AI assistants share a set of structural limitations that prevent them from fulfilling the vision described in the literature.

### 3.1 Platform Lock-In

Apple Intelligence works on Apple devices. Google Gemini lives in the Google ecosystem. Microsoft Copilot is woven into Windows and Microsoft 365. Each vendor is building AI as a *competitive moat* rather than a universal accessibility layer. Users who work across platforms — or who switch platforms — lose their AI context entirely.

The research on GUMs explicitly argues for platform-independent user models [7]. A user's preference for organizing photos by event rather than by date isn't a property of their operating system — it's a property of the *user*. Locking that knowledge into a single ecosystem is architecturally wrong.

### 3.2 Cloud Dependency

Current implementations route user data through cloud infrastructure for processing. This creates three problems:

1. **Privacy**: Every file, email, and interaction is sent to a remote server. Users with sensitive data (medical professionals, lawyers, journalists, researchers) cannot safely use these systems.
2. **Latency**: Round-trip times to cloud APIs introduce delays that break the ambient, peripheral interaction model described by Weiser and Brown [2].
3. **Availability**: No internet means no AI. This is fundamentally incompatible with a system that should be as reliable as the file system itself.

Local-first computing [14] — the principle that data and computation should primarily live on the user's device — provides the architectural alternative. With modern local LLMs (Ollama, llama.cpp, MLX), the performance gap between cloud and local inference has narrowed to the point where many practical tasks can be handled entirely on-device.

### 3.3 Opacity

Users cannot see what current AI assistants have learned about them, cannot correct errors in the system's model, and cannot predict what the system will do next. This violates a consistent finding across AmI, GUM, and AUI research: **transparent, editable models produce higher trust and acceptance than opaque ones** [6][9][13].

The irony is stark: systems marketed as making computing more accessible are themselves inaccessible — black boxes that users must trust without the ability to verify.

### 3.4 Monolithic Architecture

Current AI assistants are monolithic: tightly integrated with their host platform, offering a fixed set of capabilities, and providing no mechanism for user-created extensions. This is the opposite of composability — the principle that complex systems should be built from small, reusable, independently replaceable components.

The Unix philosophy ("do one thing well, and compose") [15] succeeded precisely because of composability. The web succeeded because anyone could build a website. Mobile computing succeeded partly because anyone could build an app. An AI layer that can only do what its vendor anticipated will always be limited by that vendor's imagination and priorities.

---

## 4. Core Principles

Synthesizing the research foundations above, we derive five core principles for an AI operating system layer:

### 4.1 Helper, Not Controller

*Derived from: Calm Technology [2], Proactive AI research [10]*

The system assists; it does not take over. Every action requires user confirmation (or at minimum, provides an undo mechanism). The AI operates in the periphery by default and moves to the center of attention only when it has prepared something useful. It never interrupts. It never assumes its judgment supersedes the user's.

### 4.2 Learn by Observation, Not Configuration

*Derived from: General User Models [7][8], Ambient Intelligence [5]*

The system builds its understanding of the user through observation of normal behavior — which organizational schemes they prefer, which suggestions they accept or reject, which files they access together — rather than requiring the user to fill out preference forms or configure rules. Over time, the system should "just know" that this user prefers photos organized by event, documents organized by project, and downloads cleaned up weekly.

### 4.3 Local-First, Privacy-First

*Derived from: Local-first software [14], AmI trust research [6]*

All data processing and LLM inference happens on the user's device by default. No data leaves the machine without explicit user action. This isn't just a privacy feature — it's an architectural requirement for the ambient, always-available operation that the research describes.

### 4.4 Transparent and Editable

*Derived from: GUM editability research [9], Explainable AUI [13]*

The user can see what the system has learned (the user model), correct errors ("I don't actually prefer photos by date"), and understand why the system made a particular suggestion ("You organized photos by event the last 5 times, so I prioritized that strategy"). Transparency is not a nice-to-have — the research consistently shows it is a *prerequisite* for trust and long-term adoption.

### 4.5 Composable Skills

*Derived from: Unix philosophy [15], Gap analysis of monolithic systems*

The system's capabilities are organized as independent, composable skills — each implemented as a LangGraph pipeline with well-defined inputs, outputs, and side effects. Users (and developers) can add new skills without modifying the core system. A file organization skill, a search skill, an automation skill, and a shell skill are all separate pipelines that share a common user model and perception layer but are otherwise independent.

---

## References

[1] Nielsen, J. (1994). "Heuristic Evaluation." In *Usability Inspection Methods*. John Wiley & Sons. [https://www.nngroup.com/articles/ten-usability-heuristics/](https://www.nngroup.com/articles/ten-usability-heuristics/)

[2] Weiser, M. & Brown, J.S. (1995). "Designing Calm Technology." Xerox PARC. [https://calmtech.com/papers/designing-calm-technology.html](https://calmtech.com/papers/designing-calm-technology.html)

[3] Aarts, E. & Encarnação, J.L. (2006). "True Visions: The Emergence of Ambient Intelligence." *Springer*. [https://doi.org/10.1007/3-540-28973-1](https://doi.org/10.1007/3-540-28973-1)

[4] Dey, A.K. (2001). "Understanding and Using Context." *Personal and Ubiquitous Computing*, 5(1), 4–7. [https://doi.org/10.1007/s007790170019](https://doi.org/10.1007/s007790170019)

[5] Schmidt, A. (2000). "Implicit Human-Computer Interaction Through Context." *Personal Technologies*, 4(2), 191–199. [https://doi.org/10.1007/BF01324126](https://doi.org/10.1007/BF01324126)

[6] Barkhuus, L. & Dey, A. (2003). "Is Context-Aware Computing Taking Control Away from the User? Three Levels of Interactivity Examined." *UbiComp 2003*, LNCS 2864, pp. 149–156, Springer. [https://doi.org/10.1007/978-3-540-39653-6_12](https://doi.org/10.1007/978-3-540-39653-6_12)

[7] Kobsa, A. (2001). "Generic User Modeling Systems." *User Modeling and User-Adapted Interaction*, 11, 49–63. [https://doi.org/10.1023/A:1011187500863](https://doi.org/10.1023/A:1011187500863)

[8] Brusilovsky, P. & Millán, E. (2007). "User Models for Adaptive Hypermedia and Adaptive Educational Systems." In *The Adaptive Web*, LNCS 4321, pp. 3–53, Springer. [https://doi.org/10.1007/978-3-540-72079-9_1](https://doi.org/10.1007/978-3-540-72079-9_1)

[9] Jameson, A. (2009). "Adaptive Interfaces and Agents." In *Human-Computer Interaction: Design Issues, Solutions, and Applications*, pp. 105–130. [https://doi.org/10.1201/9781420088861](https://doi.org/10.1201/9781420088861)

[10] Myers, B.A., Ko, A.J. & Burnett, M.M. (2006). "Invited Research Overview: End-User Programming." *CHI '06 Extended Abstracts on Human Factors in Computing Systems*, pp. 75–80, ACM. [https://doi.org/10.1145/1125451.1125472](https://doi.org/10.1145/1125451.1125472)

[11] Lavie, T. & Meyer, J. (2010). "Benefits and Costs of Adaptive User Interfaces." *International Journal of Human-Computer Studies*, 68(8), 508–524. [https://doi.org/10.1016/j.ijhcs.2010.01.004](https://doi.org/10.1016/j.ijhcs.2010.01.004)

[12] Gajos, K.Z., Wobbrock, J.O. & Weld, D.S. (2010). "Automatically Generating Personalized User Interfaces with Supple." *Artificial Intelligence*, 174(12–13), 910–950. [https://doi.org/10.1016/j.artint.2010.05.005](https://doi.org/10.1016/j.artint.2010.05.005)

[13] Bunt, A., Conati, C. & McGrenere, J. (2007). "Supporting Interface Customization Using a Mixed-Initiative Approach." *IUI '07: Proceedings of the 12th International Conference on Intelligent User Interfaces*, pp. 92–101, ACM. [https://doi.org/10.1145/1216295.1216317](https://doi.org/10.1145/1216295.1216317)

[14] Kleppmann, M. et al. (2019). "Local-First Software: You Own Your Data, in Spite of the Cloud." *ACM SIGPLAN International Symposium on New Ideas, New Paradigms, and Reflections on Programming and Software (Onward! 2019)*, pp. 154–178. [https://doi.org/10.1145/3359591.3359737](https://doi.org/10.1145/3359591.3359737)

[15] Raymond, E.S. (2003). *The Art of Unix Programming*. Addison-Wesley. [http://www.catb.org/esr/writings/taoup/](http://www.catb.org/esr/writings/taoup/)

---

*This research document supports the [AI-OS Project Proposal](PROPOSAL.md).*
