# Factorio Modding Skill

An LLM-first instruction set for developing, debugging, and maintaining **Factorio 2.0 / Space Age** mods with zero-assumption rigor, compatibility-first design, and research-driven development.

Drop these files into any AI coding assistant that supports custom instructions or agent skills — including Cursor, Windsurf, Claude Code, GitHub Copilot, Gentle AI, OpenCode, or any LLM-based coding tool.

## Features

- **Zero-Assumption Development** — the AI never assumes API signatures, prototype fields, or event parameters. Every method, event, and prototype is verified against official Factorio docs before use.
- **2.0 / Space Age Ready** — full coverage of the 2.0 C++ engine changes, new API signatures, quality system, space platforms, elevated rails, and more.
- **Compatibility-First** — namespace conventions, safe inter-mod patterns, dependency management, and conflict detection to prevent mod collisions.
- **Structured Troubleshooting** — categorised error reference (data stage, control stage, desyncs, GUI, migrations) with debugging flowcharts and log analysis patterns.
- **UPS Optimization** — event filtering, tick throttling, entity tracking patterns, and C++ vs Lua performance tradeoffs.
- **Web Research Protocol** — when the AI encounters something unknown, it follows a structured research workflow through official docs, forums, community resources, and web search.
- **Boilerplate Templates** — ready-to-use templates for `control.lua`, `data.lua`, `settings.lua`, and `info.json`.

## Requirements

- Any AI coding assistant that supports custom instructions, system prompts, or agent skill files (Cursor, Windsurf, Claude Code, GitHub Copilot, Gentle AI, OpenCode, or any LLM-based coding tool).

## Installation

### Option 1: npx skills (Any Agent — Recommended)

```bash
npx skills add Jaer985/factorio-modding-skill
```

This discovers `SKILL.md` at the repo root and installs it for your agent (Claude Code, Cursor, Copilot, and 67+ more).

### Option 2: OpenCode

Clone into the skills directory:

```bash
git clone https://github.com/Jaer985/factorio-modding-skill.git ~/.config/opencode/skills/factorio-modding
```

### Option 3: Cursor / Windsurf

1. Clone or download this repository.
2. Copy the contents of `SKILL.md` (and relevant `references/` files) into your project's `.cursorrules` or Windsurf rules file.
3. Or reference the skill path in your agent configuration.

### Option 5: Claude Code

Include as a reference in your `CLAUDE.md` or `instructions.md`:

```
## Factorio Modding Skill
Reference the factorio-modding skill at /path/to/factorio-modding/SKILL.md
Activate when working with .lua, info.json, or Factorio mod files.
```

### Option 6: GitHub Copilot

Copy relevant patterns from `references/01-patterns.md` into your `.github/copilot-instructions.md` or reference the repository in your agent instructions.

### Option 7: Any LLM (Manual Prompt)

Copy the contents of `SKILL.md` directly into your system prompt or conversation context when working on Factorio mods. You can also include specific `references/*.md` files as needed.

### Option 8: Per-Project Install (Git Submodule)

```bash
git submodule add https://github.com/Jaer985/factorio-modding-skill.git .ai/skills/factorio-modding
```

## Usage

The skill activates **automatically** when working with Factorio mod files. You don't need to manually load it.

### Automatic Triggers

| Context | Triggers |
|---------|----------|
| **File patterns** | `info.json`, `control.lua`, `data.lua`, `settings.lua`, `data-updates.lua`, `data-final-fixes.lua`, `migrations/*.lua`, `migrations/*.json` |
| **Keywords** | `factorio`, `modding`, `prototype`, `recipe`, `technology`, `desync`, `control.lua`, `data.raw`, `planet`, `quality`, `space-platform`, `migration` |

### What the AI Will Do

When the skill is active, the AI will:

1. **Before writing any code** — verify API signatures and prototype fields against the official Factorio Lua API docs.
2. **Check licenses** — before referencing or modifying third-party mod code.
3. **Namespace everything** — all prototypes, settings, and remote interfaces will be prefixed with your mod name.
4. **Add guards** — every `data.raw` access, remote interface call, and storage read will be safely guarded.
5. **Prevent desyncs** — no storage writes in `on_load`, deterministic-only operations, identical event registration.
6. **Optimize performance** — filtered events, throttled ticks, tracked entity patterns.
7. **Research unknowns** — if something isn't in the API docs, the AI will search the Factorio forums, wiki, and web before writing code.

### How to Activate

Different tools activate custom instructions in different ways:

| Platform | How to use this skill |
|----------|----------------------|
| **Any Agent** (npx skills) | `npx skills add Jaer985/factorio-modding-skill` — auto-discovered |
| **Cursor** | Paste contents into `.cursorrules` |
| **Windsurf** | Add to `.windsurfrules` |
| **Claude Code** | Reference in `CLAUDE.md` |
| **GitHub Copilot** | Add to `.github/copilot-instructions.md` |
| **Any LLM** | Paste `SKILL.md` into conversation context |

### Reference Files

The skill is modular. The main `SKILL.md` is the runtime contract, and detailed knowledge is in `references/`:

| File | Content |
|------|---------|
| `references/01-patterns.md` | Code examples: boilerplate, prototypes, remote interfaces, GUIs, migrations, locale |
| `references/02-troubleshooting.md` | Debugging guide: error categories, desync hunting, profiling |
| `references/03-compatibility.md` | Inter-mod patterns: namespacing, safe interop, conflict detection |
| `references/04-research-protocol.md` | Zero-assumption deep dive, web research workflow, source authority |
| `references/05-lua-performance.md` | UPS optimization: event filtering, entity tracking, table allocation |
| `references/06-cpp-engine.md` | 2.0 migration: C++ engine changes, API migration table, Space Age systems |
| `assets/templates/` | Boilerplate templates for quick mod scaffolding |

## What It Covers

### Factorio 2.0 / Space Age

- ✅ C++ engine changes and API migration
- ✅ Storage (`storage`) vs legacy `global`
- ✅ Single-table argument API signatures
- ✅ New collision mask format (layers dictionary)
- ✅ Quality system (native C++ in 2.0)
- ✅ Space platforms (`surface.platform`)
- ✅ Space elevator and planetary logistics
- ✅ Elevated rails
- ✅ Research triggers (no science packs)
- ✅ Fluid system 2.0

### Mod Development

- ✅ Data stage: `data.lua`, `data-updates.lua`, `data-final-fixes.lua`
- ✅ Control stage: events, remote interfaces, GUIs
- ✅ Settings: startup, runtime-global, runtime-per-user
- ✅ Prototypes: items, recipes, technologies, entities, fluids
- ✅ Custom planets, quality tiers, audio integration
- ✅ Locale: all section types, UTF-8
- ✅ Migrations: JSON renames and Lua scripts

### Quality & Safety

- ✅ Desync prevention
- ✅ UPS optimization patterns
- ✅ Inter-mod compatibility
- ✅ License compliance
- ✅ Deterministic execution
- ✅ Safe logging and debugging

## Development

### Structure

```
factorio-modding/
├── SKILL.md              # Runtime contract (frontmatter, hard rules, decision gates)
├── README.md             # This file
├── LICENSE               # MIT License
├── references/           # Detailed knowledge and examples
│   ├── 01-patterns.md
│   ├── 02-troubleshooting.md
│   ├── 03-compatibility.md
│   ├── 04-research-protocol.md
│   ├── 05-lua-performance.md
│   └── 06-cpp-engine.md
├── assets/
│   └── templates/        # Boilerplate templates
│       ├── boilerplate-control.lua
│       ├── boilerplate-data.lua
│       ├── boilerplate-settings.lua
│       └── info.json
└── .gitignore
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-improvement`
3. Commit your changes with conventional commits
4. Push: `git push origin feature/my-improvement`
5. Open a pull request

Please ensure:
- Frontmatter is valid YAML
- The main `SKILL.md` stays concise (< 1000 tokens) — put depth in `references/`
- All code examples are tested against Factorio 2.0
- Lua patterns follow deterministic and desync-safe practices

## License

MIT — see [LICENSE](./LICENSE).

## Authoritative Sources Referenced

- [Factorio Lua API (latest)](https://lua-api.factorio.com/latest)
- [Prototype API Reference](https://lua-api.factorio.com/latest/index-prototype.html)
- [Runtime API Reference](https://lua-api.factorio.com/latest/index-runtime.html)
- [Auxiliary API & Mod Structure](https://lua-api.factorio.com/latest/index-auxiliary.html)
- [wube/factorio-data](https://github.com/wube/factorio-data)
- [data.raw Wiki](https://wiki.factorio.com/Data.raw)
- [Lua 5.2 Reference Manual](https://www.lua.org/manual/5.2/)
- [Factorio Changelogs](https://factorio.com/blog/)
