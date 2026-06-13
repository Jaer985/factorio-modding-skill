# Factorio Modding Skill

An LLM-first instruction set for developing, debugging, and maintaining **Factorio 2.0 / Space Age** mods with zero-assumption rigor, compatibility-first design, and research-driven development.

Drop these files into any AI coding assistant that supports custom instructions or agent skills — including Cursor, Windsurf, Claude Code, GitHub Copilot, Gentle AI, OpenCode, or any LLM-based coding tool.

## Features

- **Zero-Assumption Dynamic RAG** — The static `references/` files are deprecated. The AI uses a dynamic vectorization pipeline that indexes the official Factorio 2.0 specs (Runtime API, Data Lifecycle, Prototypes) using structured embeddings to optimize context windows and ensure determinism.
- **verify_prototype_definition(type, name) tool** — Integrated native Function Calling in OpenCode to contrast mod schemas in `data.lua` against the official JSON specification in real time.
- **Automated Log Watcher** — Asynchronous file watcher on `factorio-current.log` that automatically intercepts stack traces on engine crashes or Lua runtime errors to formulate technical hypotheses before patching.
- **Strict Pre-Execution Linting** — Integrates `luacheck` configured with the `std+factorio` environment as a blocking step in the internal CI loop to reject undeclared globals or invalid typing.
- **2.0 / Space Age Ready** — Full coverage of the 2.0 C++ engine changes, new API signatures, quality system, space platforms, elevated rails, and more.
- **Compatibility-First** — Namespace conventions, safe inter-mod patterns, dependency management, and conflict detection to prevent mod collisions.
- **UPS Optimization** — Event filtering, tick throttling, entity tracking patterns, and C++ vs Lua performance tradeoffs.
- **Modular Scaffolding Templates** — Ready-to-use modular templates for `control.lua`, `data.lua`, `settings.lua`, `info.json`, a modular `dispatcher.lua`, and a semantic `migration.lua` pipeline.

## Requirements

- Any AI coding assistant that supports custom instructions, system prompts, or agent skill files (Cursor, Windsurf, Claude Code, GitHub Copilot, Gentle AI, OpenCode, or any LLM-based coding tool).

## Installation

### Option 1: npx skills (Any Agent — Recommended)

```bash
npx skills add Jaer985/factorio-modding-skill
```

This discovers `SKILL.md` at the repo root and installs it for your agent (Claude Code, Cursor, Copilot, and 67+ more).

### Option 2: OpenCode

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

1. **Before writing data-stage prototypes** — execute the native `verify_prototype_definition(type, name)` tool to validate schema specifications.
2. **Consult Factorio 2.0 dynamic RAG** — instead of legacy static Markdown files, verify API signatures using vectorized docs.
3. **Ingest log crash dumps** — monitor `factorio-current.log` asynchronously to diagnose errors and devises technical hypotheses before patching.
4. **Pass CI Linting** — block executions if any undeclared globals or typing violations are caught by `luacheck`.
5. **Implement Modular Event Dispatchers** — structure mod control files using dispatchers to optimize UPS.
6. **Integrate Semantic Migration Pipelines** — prevent multiplayer desyncs by checking version mutations on `storage` inside `on_configuration_changed`.
7. **Namespace everything** — all prototypes, settings, and remote interfaces will be prefixed with the mod name to avoid collisions.
8. **Add guards** — every `data.raw` access, remote interface call, and storage read will be safely guarded.

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

The main `SKILL.md` is the runtime contract. Detailed knowledge is processed dynamically via the RAG pipeline. The static `references/` directory is deprecated:

| File | Status | Content |
|------|--------|---------|
| `references/*` | DEPRECATED | Static legacy patterns (moved to dynamic RAG) |
| `assets/templates/boilerplate-control.lua` | ACTIVE | Orchestrates modular control flow |
| `assets/templates/boilerplate-dispatcher.lua` | ACTIVE | Modular event dispatcher template (routes callbacks to minimize loop overhead) |
| `assets/templates/boilerplate-migration.lua` | ACTIVE | Semantic migration pipeline template (handles version storage updates) |
| `assets/templates/boilerplate-data.lua` | ACTIVE | Safe prototype definitions with wrapped icons and standard 2.0 trigger syntax |
| `assets/templates/boilerplate-settings.lua` | ACTIVE | Boilerplate for global and startup settings |
| `assets/templates/info.json` | ACTIVE | Mod metadata schema |

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
├── SKILL.md              # Runtime contract (rules, decision gates, dynamic RAG & tool specs)
├── README.md             # This file
├── LICENSE               # MIT License
├── references/           # DEPRECATED (Moved to Dynamic RAG Pipeline)
│   ├── ...
├── assets/
│   └── templates/        # Boilerplate templates
│       ├── boilerplate-control.lua
│       ├── boilerplate-dispatcher.lua
│       ├── boilerplate-migration.lua
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
