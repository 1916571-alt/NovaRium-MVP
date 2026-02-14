# V2 Demo Playbook (10 Minutes)

## Goal
- Show an end-to-end learning loop: synthetic platform data -> SQL analysis -> funnel bottleneck diagnosis -> experiment decision -> adoption/journey/community outcome.

## Prep (2 min)
- Start API:
```bash
cd v2_core
uvicorn apps.api.main:app --reload --port 8100
```
- Start Web:
```bash
cd v2_core/apps/web
npm run dev
```
- Ensure env:
  - `DATABASE_URL` is configured
  - `NEXT_PUBLIC_API_BASE=http://localhost:8100/v2`

## Flow Script (8 min)
1. Login + Workspace + Project (1 min)
- Open `/`.
- Create workspace and project from onboarding.
- Explain role model: owner/editor/viewer.

2. Bootstrap synthetic data (2 min)
- Choose template (`commerce` recommended for demo).
- Choose seed preset (`standard`).
- Turn on starter SQL challenge seeding.
- Run bootstrap and note `run_id`.

3. Diagnose with Funnel (1 min)
- Go to `/analytics`.
- Set project and run_id.
- Show `bottleneck_step`, conversion/dropoff by step.
- Explain why this stage is the optimization target.

4. Verify with SQL (2 min)
- Go to `/sql`.
- Run starter query or create snippet with `run_id` filter.
- Show variant-level rate difference and row-level evidence.
- Save snippet with tags (`funnel`, `conversion`).

5. Experiment decision + adoption (1 min)
- Go to `/experiments`.
- Analyze run (`run_id`) and show recommendation.
- Use adopt flow for winning variant.

6. Personalized endpoint + community (1 min)
- Go to `/journey` and show user-specific state updates.
- Go to `/community` and post rationale:
  - What changed
  - Why selected
  - Evidence query reference

## Demo Talking Points
- Same starting platform, different teams/users can choose different adoptions.
- Each adoption history creates a distinct endpoint ("mini-homepage" trajectory).
- Decisions are explainable because they are tied to SQL evidence and funnel diagnostics.

## Optional Operations Note
- Dry-run cleanup:
```bash
python v2_core/scripts/cleanup_stale_simulations.py --retention-days 30
```
- Apply cleanup:
```bash
python v2_core/scripts/cleanup_stale_simulations.py --retention-days 30 --apply
```
- Dry-run expired scenario share-link cleanup:
```bash
python v2_core/scripts/cleanup_expired_scenario_shares.py
```
- Apply expired scenario share-link cleanup:
```bash
python v2_core/scripts/cleanup_expired_scenario_shares.py --apply
```
