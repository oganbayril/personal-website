# oganbayril.com

Personal portfolio. Plain HTML and CSS, one small JavaScript file for the theme
switch. No framework, no build step.

**Only `public/` is deployed.** Everything else (this README, `deploy.sh`,
`serve.py`, `templates/`) stays in the repo.

```
public/                     what the site serves (= /srv/oganbayril on the server)
  index.html                /
  projects.html             /projects
  projects/<slug>.html      /projects/<slug>
  cv.html                   /cv          (+ cv.pdf, which you add)
  contact.html              /contact
  404.html                  shown for any unknown path
  assets/css/style.css      all styles; colours are tokens at the top (light + dark)
  assets/js/theme.js        System / Light / Dark switch
  assets/img/projects/      screenshots (create when you add the first one)
  favicon.svg, favicon.ico, apple-touch-icon.png, og-image.png
  robots.txt, sitemap.xml
templates/project.html      starting point for a new project page
deploy.sh                   publish to the VPS (see below)
serve.py                    local preview with clean URLs
```

## URLs

Files are plain `.html`; links always use the clean form: `/cv`, never `/cv.html`.
Caddy serves `/cv` from `cv.html` and permanently redirects `/cv.html` to `/cv`
(vps-infra `templates/static-www.caddy`). Every link is absolute (`/projects`,
`/assets/...`) because pages are served from different depths.

The header, `<head>` and footer are repeated in every page (there is no build step).
When you change one, change it in all of them, including `templates/project.html`.
`grep -rn 'site-nav' public` shows every copy.

## Filling in the content

Every placeholder contains the word `TODO`. It also shows on the page as a yellow
dashed box, so nothing slips through:

```bash
grep -rn TODO public
```

`deploy.sh` refuses to deploy while any `TODO` remains in `public/`.

Still to provide:

- Bio and one-line pitch (`index.html`), CV content (`cv.html`) and `public/cv.pdf`.
- Per project: summary, question, result, tools, screenshot (`projects/*.html`
  and the cards in `projects.html`).
  Screenshots go in `public/assets/img/projects/<slug>.png`, ideally 16:10
  (e.g. 1600x1000). The HTML comment next to each placeholder has the exact `<img>` tag.
- Optional: your own `og-image.png` (1200x630), the image link previews show.
- The project titles are working titles taken from the repo names. Confirm or change them.
- `eu-energy-transition`: the live demo link is the Streamlit URL from that repo's
  README. Check that it is still up.

## Add a project

1. `cp templates/project.html public/projects/<slug>.html` (lowercase, hyphens).
2. Replace `__SLUG__`, `__TITLE__`, `__REPO__`, `__LIVE_URL__` and remove the
   instruction comment at the top.
3. Add a card to `public/projects.html` (copy an existing `<li class="card">`).
4. Add the URL to `public/sitemap.xml`.

## Preview locally

```bash
python serve.py        # http://localhost:8000, same clean URLs as the live site
```

## Deploy

```bash
git push               # the server deploys from GitHub, not from this PC
./deploy.sh            # from Git Bash
```

The server's address and SSH user are not in the repo. Set them once in a local,
git-ignored `deploy.env` (`deploy.sh` stops with a message if it is missing):

```bash
cp deploy.env.example deploy.env   # then fill in DEPLOY_HOST and DEPLOY_USER
```

`deploy.sh` checks that the working tree is clean and that local `main` is pushed.
It then connects to `DEPLOY_USER@DEPLOY_HOST`, updates the deploy-only checkout
(`DEPLOY_CHECKOUT`, default `~/src/personal-website` on the server) to `origin/main`, and runs (on the server)
`rsync -a --delete public/ /srv/oganbayril/`. Last, it checks that the live pages
answer 200. rsync runs on the server because Git Bash has no rsync.

Safety: the rsync target must be exactly `/srv/oganbayril` (anything else, including
an empty value, aborts), and a commit without `public/index.html` is never synced.

```bash
./deploy.sh <commit>     # deploy a specific pushed commit
./deploy.sh --rollback   # back to the commit that was live before the last deploy
```

The server keeps the live commit in `<checkout>.deployed` and the one before it in
`<checkout>.previous`, next to the deploy checkout.

Server side, set up once (see the vps-infra repo): Caddy site
`/etc/caddy/sites-enabled/oganbayril.conf` from `templates/static-www.caddy`.
`www.oganbayril.com` redirects to `oganbayril.com`. DNS is on Cloudflare, DNS only.
