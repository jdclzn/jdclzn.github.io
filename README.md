# Drafts & Dragons

Drafts & Dragons is the source for [jdaclizon23.github.io](https://jdaclizon23.github.io), the personal website and blog of Jovanie Daclizon.

This website is a writing space shaped by a developer's voice. It blends technical curiosity with personal reflection, using the language of software, systems, debugging, architecture, and failure to talk about both code and life. Some posts are grounded in web development and engineering practice; others are reflective essays about grief, growth, memory, and the human side of building things.

## About the Website

Drafts & Dragons is built as a personal publishing home rather than a generic portfolio or theme demo. The site is meant to hold:

- developer essays and field notes
- software and web development insights
- architecture, workflow, and tooling reflections
- project updates and experiments
- personal writing told through a technical lens

The goal is simple: create a place where technical writing and personal storytelling can live side by side without feeling like separate identities.

## Stack

- [Jekyll](https://jekyllrb.com/)
- [Chirpy](https://github.com/cotes2020/jekyll-theme-chirpy)
- GitHub Pages
- Giscus for comments

## Local Development

Install dependencies:

```bash
bundle install
```

Start the site locally:

```bash
bash tools/run.sh
```

Or run Jekyll directly:

```bash
bundle exec jekyll serve --incremental --livereload --drafts
```

Build and validate the site:

```bash
bash tools/test.sh
```

## Banner Generation

Generate a PNG blog header banner from the repository root:

```bash
python3 tools/generate_post_banner.py
```

Command usage:

```text
usage: generate_post_banner.py [-h] [--preset {engineering,launch,reflection,signal,summit}] [--output OUTPUT] [--width WIDTH] [--height HEIGHT] [--background BACKGROUND] [--ink INK] [--seed SEED] [--list-presets]
```

Choose a different preset or output file:

```bash
python3 tools/generate_post_banner.py --preset summit --output assets/postbg/my-journey.png
python3 tools/generate_post_banner.py --preset signal --output assets/postbg/ops-metrics.png --seed 7
python3 tools/generate_post_banner.py --preset engineering --output assets/postbg/systems-design.png --seed 2
```

Full render example with all generation options:

```bash
python3 tools/generate_post_banner.py \
  --preset engineering \
  --output assets/postbg/engineering-wide.png \
  --width 1500 \
  --height 380 \
  --background '#D3D5D8' \
  --ink '#000000' \
  --seed 3
```

`--list-presets` is a standalone helper flag that prints the available presets and exits:

```bash
python3 tools/generate_post_banner.py --list-presets
```

Available presets:

- `launch` for deployment, release, checklist, and operational playbook posts
- `signal` for metrics, performance, analytics, and engineering trend posts
- `engineering` for coding workflow, computer science, systems design, and software engineering posts
- `summit` for challenge, growth, roadmap, and journey-style posts
- `reflection` for personal, reflective, and human-centered posts

Using `--seed`:

- `--seed` accepts any integer such as `0`, `1`, `7`, or `42`
- the same preset, seed, size, and colors will generate the same banner every time
- changing the seed can switch both the overall composition and the smaller pattern details
- seeds `0`, `1`, `2`, and `3` usually give the most obviously different layout families inside the same preset
- larger seeds continue to vary the layout, but may sometimes stay in the same visual family with different positioning and pattern changes
- the default seed is `0`

Example seed variations:

```bash
python3 tools/generate_post_banner.py --preset launch --seed 0 --output assets/postbg/release-v1.png
python3 tools/generate_post_banner.py --preset launch --seed 9 --output assets/postbg/release-v2.png
```

If you are already inside the `tools/` directory, run:

```bash
python3 generate_post_banner.py
```

Use the generated PNG in post front matter like this:

```yaml
image:
  path: /assets/postbg/release-dragon.png
  alt: Release workflow banner
```

Notes:

- `image.path` is the single banner source used in the post layout, homepage cards, and share metadata.
- Keep the banner at `1500x380` when possible so it matches the post header layout cleanly.

## Google Drive Images

Google Drive share pages like `https://drive.google.com/file/d/.../view` should not be embedded directly as image sources. The site now supports Google Drive images in two authoring-friendly ways.

Use a Google Drive banner in post front matter:

```yaml
image:
  drive_id: 1la-188wXrmGrqT5pFevlKSu56kaM9usk
  alt: Knight at dungeon entrance ready for battle
  source: https://drive.google.com/file/d/1la-188wXrmGrqT5pFevlKSu56kaM9usk/view
```

You can also keep using `image.path`, and if it is a Google Drive share link the layout will convert it to a direct image URL automatically.

Use a Google Drive file as an iframe embed inside post content:

```liquid
{% include drive-iframe.html
  source="https://drive.google.com/file/d/1la-188wXrmGrqT5pFevlKSu56kaM9usk/view?usp=drive_link"
  title="Knight at dungeon entrance ready for battle"
  caption="Embedded from Google Drive as an iframe."
  clickthrough=true
%}
```

This converts the Drive share link to the `/preview` URL that Google Drive allows inside an iframe. Add `clickthrough=true` when you want the whole embedded area to open the Drive file in a new tab.

## Repository Structure

- `_posts/` contains published blog posts
- `_tabs/` contains standalone pages such as About, Projects, Tags, and Archives
- `_data/` stores shared site metadata
- `assets/` contains images and other static resources

## License

This repository is available under the [MIT License](LICENSE).
