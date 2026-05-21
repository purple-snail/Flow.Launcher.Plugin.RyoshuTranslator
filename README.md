# Flow Launcher Plugin - Ryoshu Translator

A [Flow Launcher](https://www.flowlauncher.com/) plugin for quickly searching Ryōshū's **SANGRIA** (Succinct Abbreviation Naturally Germinates Rather Immaculate Art) abbreviations from _Limbus Company_.

Type `rs` followed by a SANGRIA acronym to instantly find its full translation, source, and reliability — all powered by the [Limbus Company wiki](https://limbuscompany.wiki.gg/wiki/Ry%C5%8Dsh%C5%AB).

## Features

- **Instant search** — type `rs LD`, `rs SYNC`, `rs BARF` — results appear immediately
- **Click to copy** — select a result to copy the full entry to your clipboard
- **Auto-caching** — data is cached locally for 1 hour to minimize wiki requests
- **Zero dependencies** — pure Python standard library, no extra packages needed
- **Custom icon** — features Ryōshū artwork

## Usage

| Action         | Keystrokes                         |
| -------------- | ---------------------------------- |
| Open menu      | `rs`                               |
| Search SANGRIA | `rs` + abbreviation (e.g. `rs LD`) |
| Refresh cache  | `rs refresh`                      |
| Cache info     | `rs`                           |

## Icon Credit

Plugin icon uses artwork by [**@teko1193**](https://x.com/teko1193/status/2002018470691823817) on X/Twitter.

## Installation

1. Open Flow Launcher
2. Type `pm install Ryoshu Translator`
3. Or download the latest release and extract to `%APPDATA%\FlowLauncher\Plugins\`

## Building from Source

```bash
git clone https://github.com/purple-snail/Flow.Launcher.Plugin.RyoshuTranslator.git
# No dependencies to install — just drop the folder into Flow Launcher's Plugins directory
```

## License

This project is a fan-made tool for _Limbus Company_ (Project Moon). All game-related content belongs to Project Moon.
