# Muhammed & Waad — Engagement Invitation

An interactive, single-page invitation built from the original invitation artwork.
Plain HTML, CSS and JavaScript: no framework, no build step, no dependencies.

## The experience

One continuous illustrated story: a vintage Egyptian musical evening in your card's palette.

1. **Opening.** The card's sage arch appears as closed doors. Tapping opens them, and petals drift over everything.
2. **Om Kalthoum (the first scene).** She stands before a sunburst halo at the top of a grand staircase, inside a gold frame with an Arabic-geometric crest.
   - Your names, warm light rays, watercolour branches and swallows circle her.
   - On wide screens, brass lanterns and your card's garlands fill the sides.
   - **Tap to Listen** plays the song. While it plays she sings, the halo turns and breathes with the music, and notes rise from the microphone.
3. **The invitation card.** It reassembles layer by layer when you scroll to it, with the live countdown. Vines grow beside it on wide screens.
4. **The message arch.** A nay player and an oud player sit at its corners, with Egyptian lanterns overhead that glow with the music, and the RSVP button.
5. **When & where.** An ivory botanical arch: a gold chandelier, a large date, the time, **Farha VIP Hall** with its Maps link, calendar buttons and a butterfly.
6. **Closing.** Your original card as a keepsake, swallows flying off, and share and save buttons.

**Small touches:**
- Tap a branch to rustle it and scatter petals.
- Tap a swallow to startle it.
- Tap or hover over a lantern to set it swinging.

**Behaviour:**
- Everything decorative pauses when the tab is hidden.
- Under reduced motion nothing flies or drifts, and all text stays readable.

## Editing the details

Everything you'd change lives in **`js/config.js`**. Fill in the fields marked `TODO`:

| Field | What it does |
|---|---|
| `couple.first / second` | Names (currently taken from the folder name; please confirm the spelling) |
| `event.timeZone` | e.g. `"Africa/Cairo"`. **Set this.** Without it, each guest's countdown uses their own clock. |
| `venue.name`, `venue.address` | Shown on the page and used for the map buttons |
| `venue.mapsUrl` / `venue.coordinates` | Optional, for more precise map links |
| `rsvp.whatsapp` *or* `rsvp.url` | Shows the RSVP button. WhatsApp opens a pre-written message to that number. |
| `music.src` | Set to `assets/music/zaffa-om-kalthoum.mp3`, a URL-safe copy of your file `زفة بمقدمة ام كلثوم ❤.mp3` (27.7 s; loops). |
| `music.startAt` | Seconds into the track where the performance begins, so you can skip a long intro |
| `music.loop` | `true` loops back to `startAt`. `false` lets the scene settle when the song ends. |
| `music.bpm` | Optional tempo, used for the halo's pulse when the page is opened as a file rather than from a website |
| `music.startOnOpen` | `true` also starts the song when the doors open. The default is `false`, as in the reference. |

When a field is empty, the page hides whatever depends on it. Nothing made up is ever shown.

> The date and time inside the card come from the artwork itself. If the date changes,
> update the artwork and re-run the asset script below as well as `event.start`.

### The musical scene and the song

The stage and musicians are inline SVG illustrations in `index.html`, with each moving part on its own layer.
Picture and sound are tied together:
- The scene performs exactly while the song plays. It starts, pauses and stops with the audio, from either **Tap to Listen** or the floating music button.
- On a real website (http or https), the page measures the song's loudness live, and the halo breathes with it.
- Opened as a local file, the halo pulses at `music.bpm` instead. Browsers can silence local audio that is analysed this way.
- To watch the performance before you have the song, open the page with `?preview-scene` (for example `http://localhost:8000/?preview-scene`). The preview is silent.
- With reduced motion turned on, the scene stays still and only the music plays.

### Personal links

Add `?to=Name` to the link to greet a guest by name, for example:
`https://your-site.example/?to=Sara`.
The **Share** button always shares the plain link, so a personal greeting is never forwarded.

## Running it locally

Double-clicking `index.html` works. For a closer match to the live site, serve the folder:

```bash
python -m http.server 8000      # then open http://localhost:8000
```

## Publishing

It's a static site, so any static host works:

- **Netlify Drop**: drag this folder onto https://app.netlify.com/drop
- **GitHub Pages**: push the folder to a repository, then Settings → Pages → deploy from branch
- **Vercel / Cloudflare Pages**: import the folder with no build command and output directory `/`

After deploying:

1. In `index.html`, change `og:image` to the full URL, e.g. `https://your-site.example/assets/og-image.jpg`.
   WhatsApp needs an absolute URL to show the preview image.
2. Optionally uncomment the `canonical` link and set your domain.

`assets/source/invitation-original.png` (17 MB) is only an input for the asset script.
The page never loads it, so you can leave it out of the upload.

## Regenerating the artwork layers

`tools/build_assets.py` derives every image in `assets/card/`, plus the background pattern, favicon and social image, from `assets/source/invitation-original.png`.
It never modifies the original.

```bash
pip install opencv-python-headless numpy
python tools/build_assets.py
```

## Files

```
index.html            page structure
css/styles.css        design tokens (colours sampled from the card), layout, motion
js/config.js          ← your event details
js/main.js            opening, countdown, reveals, maps, calendar, RSVP, music, share
js/world.js           petals & gold dust, swallows, butterfly, vines, parallax, tap interactions
assets/art/           original watercolour and gold artwork (branch, lantern, chandelier, frame, divider, paper)
assets/music/         the song
assets/card/          layers cut from the artwork (plate, lettering, monogram, garlands)
tools/build_assets.py asset pipeline
```
