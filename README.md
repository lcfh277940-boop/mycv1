# HADEEL — Personal Digital Identity

Static personal portfolio built with HTML5, CSS3, and vanilla JavaScript.

## Project structure

```text
MYCV1/
├── index.html
├── style.css
├── script.js
├── favicon.png
├── favicon.webp
├── README.md
├── README.txt
└── images/
    ├── profile.jpg
    ├── profile.webp
    ├── backgrounds/
    │   ├── about-texture.jpg
    │   ├── about-texture.webp
    │   ├── hero-tech.jpg
    │   ├── hero-tech.webp
    │   ├── pattern-grid.png
    │   ├── vision-future.jpg
    │   └── vision-future.webp
    └── projects/
        ├── project-ai-research.jpg
        ├── project-ai-research.webp
        ├── project-building-materials.jpg
        ├── project-building-materials.webp
        ├── project-hotel-database.jpg
        ├── project-hotel-database.webp
        ├── project-java-oop.jpg
        ├── project-java-oop.webp
        ├── project-luxury-hospitality.jpg
        └── project-luxury-hospitality.webp
```

## Run locally

Start a local server in the project folder:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000
```

## Notes

- All asset paths are relative for GitHub Pages compatibility.
- Images are stored under `images/`.
- Site images now use `.webp` where available.
- The site supports Arabic (RTL) and English (LTR), light/dark themes, and responsive layouts.
```