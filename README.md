# Podcast Brasil

A daily mini podcast in Brazilian Portuguese with Ana and Rafa, for B1–B2 learners.

- Feed: https://podcast-creator3939.github.io/portugeus-podcast/feed.xml
- Site: https://podcast-creator3939.github.io/portugeus-podcast/

## How an episode is made

1. Write `episodes/YYYY-MM-DD/script.md`. Dialogue lines must be `**Ana:** ...` or `**Rafa:** ...`.
   Everything after the `## Notas de estudo` heading is study notes and is not read aloud.
2. Write `episodes/YYYY-MM-DD/meta.json`: `{"title": "...", "summary": "..."}`.
3. `pip install piper-tts markdown` then
   `python3 tools/make_audio.py episodes/YYYY-MM-DD/script.md episodes/YYYY-MM-DD/episode.mp3`
4. `python3 tools/build_site.py` (rebuilds pages, `feed.xml`; keeps MP3s for the newest 30 episodes).
5. Commit and push to `main`. GitHub Pages publishes it.

The voice model in `voices/` is Piper's `pt_BR-faber-medium` (MIT licence, from rhasspy/piper-voices).
The site is unlisted: `robots.txt` and `noindex` keep it out of search engines, and it is not submitted to podcast directories.
