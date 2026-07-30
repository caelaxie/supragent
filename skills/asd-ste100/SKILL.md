---
name: asd-ste100
description: Apply ASD-STE100 Simplified Technical English principles to prose — documentation, explanations, commit messages, PR descriptions, design docs, and code comments. Use when writing or reviewing user-facing text, commit/PR text, README content, or comments, so that non-native English readers and translation tooling can parse it reliably. Adapted for software engineering; never apply to source code identifiers, API names, external specs, or required technical terms.
---

# ASD-STE100 Writing Style

This skill adapts ASD-STE100 Simplified Technical English for software engineering prose. The original standard targets aerospace maintenance documentation; this skill keeps its ambiguity-reduction rules and drops its domain-specific parts (the controlled dictionary, warning/caution/note hierarchy, and technical-noun categories). In software, identifiers and API names take the role of approved technical terms.

## When to Apply

Apply this style to:
- documentation and explanations
- commit messages and PR descriptions
- design documents
- code comments

Never apply this style to:
- source code identifiers
- API names
- external specifications
- required technical terminology

Renaming identifiers or softening terms in a quoted spec creates mismatches between text and code. Clarity rules apply to prose only.

## Words

1. Use simple words. Common words survive translation tools and non-native readers; rare words do not.
2. Use one word for one meaning. If "run" means execute, never use it for operate or manage — readers cannot tell which sense is active.
3. Use one word per concept. Do not alternate between "remove", "delete", and "drop" for the same action; pick one and keep it.
4. Use verbs for actions, not nouns. "Install the package", not "Perform the installation of the package". Noun forms hide the action and add filler words.
5. Avoid "-ing" forms except as technical nouns or modifiers. "Save the file before you close it", not "Saving the file before closing is recommended". Gerunds blur the line between action, actor, and state.
6. Never omit articles ("a", "an", "the") or demonstratives ("this", "these") to shorten a sentence. Terse tech writing drops them; non-native readers need them to parse noun boundaries.
7. Avoid vague words. Words like "various", "appropriate", and "several" commit to nothing; the reader must guess the count or the criteria.

## Sentences

8. Write short sentences. Maximum 20 words for instructions, 25 for descriptions. Long sentences hide the verb and the condition.
9. Do not use contractions or omit words to fit the limit. Split the sentence instead.
10. Use active voice in instructions. "The script deletes the cache", not "The cache is deleted by the script". Active voice names who does the action.
11. In descriptions, use the passive voice only when the agent is unknown or irrelevant. "The record is locked during a migration" is acceptable; never use the passive to hide who made a decision.

## Instructions

12. Use direct instructions. "Run the test", not "You should run the test" or "It is recommended to run the test".
13. Write one instruction per sentence, unless the actions must occur at the same time. Sequenced steps in one sentence force the reader to re-parse to find the order.
14. Warn before a destructive step. State the risk first, then the instruction, then the consequence. "This command deletes all local data. Run `git clean -fdx` only after you commit your work. Uncommitted changes are not recoverable." A warning after the instruction arrives too late.

## Paragraphs

15. Keep one topic in each paragraph. Mixed topics force the reader to re-read to find which sentence belongs to which subject.
16. Keep paragraphs to six sentences or fewer. Move additional detail to a new paragraph or a list.

## Noun Clusters

17. Never join more than three nouns into a cluster. "User session token refresh logic" forces the reader to guess the grouping. Rewrite with prepositions: "the logic that refreshes user session tokens". Hyphenate two-noun compounds only when the grouping is unambiguous.

## Word Choice

Use:
- "use", "run", "create", "change", "remove", "check", "show", "start", "stop"

Avoid:
- "utilize" → use "use"
- "leverage" → use "use"
- "facilitate" → use "help" or "make possible"
- "optimize" → only when it means a measured performance improvement; otherwise use "improve"
- "ensure" → only when a guarantee or check exists; otherwise use "make sure" or rewrite
- "various", "several", "multiple" → give the number or the list
- "appropriate" → give the criteria for the choice
- "seamless" → state what actually happens

## Code Comments

Explain why, not what. The code already shows what it does; a comment that restates it adds no information and rots when the code changes.

Good:
```
// Cache this value because the API rate limit is low.
```

Bad:
```
// Store value in cache.
```

Good:
```
Retry the request after a timeout.
```

Bad:
```
This mechanism provides retry capabilities in timeout scenarios.
```

## Review Checklist

Read the final text and answer each question. Fix every "no".

- Is each sentence 20 words or fewer (25 for descriptions)?
- Is each sentence clear to a non-native English reader?
- Does each word have only one meaning in this text?
- Does each concept use the same word everywhere?
- Did I keep every article ("a", "an", "the")?
- Does every action use a verb, not a noun form?
- Did I remove every gerund that is not a technical noun?
- Does every noun cluster have three nouns or fewer?
- Did I remove every vague word ("various", "appropriate", "seamless")?
- Is every instruction imperative, active, and one action per sentence?
- Does every destructive step warn before the command?
- Does each paragraph have one topic and six sentences or fewer?
