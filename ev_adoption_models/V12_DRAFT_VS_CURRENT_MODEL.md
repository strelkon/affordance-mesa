# v12 draft (Eva_JorgeNike_versao12.pdf) vs. current model — consistency check

Checked 2026-07-23 against branch `evam-model-review-fixes` @ `b390871`
(PR #2: range-anxiety/budget-gate fixes, Wright pricing, empirical income
anchor, Portugal calibration with 2021–2024 hold-out).

## Verdict in one paragraph

The v12 draft describes the **pre-review model**. One important formula the
draft carries (range anxiety) is now *correct* against the code — the code
was fixed to match the paper. But the economic component, the sensitivity
traits, the income distribution, the price-learning mechanism, and the
affordability treatment described in §3/Appendix A no longer match the
implementation, and §4's results are **not reproducible with the current
version in either direction**: the draft's own prose (baseline 12%,
subsidy ~30%) contradicts its own updated figures (~35%, ~58%), and the
current model produces **0.2–0.5% adoption in all five illustrative
scenarios** because the calibrated affordability gate and Wright pricing
were fitted at Portugal scale (4,000 agents), not at `colleague_baseline`
scale (100 agents). The paper's strongest new asset — empirical income
(Eurostat) + calibration to Portugal 2010–2020 with a genuine 2021–2024
hold-out — is not mentioned at all.

## 1. Now consistent (keep as-is)

| Draft location | Item | Status |
|---|---|---|
| p. 10, p. 21 | Range anxiety `R = s_range · (1 − A_eff)` | ✅ Code now implements exactly this (was flat penalty before PR #2). |
| p. 5, p. 16 | Charging access `A = (1 + d/δ)⁻¹`, congestion factor `F = min(1, Cap/D)` | ✅ Unchanged. |
| p. 8–9 | Score weights, deterministic/logistic rules, charging component 0.7/0.3, environmental blend `(1−w)·env + w·pro_env` | ✅ Unchanged (but see threshold *value*, §3). |
| p. 7 | Peer adoption share definition | ✅ Unchanged. |

## 2. Formula/mechanism mismatches (must fix in text)

1. **Economic component** (p. 9 and p. 21). Draft:
   `Econ = (0.5 + s_price)·econScore + 0.1·affordability`.
   Current code: `Econ = s_price · econScore` with `s_price ~ U(0.5, 1.5)`;
   the additive affordability term was **removed**.
2. **Affordability is a hard gate, not a score term.** The draft's sentence
   "each agent cannot spend more than 10% of its annual income" is now
   *actually true* — implemented as
   `(TCO_EV / tco_years) ≤ income_budget_share · income` with
   `income_budget_share = 0.108`, **fitted against empirical income data
   and landing at the 10% rule**. The draft describes the old (wrong)
   mechanism; the new one is both correct and a better story.
3. **Peer component** (p. 9, p. 21): `(0.5 + s_peer)` → now `s_peer`
   directly, with `s_peer ~ U(0.5, 1.5)`. Identical distribution, simpler
   equation.
4. **Table 1 (p. 6) is stale on four rows**:
   - Income: `N(30000, 8000)` → **lognormal, mean 11,600 / sd 7,600 —
     empirical** (Eurostat EU-SILC `ilc_di03` for Portugal, 2010–2024 avg
     €11,565; σ ≈ 0.60 cross-confirmed by mean/median ratio and Gini
     `ilc_di12`).
   - Price sensitivity: `U(0,1)` → `U(0.5, 1.5)`.
   - Peer sensitivity: `U(0,1)` → `U(0.5, 1.5)`.
   - Vehicle age: `Uniform(1,12)` → by default staggered
     `U(0, r_i − 1)` per agent (removes the synchronized replacement burst
     at step 1); `Uniform(1,12)` only if staggering is disabled.
5. **Price learning** (p. 3, p. 20). The linear formula
   `p_eff = max(p(1 − η·s), p·floor)` is no longer the default. Default is
   **Wright's law**: `p(N) = p₀ · (N/N₀)^(−b)`, `b = −log₂(1 − LR)`,
   LR = 0.18, N₀ = 5 adopters, floored at 0.5·p₀. (The draft's own
   "learning (or experience) curve" framing finally matches the
   implementation — but the displayed formula is the linear proxy, which
   is now the non-default option.)
6. **Time-varying policy/prices not mentioned.** `subsidy`, `fuel_price`,
   `electricity_price` can now follow per-step schedules
   (`current_subsidy` etc.); the Portugal scenario uses a subsidy ramp
   (€0 2010–2014, €500→€4,000 2015–2024).
7. **ODD Appendix**:
   - "Input Data: the model uses no external datasets" (p. 20) is **no
     longer true** — income is anchored to Eurostat EU-SILC and the
     defaults are calibrated to the UVE/ACAP-derived Portuguese BEV
     fleet-share series with a hold-out. This should become a highlighted
     strength, not an omission.
   - Telemetry list (p. 18) missing `last_affordable`.
   - Optional mechanisms missing: discounted TCO (`discount_rate`),
     income-correlated home charging (`home_charging_income_weight`),
     staggered initial age, price schedules, `portugal_2010_2024` scenario.
8. **Minor carried-over items**: replacement-interval text still proposes
   Normal(11, 1) (Voelcker) while Table 1 and the code use Uniform(6, 14);
   consumption units "L/kWh" should be kWh/km; "Thie parameter" typo
   (p. 6); Introduction quotes a long verbatim passage from [10] that
   should be paraphrased; two `[?]` citations unresolved.

## 3. Default parameter values cited implicitly (all changed)

| Parameter | v12-era value | Current default | Provenance |
|---|---|---|---|
| `income_mean/sd` | 30000/8000 normal | **11600/7600 lognormal** | Eurostat (empirical) |
| `ev_purchase_price` | 35000 | **44000** | calibrated |
| `ice_purchase_price` | 25000 | **23200** | calibrated |
| `adoption_threshold` | 0.34 | **0.02** | calibrated (search floor; budget-gate-dominated regime) |
| `charger_expansion_rate` | 2.0 | **1.86** | calibrated |
| price learning | linear, rate 0 (off) | **Wright, LR 0.18, N₀ 5** | calibrated |
| `income_budget_share` | (not in model) | **0.108** | fitted; confirms the 10% rule |

## 4. Results section (§4) — not reproducible; needs rebuilding

**Internal inconsistency first**: the prose still reports v11 numbers
(baseline 12%, subsidy ≈30%, "unexpected" subsidy dip at 8–10k) while the
v12 figures show ≈35% baseline / ≈58% subsidy and *no* subsidy dip and a
*monotonic* fuel-price curve (the v11 non-monotonicity the text still
discusses is gone from the v12 Figure 2 — itself evidence these single-run
curves are seed noise).

**Against the current model**: with current defaults, the five illustrative
scenarios produce (200 steps, 6 seeds, mean final share):

| Scenario | v12 Fig. 1 | Current model |
|---|---|---|
| colleague_baseline | ≈0.35 | **0.003** |
| no_policy | ≈0.00 | 0.002 |
| subsidy | ≈0.58 | **0.005** |
| fuel_price | ≈0.50 | 0.003 |
| charging_expansion | ≈0.42 | 0.003 |

Two structural reasons, both intended consequences of the calibration:

1. **The affordability gate binds hard at empirical incomes.** At list
   price €44k with €8k subsidy, only ≈0.3% of the lognormal income
   distribution clears `annual cost ≤ 0.108 × income`; even at the Wright
   price floor the ceiling is ≈6.5% (≈12% at €12k subsidy, ≈2% with no
   subsidy).
2. **Wright pricing cannot ignite at 100 agents.** The price stays at list
   until 5 agents adopt, but 0.3% affordability × 100 agents ≈ 0 first
   adopters — the price-decline feedback never starts. The calibrated
   defaults presuppose the Portugal scenario's 4,000-agent scale.

**Recommendation for v13 §4**: replace the five illustrative scenarios as
the paper's core results with:

1. The **Portugal calibration + hold-out** (fit 2010–2020 log-RMSE 0.36;
   hold-out 2021–2024 log-RMSE 0.29; documented undershoot of the
   post-2020 surge) — this directly supplies the empirical-validation bar
   that the SOTA benchmark identified as the field's minimum expectation.
2. **Policy counterfactuals run on the Portugal scenario** (4,000 agents,
   ≥10 seeds, mean ± CI): e.g. no-subsidy counterfactual, doubled charger
   rollout, earlier subsidy introduction. These replace the abstract
   subsidy/fuel/charging sweeps with historically-anchored experiments.
3. If abstract sensitivity sweeps are kept, run them at Portugal scale
   with ≥10 seeds and error bars, and drop all threshold/tipping-point
   claims that do not survive averaging (the v11→v12 figure instability
   demonstrates why).
4. Report the two structural findings the calibration produced: (i) the
   fitted regime is **budget-gate-dominated** (score threshold at the
   search floor — affordability, charging access, and the subsidy/price
   path do the explanatory work); (ii) the model **undershoots the
   post-2020 surge**, whose drivers (model availability, fleet
   electrification, 2022 fuel-price spike) are outside scope — an honest
   scope statement, not a failure.

## 5. Suggested §4 reproduction commands

```bash
# Portugal calibration + hold-out figure
python scripts/run_ev_experiments.py --scenarios portugal_2010_2024 \
    --seeds 1 2 3 4 5 6 7 8 9 10 11 12 --steps 14 \
    --targets outputs/portugal_ev_stock_share_targets.csv

```

Counterfactuals need a `subsidy_schedule` override the CLI cannot express
(`None`/tuples), so run them from Python:

```python
from affordance_mesa.ev_model import EVAdoptionModel
from affordance_mesa.ev_params import EVParams

# No-subsidy counterfactual on the calibrated Portugal scenario
params = EVParams.from_scenario("portugal_2010_2024",
                                subsidy_schedule=None, subsidy=0.0)
shares = []
for seed in range(1, 13):
    m = EVAdoptionModel(params, seed=seed)
    m.run_model(14)
    shares.append(m.datacollector.get_model_vars_dataframe()["ev_adoption_share"])
```
