# Validation Notes

This Mesa implementation preserves the original conceptual mechanisms:
environmental affordances, personal pro/non states, individual learning, social
learning through networks, mutation, movement, and cultural niche construction.
It intentionally excludes nudge, policy-intervention, and consumer-choice
extensions so validation focuses on the NetLogo v1.2.0 model.

Known implementation deviations from the NetLogo v1.2.0 model:

1. Movement is a discrete Moore-neighbour random walk on a toroidal grid. The
   NetLogo model uses continuous headings with `rt random 45`, `lt random 45`,
   and `fd 1`.
2. Behaviour attempts are guarded by `max_behavior_attempts` to prevent rare
   infinite loops. NetLogo loops until an agent behaves.
3. The Klemm-Eguiluz network generator is an approximation of the NetLogo
   procedure and has not been proven byte-for-byte equivalent.
4. Random number streams are Mesa/Python/NumPy streams, so exact trajectory
   identity with NetLogo should not be expected even with comparable seeds.
5. This port reports affordance share in the model data collector; the NetLogo
   BehaviorSpace experiments often report a pro-affordance patch count.

To compare against NetLogo outputs, place BehaviorSpace CSV files in
`original_outputs/` and run:

```bash
python scripts/validate_against_netlogo.py
```

The validation script reads matching parameter columns where present, runs Mesa
with comparable settings, and writes metric differences to `outputs/validation/`.
