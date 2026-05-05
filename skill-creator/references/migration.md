# Migration

Patterns for converting a skill from one topology to another. Most skills do not start in their final shape: they begin as standalones, grow into members, and sometimes promote to hubs. This file specifies the migration paths and gives concrete procedures for each.

## Reading Order

| Task | Read |
|------|------|
| Standalone skill that two skill-sets want to compose | [Standalone to Member](#standalone-to-member) |
| Member skill that has accumulated 4+ sub-domains | [Member to Hub](#member-to-hub) |
| Bloated single SKILL.md (>500 lines, multiple themes) | [Flat Skill to Hub](#flat-skill-to-hub) |
| Premature hub with only 1-2 children | [Hub to Member or Standalone](#hub-to-member-or-standalone) |
| Hub flavor change (reference-hub ↔ skill-set hub) | [Reference-Hub to Skill-Set Hub](#reference-hub-to-skill-set-hub-and-back) |
| Splitting a member into multiple members | [Member to Multiple Members](#member-to-multiple-members) |
| Validation after migration | [Post-Migration Validation](#post-migration-validation) |
| Pitfalls | [Gotchas](#gotchas) |

## General Migration Principles

Before any migration:

1. **Take inventory.** List everything in the skill: SKILL.md sections, references, scripts, assets, and the skill-sets that include it.
2. **Identify the breaking changes.** What paths will move? What names will change? What downstream consumers depend on stable structure?
3. **Plan the rename map.** Old path → new path for every file. This becomes the validation checklist.
4. **Migrate in a single commit.** Partial migrations leave the skill in an inconsistent state where some references work and others do not.
5. **Test the new shape.** Trigger the skill with sample prompts. Verify the description still matches the new topology.

## Standalone to Member

**When:** A second use case appears for an existing standalone skill, indicating it would benefit from composition into multiple skill-sets.

**Effort:** Small. Mostly metadata and an explicit scope contract.

**Procedure:**

1. **Add an Out-of-Scope section** to SKILL.md. Standalone skills often skip this; members require it as their scope contract. Name 3-5 adjacent capabilities the consuming hub should layer alongside.
2. **Tighten the description** to make scope boundaries explicit. Add a "Use this skill for X. NOT for Y (load Z instead)" clause.
3. **Verify file paths are stable.** No internal paths change. The skill stays at `all-skills/<name>/`.
4. **Create the symlink in the consuming skill-set.** From `skill-sets/<set-name>/`, run:
   ```bash
   ln -s ../../all-skills/<name> <name>
   ```
5. **Update the consuming skill-set's hub SKILL.md** to add the new member to its triage table or common combinations.

**Effects:**
- Skill now lives once in `all-skills/`, available to multiple skill-sets via symlink.
- Hub authors can compose this skill confidently because the scope contract is explicit.

## Member to Hub

**When:** A member skill has accumulated 4+ distinct sub-domains, each of which would benefit from independent loading. Body is approaching 500 lines or already past it.

**Effort:** Medium. Decompose, restructure, redirect.

**Procedure:**

1. **Inventory the sub-domains.** Identify the 4+ distinct sub-domains within the current skill. Each becomes a child or a topic directory.
2. **Choose hub flavor:**
   - If sub-domains are independently useful in other skill-sets → skill-set hub (skill-sets/<name>/, symlinked children)
   - If sub-domains are tightly coupled to one platform → reference-hub (all-skills/<name>/, references/<topic>/ subdirectories)
   - See [topology-decision.md](./topology-decision.md) for details.
3. **For skill-set hub:**
   - Create `skill-sets/<hub-name>/`.
   - For each sub-domain, create a new member skill at `all-skills/<sub-name>/` and move the relevant content.
   - Symlink each new member into `skill-sets/<hub-name>/<sub-name>` from `../../all-skills/<sub-name>`.
   - Write `skill-sets/<hub-name>/SKILL.md` with triage table, common combinations, cross-cutting rules, out-of-scope. See [routing-mechanics.md](./routing-mechanics.md).
4. **For reference-hub:**
   - Restructure `all-skills/<name>/references/` into subdirectories by topic.
   - Within each topic, apply the appropriate taxonomy template. See [taxonomy-templates.md](./taxonomy-templates.md).
   - Rewrite SKILL.md as a routing surface with decision trees and product index.
5. **Hoist cross-cutting rules.** Rules that applied to all sub-domains move from the original body to the hub body. Children no longer restate them.
6. **Update consuming skill-sets.** Any skill-set that previously included the original member now includes the new hub or specific children, depending on intent.
7. **Validate.** Trigger the hub with sample prompts. Verify routing reaches the right child or topic.

**Effects:**
- The original skill name now points to a hub.
- Sub-domains are loadable independently.
- Body shrinks to a routing surface.
- Children can be reused outside the original context (skill-set hub case).

**Migration variants:**
- If only some sub-domains are reused elsewhere, hybrid: most as members under skill-set hub, the tightly-coupled ones as references/topic/ within a reference-hub. Cloudflare uses this hybrid.

## Flat Skill to Hub

**When:** A single SKILL.md has grown past 500 lines covering multiple themes that were never separated.

**Effort:** Medium-Large. Same as member-to-hub but starts from a less organized state.

**Procedure:**

1. **Identify the implicit sub-domains.** Read the bloated SKILL.md and group sections by theme. The themes are the latent children.
2. **Confirm the sub-domains pass the topology criteria.** If only 2-3 themes emerge, this is not a hub-shaped problem; it is a member that needs better progressive disclosure (move themes to references/, not into children). See [design-principles.md](./design-principles.md).
3. **If 4+ themes confirmed:** apply the [Member to Hub](#member-to-hub) procedure.
4. **If 2-3 themes:** stay as member but extract themes to references/. Update the body to load references conditionally per task type.

**Distinguishing flat-to-hub from flat-to-better-references:**

| Signal | Outcome |
|---|---|
| Themes are independently useful in other contexts | Hub (skill-set or reference) |
| Themes are tightly coupled to this skill's domain | Better references in the same skill |
| Body has 2-3 distinct sections, each <100 lines | Better references |
| Body has 4+ distinct sections, each capable of standing alone | Hub |

## Hub to Member or Standalone

**When:** A hub was created prematurely and has only 1-2 children that are never used independently. The hub adds indirection without saving any cost.

**Effort:** Small-Medium. Inverse of member-to-hub.

**Procedure:**

1. **Confirm the children are never used independently.** Search consuming skill-sets. If any skill-set includes a child without the hub, the hub is justified; do not collapse.
2. **Decide target topology:**
   - If the merged content fits in <200 lines → standalone or member, depending on whether composition into other skill-sets is anticipated
   - If the merged content fits in 200-400 lines → member with good references
3. **Merge children back.** Move child content into the (new) single SKILL.md and references/.
4. **Delete the obsolete children and the hub directory.**
5. **Update consuming skill-sets** to point to the new single skill instead of the hub.
6. **Validate.** Trigger the new single skill with sample prompts.

**Effects:**
- Indirection removed.
- One skill instead of multiple.
- Loses optionality (cannot recombine without re-migrating).

## Reference-Hub to Skill-Set Hub (and back)

**When:** A reference-hub has topics that other skill-sets want to compose independently. Or a skill-set hub has children that are too tightly coupled and would simplify as topic directories.

**Effort:** Medium. Path-heavy migration.

### Reference-Hub → Skill-Set Hub

1. **Identify which topics need independent lives.** Search consuming skill-sets for any that want to load only specific topics.
2. **For each independent topic:** create a new member skill at `all-skills/<topic-name>/`. Move the topic's reference content into the new member's SKILL.md and references/.
3. **Create the skill-set hub** at `skill-sets/<hub-name>/`.
4. **Symlink the new members** into the skill-set.
5. **Decide the fate of remaining topics:** topics that did not need independent lives may stay in the original reference-hub (now possibly slimmer), or join the skill-set hub as additional members.
6. **Update consuming skill-sets** to use the new structure.

### Skill-Set Hub → Reference-Hub

1. **Confirm none of the children need independent lives elsewhere.** If any skill-set composes a child without this hub, this migration is wrong.
2. **Create the reference-hub at `all-skills/<hub-name>/`** if it does not exist.
3. **For each former child:** move its content into `all-skills/<hub-name>/references/<topic>/` using the appropriate taxonomy template.
4. **Delete the former child skills from `all-skills/`.**
5. **Replace the skill-set hub** with the reference-hub, or delete it if redundant.

**Effects:**
- Reference-hub: simpler structure, fewer files to manage, but topics are not independently composable.
- Skill-set hub: more flexibility for composition, but more files to keep in sync via symlinks.

## Member to Multiple Members

**When:** A single member has grown to cover 2-3 distinct capabilities that should each be their own member, but not enough to warrant a hub.

**Effort:** Small-Medium.

**Procedure:**

1. **Identify the split lines.** What are the 2-3 capabilities? Each becomes a member.
2. **Create new member directories** at `all-skills/<new-name>/` for each.
3. **Move content** from the original member into the new members.
4. **Decide the fate of the original:** delete (if all content moved) or keep as a thin coordination skill if some shared content remains.
5. **Update consuming skill-sets** to symlink the new members instead of (or alongside) the original.

**Effects:**
- More granular composition.
- More files to maintain.
- Useful when one member was clearly two skills wearing one name.

## Post-Migration Validation

After any migration, run this checklist:

1. **Trigger reliability:** Run 5-10 sample prompts that should trigger the (possibly new) skill name and description. Confirm the harness loads the right artifact.
2. **No broken links:** grep for the old paths in remaining skill-sets and references. Update or remove stale references.
3. **No orphan files:** confirm all moved files reached their new home. The old paths should either be empty or deleted.
4. **No symlink cycles:** verify symlinks resolve to actual directories under all-skills/.
5. **Body length:** if the migration was supposed to shrink the body (member → hub), confirm the new hub body is <250 lines.
6. **Cross-cutting rules:** rules that should be at the hub are at the hub, not duplicated in children.
7. **Out-of-scope sections:** every member and the hub have explicit out-of-scope sections.
8. **Consuming skill-sets work:** load each consuming skill-set in the harness and confirm trigger and content delivery still work.

## Gotchas

### Migrating without an explicit rename map

**Symptom:** Halfway through, a path is unclear and the migration creates duplicate or missing files.

**Cause:** The migration was not planned as a complete rename map first.

**Solution:** Before moving any file, write the full old-path → new-path table. The table is the source of truth during execution.

### Forgetting consuming skill-sets

**Symptom:** Skill-sets that previously included the migrated skill silently break (broken symlinks, missing children).

**Cause:** Migration only touched the skill itself, not its consumers.

**Solution:** As part of inventory, list every skill-set that includes the skill. Update each one in the same commit.

### Hoisting too aggressively

**Symptom:** Member-to-hub migration moves rules to the hub that actually only applied to one child. Children re-implement them inconsistently.

**Cause:** "Looks shared" is not the same as "is shared."

**Solution:** Verify the rule applies to ALL children before hoisting. If it applies to most-but-not-all, leave it in each child where it applies.

### Splitting at theme boundaries that do not match user task boundaries

**Symptom:** Children are organized by what the author found logical, not by what the user actually does. Triage misses frequently.

**Cause:** Migration was author-centric, not user-centric.

**Solution:** Re-do the inventory by user task. What does a user with task X load? What does a user with task Y load? Children should align with task boundaries, not topic boundaries.

### Migrating before the criteria are met

**Symptom:** A member with 250-line body and 2 themes gets promoted to hub. The new hub has 2 thin children that always load together. No win.

**Cause:** Migration triggered by perceived complexity rather than concrete criteria.

**Solution:** Apply the topology criteria from [topology-decision.md](./topology-decision.md) literally. 4+ distinct sub-domains, each independently useful, each warranting its own description.

### Leaving stale references during migration

**Symptom:** Old references/ files remain after migration, unlinked from anything but still searchable. Future grep finds the wrong content.

**Cause:** "Move" was implemented as "copy" without deleting the source.

**Solution:** Use git mv when possible (or move-then-delete). After migration, search for unreferenced files in references/ and remove them.

### Symlinks pointing to non-existent paths

**Symptom:** A skill-set hub has symlinks to children that were deleted or renamed during migration.

**Cause:** Symlinks were not updated when targets moved.

**Solution:** Re-create all symlinks from the rename map. `find skill-sets/ -type l ! -exec test -e {} \; -print` lists broken symlinks for cleanup.

## See Also

- [topology-decision.md](./topology-decision.md) for the criteria that trigger migrations
- [taxonomy-templates.md](./taxonomy-templates.md) for the target taxonomy of the migrated skill
- [routing-mechanics.md](./routing-mechanics.md) for the routing primitives the new hub will use
- [gotchas.md](./gotchas.md) for general skill-creation failure modes that may surface during migration
