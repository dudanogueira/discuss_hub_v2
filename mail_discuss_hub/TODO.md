# TODO - Discuss Hub Core

## Team <-> Channel/Gateway Assignment (Design Draft)

### Goal
- Allow conversations to be routed/assigned by team (not just a single user).
- Keep the core generic for all sources (gateway, livechat, internal).

### Decisions Needed
- Assignment mode:
  - `all_members`: every team member is added to the channel.
  - `assigned_only`: only assigned members join; others can opt-in.
- Visibility rule (no membership = no access) vs. automatic membership.

### Core (mail_discuss_hub) Proposal
- Model `mail.discuss.team`
  - Fields: `name`, `company_id`, `member_ids`, `leader_id`, `assignment_mode`.
- Extend `discuss.channel`
  - Fields: `team_id` (m2o), `assigned_user_id` (m2o) or `assigned_user_ids` (m2m).
- Behavior:
  - If `assignment_mode = all_members`, add all team members to channel members.
  - If `assigned_only`, add only assigned member(s); others can join manually.

### Gateway Addon (mail_discuss_hub_gateway)
- Add `default_team_id` on `mail.gateway`.
- When a channel is created from gateway:
  - Set `team_id = default_team_id`.
  - Apply assignment mode behavior.

### Integration Addons
- `mail_discuss_hub_crm` and `mail_discuss_hub_helpdesk_mgmt`:
  - Bidirectional sync between external teams and `mail.discuss.team`.
  - Use context flags to avoid loops.

### UI (Discuss)
- Channel header: show Team + Assigned.
- Actions:
  - Assign to me
  - Add team member
  - Join channel (when `assigned_only`)
- Optional: sidebar filters by team.

### Notes / Risks
- Multi-company: team/company must match channel company.
- Avoid auto-creating teams in core; keep link-driven.
- Membership growth in `all_members` mode may reduce usability.
