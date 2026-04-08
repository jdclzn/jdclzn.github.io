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

## Repository Structure

- `_posts/` contains published blog posts
- `_tabs/` contains standalone pages such as About, Projects, Tags, and Archives
- `_data/` stores shared site metadata
- `assets/` contains images and other static resources

## License

This repository is available under the [MIT License](LICENSE).
