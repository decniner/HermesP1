# Balance Tracking with State File

## Why Not Just Query the API?

DeepSeek's `/user/balance` endpoint returns **current remaining** balance only. There is no `/usage` or `/billing/usage` endpoint (confirmed: returns 404). To show "total used," we must track it ourselves by comparing balance snapshots.

## The State File Pattern

File: `balance_state.json` (co-located with kanban_server.py)

```json
{"last_topped_up": 2.34, "last_granted": 0.0, "total_used": 0.38}
```

## Tracking Logic (Python)

```python
state = _load_state()  # reads balance_state.json

for bi in ds_data.get('balance_infos', []):
    topped = float(bi['topped_up_balance'])
    granted = float(bi['granted_balance'])

    # Only track after first baseline is established
    if state['last_topped_up'] > 0 or state['last_granted'] > 0:
        # Detect drops → those are consumption
        topped_drop = state['last_topped_up'] - topped
        if topped_drop > 0:
            state['total_used'] += topped_drop
        granted_drop = state['last_granted'] - granted
        if granted_drop > 0:
            state['total_used'] += granted_drop

    # Update state with current values
    state['last_topped_up'] = topped
    state['last_granted'] = granted

_save_state(state)
```

## Edge Cases Handled

| Event | Behavior |
|-------|----------|
| First ever run | Baseline set, usage=0 (no prior data) |
| Usage occurs | Topped_up drops → difference accumulated |
| User tops up | Topped_up increases → no usage counted |
| Post top-up usage | Still tracks correctly (new baseline = increased amount) |
| Server restart | State file survives, tracking resumes |
| State file deleted | Resets to 0 baseline, starts fresh |

## What Gets Sent to the Frontend

Added to each balance_info object:

```python
bi['total_used'] = round(state['total_used'], 2)       # e.g. 0.38
bi['total_used_jpy'] = round(state['total_used'] * jpy_rate, 0)  # e.g. 62
```

The frontend accesses these as `bi.total_used` and `bi.total_used_jpy`.
