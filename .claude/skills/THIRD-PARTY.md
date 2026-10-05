# Third-party skills

| Folder(s) | Source | Licence | Commit |
|---|---|---|---|
| `gsap-core`, `gsap-timeline`, `gsap-plugins`, `gsap-utils`, `gsap-performance` | https://github.com/greensock/gsap-skills (official GreenSock skills) | MIT, see `gsap-LICENSE` | `aed9cfd3277740755f6bfc1155c7aa645403b760` |
| `frontend-design` | https://github.com/anthropics/skills/tree/main/skills/frontend-design (official Anthropic skill) | Apache-2.0, see `frontend-design/LICENSE.txt` | `683bc88e56f3e09ba94f7055977f3d3aa499f202` |

Copied unmodified. Left out on purpose: `gsap-react`, `gsap-frameworks`, `gsap-scrolltrigger` (scroll-driven web pages, not video).
To update: re-copy from the source repo and bump the commit above.

Not vendored: Remotion skills (paid licence at 4+ staff, and not in our stack) and `threejs-skills` (unvetted community repo, 3D not needed yet).

## Fonts

**ABC Arizona Flare is not in this repo and must never be committed here.** This repo is public and the font's licence
(ABC Dinamo) excludes storing it on publicly available servers. `fmf-motion-graphics/scripts/render.mjs` reads it at
render time from the private repos cloned beside this one (`fmf-clients/_brand/fonts`), or from `$FMF_FONT_DIR`.
The copy held there is the **Unlicensed Trial**; a full licence is needed for production use.
