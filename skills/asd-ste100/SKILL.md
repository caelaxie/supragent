---
name: asd-ste100
description: Apply ASD-STE100 Simplified Technical English principles to all prose the agent writes for humans — chat replies, status updates, documentation, explanations, commit messages, PR descriptions, design docs, and code comments. Use whenever writing or reviewing text a person will read, so that non-native English readers and translation tooling can parse it reliably. Adapted for software engineering; never apply to source code, identifiers, API names, external specs, or required technical terms.
---

# ASD-STE100 Writing Style

This skill adapts ASD-STE100 Simplified Technical English for software engineering. It keeps the ambiguity-reduction rules and drops the aerospace-specific parts (controlled dictionary, warning hierarchies, noun categories). Source code identifiers and API names take the role of approved technical terms: they are always correct as written.

## Scope

Apply this style to all prose a person will read:
- chat replies and status updates to the user
- documentation and explanations
- commit messages and PR descriptions
- design documents
- code comments

Never apply this style to:
- source code, commands, file paths, identifiers
- API names
- quoted external specifications
- required technical terminology

Renaming an identifier or softening a term in a quoted spec creates a mismatch between text and code. Clarity rules apply to prose only.

## Words

1. Use simple words. Common words survive translation tools and non-native readers; rare words do not.
2. Use one word for one meaning. If "run" means execute, never use it for operate or manage — readers cannot tell which sense is active.
3. Use one word per concept. Do not alternate between "remove", "delete", and "drop" for the same action; pick one and keep it.
4. Use verbs for actions, not nouns. "Install the package", not "Perform the installation of the package". Noun forms hide the action and add filler words.
5. Avoid "-ing" forms except as technical nouns or modifiers. "Save the file before you close it", not "Saving the file before closing is recommended". Gerunds blur the line between action, actor, and state.
6. Never omit articles ("a", "an", "the") or demonstratives ("this", "these"). Non-native readers need them to parse noun boundaries.
7. Never use vague words. "Various", "appropriate", "several", and "multiple" commit to nothing. Give the number, the list, or the criteria.
8. Never join more than three nouns into a cluster. "User session token refresh logic" forces the reader to guess the grouping. Rewrite with prepositions: "the logic that refreshes user session tokens". Hyphenate two-noun compounds only when the grouping is unambiguous.
9. Use a pronoun only when its antecedent is unmistakable. If "it" or "this" can point to two nouns, repeat the noun. A wrong antecedent reads as confident, not as ambiguous.

Approved verbs: "use", "run", "create", "change", "remove", "check", "show", "start", "stop".

Replacements:
- "utilize" → "use"
- "leverage" → "use"
- "facilitate" → "help" or "make possible"
- "optimize" → only for a measured performance improvement; otherwise "improve"
- "ensure" → only when a guarantee or a check exists; otherwise "make sure" or rewrite
- "seamless" → state what actually happens

## Sentences

10. Write short sentences. Maximum 20 words for instructions, 25 for descriptions. Long sentences hide the verb and the condition.
11. Do not use contractions or omit words to fit the limit. Split the sentence instead.
12. Use simple tenses. Simple present for procedures and descriptions, simple past for completed events, simple future only for real future results. Never use "will" to make an instruction formal: "Remove the panel", not "The operator will remove the panel". Complex tenses hide the sequence of actions.
13. Use active voice in instructions. "The script deletes the cache", not "The cache is deleted by the script". Active voice names who does the action.
14. In descriptions, use the passive voice only when the agent is unknown or irrelevant. "The record is locked during a migration" is acceptable; never use the passive to hide who made a decision.

## Instructions

15. Use direct instructions. "Run the test", not "You should run the test" or "It is recommended to run the test".
16. Use "must" for mandatory conditions and "should" only for real recommendations. "Should" reads as advice; a mandatory step written with "should" will be skipped.
17. Write one instruction per sentence, unless the actions must occur at the same time. Sequenced steps in one sentence force the reader to re-parse to find the order.
18. Warn before a destructive step. State the risk first, then the instruction, then the consequence. "This command deletes all local data. Run `git clean -fdx` only after you commit your work. Uncommitted changes are not recoverable." A warning after the instruction arrives too late.

## Paragraphs

19. Keep one topic in each paragraph. Mixed topics force the reader to re-read to find which sentence belongs to which subject.
20. Keep paragraphs to six sentences or fewer. Move additional detail to a new paragraph or a list.

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

All word and sentence rules apply to comments. "Retry the request after a timeout", not "This mechanism provides retry capabilities in timeout scenarios".

## Review Checklist

Read the final text and answer each question. Fix every "no".

- Is each sentence 20 words or fewer (25 for descriptions)?
- Is each sentence clear to a non-native English reader?
- Does each word have only one meaning in this text?
- Does each concept use the same word everywhere?
- Did I keep every article ("a", "an", "the")?
- Does every pronoun have one unmistakable antecedent?
- Does every action use a verb, not a noun form?
- Did I remove every gerund that is not a technical noun?
- Did I use simple tenses, without "will" in instructions?
- Does every mandatory condition use "must"?
- Does every noun cluster have three nouns or fewer?
- Did I replace every vague word with a number, a list, or criteria?
- Is every instruction imperative, active, and one action per sentence?
- Does every destructive step warn before the command?
- Does each paragraph have one topic and six sentences or fewer?
