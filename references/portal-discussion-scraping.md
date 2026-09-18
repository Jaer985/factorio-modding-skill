# Factorio Mod Portal: Discussion Scraping Reference

## URL patterns

| Resource | URL |
|----------|-----|
| Discussion list | `https://mods.factorio.com/mod/<mod-name>/discussion` |
| Single thread | `https://mods.factorio.com/mod/<mod-name>/discussion/<hex-id>` |
| Filtered (Bugs) | `https://mods.factorio.com/mod/<mod-name>/discussion/b` |
| Filtered (Ideas) | `https://mods.factorio.com/mod/<mod-name>/discussion/i` |
| Filtered (General) | `https://mods.factorio.com/mod/<mod-name>/discussion/g` |

The `User-Agent` header is typically NOT required for discussion pages, but add `-H "User-Agent: Mozilla/5.0"` if you get an empty response or login page.

## Known issues / pitfalls

- **Shortened IDs return 404**: Thread IDs are 20+ character hex strings (e.g. `6a3ed25ffe5026eb137972d3`). Using only the first 8 chars (e.g. `6a3ed25f`) returns a 404 page. Always use the full ID.
- **Meta-tag quick-scan may return empty**: The `<meta property="og:description">` tags relied on by the quick-scan approach (Step 2) are rendered by React and may be absent or empty when served to curl, even with a User-Agent header. When the quick-scan produces no output, fall back to Python text extraction (Method B in Step 3).
- **React rendering changes**: The Mod Portal's React-rendered HTML structure changes periodically. Grep-based extraction patterns (discussion-message-body, discussion-message-author classes) may stop working between Factorio releases. The Python text extraction approach is the most resilient to structural changes.

## Step 1: Extract thread IDs from the list page

```bash
# Hex IDs only (cleanest)
curl -sL 'https://mods.factorio.com/mod/<mod-name>/discussion' | \
  grep -oP '/discussion/[a-f0-9]{20,}' | sort -u | sed 's|/discussion/||'

# Full URL paths (includes mod name prefix)
curl -sL 'https://mods.factorio.com/mod/<mod-name>/discussion' | \
  grep -oP '/mod/[^/]+/discussion/[a-zA-Z0-9-]+' | sort -u
```

## Step 2: Map thread IDs to titles (skip this if you only need the IDs)

When you need to know which ID corresponds to which thread without fetching every page, search for a keyword from the thread title near the href pattern in the discussion list HTML:

```bash
curl -sL -H "User-Agent: Mozilla/5.0" 'https://mods.factorio.com/mod/<mod-name>/discussion' | \
  python3 -c "
import sys, re
html = sys.stdin.read()
# Search for a keyword near href discussion IDs
keyword = 'moon-eneas'  # change to the keyword you're looking for
idx = html.lower().find(keyword)
if idx > 0:
    chunk = html[idx-500:idx+500]
    ids = re.findall(r'/discussion/([a-f0-9]{20,})', chunk)
    print('IDs near keyword:', ids)
"
```

## Step 3: Quick-scan first posts via meta tags (fastest)

Each thread page embeds the FIRST post's content in `<meta property="og:description">` and
the thread title in `<meta property="og:title">`. This avoids parsing the React-rendered body.

One-shot scan of ALL threads:
```bash
for id in $(curl -sL 'https://mods.factorio.com/mod/<mod-name>/discussion' | \
  grep -oP '/discussion/[a-f0-9]{20,}' | sort -u | sed 's|/discussion||'); do
  echo "=== $id ==="
  curl -sL "https://mods.factorio.com/mod/<mod-name>/discussion/$id" | \
    grep -oP '(?<=<meta property="og:(title|description)" content=")[^"]+'
  echo
done
```

Sample output:
```
=== 6a54a3f2fa53b9e6f02cb73a ===
just here to say thanks! - Dark Matter Replicators Reborn
so i downloaded the newest version, and finally i can play dark matter replicators with angel+bobs+space age!!!
thank you for the amazing job!!
```

## Step 4: Full parse of individual threads (all replies)

**The grep/div approaches are unreliable** -- React-rendered threads with multiple replies often return empty or partial content. Use these methods in order of reliability:

**Method A: Meta tag quick-scan** (Step 2 above) -- best for first-pass triage. Gives you the thread description and title without rendering the full page.

**Method B: Python text extraction** (most reliable for full content including reply chains and timestamps):

```bash
curl -sL -H "User-Agent: Mozilla/5.0" \
  "https://mods.factorio.com/mod/<mod-name>/discussion/$id" | \
  python3 -c "
import sys, re
html = sys.stdin.read()
text = re.sub(r'<[^>]+>', ' ', html)
text = re.sub(r'\s+', ' ', text).strip()
idx = text.lower().find('discussion')
if idx > 0:
    start = max(0, idx)
    print(text[start:start+2500])
"
```

Sample output (real extraction from DMR "The Blue Bottle in T5?" thread):
```text
Discussion 11 Metrics g The Blue Bottle in T5? sp518 10 days ago
With bob's, Blue bottles will appear in T5... too expensive, is it right?
Jaer985 8 days ago Nope, I'll change it, should be earlier, as soon as you can make them.
But since it's dynamically generated based on mods you have, probably caused this.
```

This reveals author names ("sp518", "Jaer985"), relative timestamps ("10 days ago", "8 days ago"), and the full reply chain. The og:description meta tag only shows the first post; Python extraction gets the entire conversation including follow-ups.

**Method C: grep patterns** (try when Python is unavailable):
```bash
curl -sL "https://mods.factorio.com/mod/<mod-name>/discussion/$id" | \
  grep -oP '<div class="discussion-message-body[^"]*"[^>]*>.*?(?=</div>)' | \
  sed 's/<[^>]*>//g' | sed '/^$/d'
```

**Author names** (each message block):
```bash
curl -sL "https://mods.factorio.com/mod/<mod-name>/discussion/$id" | \
  grep -oP '(?<=class="discussion-message-author">)[^<]+'
```

**Author + timestamp pairs** (structured):
```bash
curl -sL "https://mods.factorio.com/mod/<mod-name>/discussion/$id" | \
  grep -oP '(?<=class="discussion-message-author">)[^<]+|(?<=title=")[0-9]{4}-[0-9]{2}-[0-9]{2}T[^"]+' | \
  paste - - | grep -v '^[[:space:]]*$'
```

**Mod author indicator** (star icon marks thread starter as mod author):
```bash
curl -sL "https://mods.factorio.com/mod/<mod-name>/discussion/$id" | \
  grep -oP 'discussion-message-header-owner|fa fa-star'
```

## Step 5: Thread metadata from the list page

Thread titles, tags (Bugs/Ideas/General), and timestamps in one pass:
```bash
curl -sL "https://mods.factorio.com/mod/<mod-name>/discussion" | \
  grep -oP '(?<=title=\")[0-9]{4}-[0-9]{2}-[0-9]{2}T[^\"]*|[a-z][a-z -]+(?=\")' | \
  grep -vE '^(Last|Available|Downloads|You)' | paste - - -
```

Reply counts per thread (from the `fa fa-comments` icon span):
```bash
curl -sL "https://mods.factorio.com/mod/<mod-name>/discussion" | \
  grep -oP '<i class="fa fa-comments"></i>\s*\K\d+'
```

## Step 6: Full discussion list text extraction (one-shot snapshot)

For a complete overview of every thread's title, author, timestamp, reply count, and last-message info in a single pass, extract the discussion list page text via Python:

```bash
curl -sL -H "User-Agent: Mozilla/5.0" 'https://mods.factorio.com/mod/<mod-name>/discussion' | \
  python3 -c "
import sys, re
html = sys.stdin.read()
text = re.sub(r'<[^>]+>', ' ', html)
text = re.sub(r'\s+', ' ', text).strip()
idx = text.lower().find('discussion')
if idx > 0:
    print(text[idx:idx+3000])
"
```

Output is a plain-text listing of all threads with author names, relative timestamps, reply counts, and last-message authors — all in one go. This is the best first-pass triage tool: scan for keywords (bug, error, crash) and timestamps (hours ago, days ago) to identify new or active threads.

## Step 7: Bulk pipeline: list → scan → filter → full-read

```bash
#!/bin/bash
MOD="dark-matter-replicators-reborn"
URL="https://mods.factorio.com/mod/$MOD/discussion"

# 1. Get all thread IDs
IDS=$(curl -sL "$URL" | grep -oP '/discussion/[a-f0-9]{20,}' | sort -u | sed 's|/discussion||')

# 2. Quick-scan via meta tags, filter for bug keywords
for id in $IDS; do
  html=$(curl -sL "$URL/$id")
  desc=$(echo "$html" | grep -oP '(?<=<meta property="og:description" content=")[^"]+')
  echo "=== $id ==="
  echo "desc" | grep -qiE '(bug|error|crash|issue|fail|incompatible|problem|not work)' && echo "$desc"
done

# 3. For flagged threads, fetch full body
for id in $FLAGGED_IDS; do
  echo "=== Full thread $id ==="
  curl -sL "$URL/$id" | \
    grep -oP '<div class="discussion-message-body[^"]*"[^>]*>.*?(?=</div>)' | \
    sed 's/<[^>]*>//g' | sed '/^$/d'
done
```

## Verbatim session transcript (worked example)

The following is a real scrape of DMR discussions from 2026-07-15:

```
=== 6a54a3f2fa53b9e6f02cb73a ===
just here to say thanks! - Dark Matter Replicators Reborn
so i downloaded the newest version, and finally i can play dark matter replicators with angel+bobs+space age!!!
thank you for the amazing job!!

=== 6a561cb9accd254ecaa026ba ===
The Blue Bottle in T5? - Dark Matter Replicators Reborn
With bob's, Blue bottles will appear in T5... too expensive, is it right?

=== 6a4bc19920bc2715492734f2 ===
Cant work with space-age - Dark Matter Replicators Reborn
(description unavailable - likely empty or error)
```

After identifying threads of interest, full body extraction yields:
```
so i downloaded the newest version, and finally i can play dark matter replicators with angel+bobs+space age!!!
thank you for the amazing job!!
```
(and for the second thread:)
```
With bob's, Blue bottles will appear in T5... too expensive, is it right?
```
