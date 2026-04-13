# Daily Brief Skill

**Triggers:** morning brief, daily brief, what's happening today
**Tools:** memory_search, perplexity_search (if key set)
**Output:** Discord message with date, top priorities, any flagged items

## What This Does

When the user asks for a morning or daily brief, the agent:
1. Reads `workspace/memory/tasks.md` for open items (`- [ ]` lines)
2. Checks the last 24 h of `workspace/memory/heartbeat.log` for flagged alerts
3. Optionally queries Perplexity for any news items listed in tasks (requires `PERPLEXITY_API_KEY`)
4. Returns a formatted brief as a Discord message

## Prompt Template

```
You are generating a daily briefing for [USER].

Today's date: {date}

Review the following context and produce a concise morning brief:

Open tasks:
{open_tasks}

Recent heartbeat flags:
{flagged_items}

Format the response as:

**{date} Morning Brief**
- Priority 1: ...
- Priority 2: ...
- Priority 3: ...
- Flagged: ... (only if flagged_items is non-empty)
- Open tasks: ... (only if open_tasks is non-empty)

Keep it scannable. No more than 10 bullet points total.
```

## Adding This Skill

To enable this skill, include the following in your `workspace/AGENTS.md`:

```markdown
## Daily Brief
When the user asks for a "morning brief", "daily brief", or "what's happening today",
run the daily brief skill:
1. Call memory_search("tasks") to find open items
2. Read workspace/memory/heartbeat.log for FLAGGED lines
3. Use the Daily Brief prompt template
4. Return formatted output
```

## Customization

- Add your own recurring priorities to `workspace/memory/tasks.md`
- Modify the prompt template to include business-specific context
- Set `PERPLEXITY_API_KEY` in `.env` to enable web search integration
