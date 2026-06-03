# Jarvis — TODO / Backlog

## Alta priorità

- [x] **TTS migliorato** — Kokoro ONNX locale, voce `if_sara` (IT, F) o `im_nicola` (IT, M). Endpoint `/tts` in FastAPI, frontend usa `Audio` element. Nessuna API key.
  Opzioni (in ordine di qualità):
  1. **ElevenLabs** — qualità umana, voices italiane, free tier 10k chars/mese. Aggiungere endpoint `/tts` nel backend FastAPI che chiama l'API ElevenLabs e restituisce audio/mpeg; il frontend fa `<audio>.play()` invece di `speechSynthesis`.
  2. **OpenAI TTS** — molto buono, `tts-1` / `tts-1-hd`, $15/1M chars. Stesso schema del punto 1.
  3. **Kokoro TTS (locale)** — open source, gira sul server, zero costo, qualità discreta. `pip install kokoro-onnx`.
  - In ogni caso: stream audio chunked (non aspettare la risposta intera), aggiungere selezione voce nel settings.

## Media priorità

- [x] **Livello 2 tools** — drive_list, drive_read, sheets_read/write/append, tasks_list/create/complete. ⚠️ Richiede re-auth Google per i nuovi scope (cancellare config/google_token.json e rilanciare).
- [x] **GitHub tool** — github_repos, github_issues, github_prs, github_search. Token opzionale (GITHUB_TOKEN nel .env).
- [x] **System stats tool** — CPU, RAM, disco, top processi, uptime. Zero dipendenze extra.
- [x] **Schedule task tool** — schedule_task/list_scheduled/cancel_scheduled. Il cron trigger controlla ogni minuto e invia il risultato su Telegram.

## Bassa priorità / idee

- [ ] Reddit scraping (PRAW) — esplicitamente deferred dall'utente
- [ ] ScrapeGraphAI integration — hybrid LLM+scraping
- [ ] Spotify control (spotipy)
- [ ] Home Assistant integration
- [ ] Entity-per-file memory con YAML frontmatter (stile Skywork)
