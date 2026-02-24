---
layout: default
icon: fa-solid fa-diagram-project
order: 5
---

# Projects
<ul>
  {% for project in site.projects %}
    <li>
      <a href="{{ project.url }}">{{ project.title }}</a> - {{ project.date | date: "%b %-d, %Y" }}
    </li>
  {% endfor %}
</ul>