# Portugal EV Adoption Data — Calibration Notes

Collected 2026-07-22 for use with the existing `scripts/run_ev_experiments.py --targets` calibration workflow (see `VALIDATION.md`).

## 1. Important distinction: fleet (stock) share vs. new-registration (sales) share

EVAM's `ev_adoption_share` is a **stock** variable — the fraction of *agents/households currently owning an EV*, evaluated once per household at vehicle replacement. This is directly analogous to the **share of the circulating vehicle fleet that is electric**, not the commonly reported "new car sales market share" (e.g. "20% of 2024 new registrations were BEV"). Portuguese/EU press coverage overwhelmingly reports the sales-share number, which is 5–10× larger than the fleet-share number in a market still early in the transition. **Use the fleet-share series below as the calibration target, not the sales-share headlines.**

## 2. Annual BEV fleet size and stock share, Portugal 2010–2024

Source: UVE (Utilizadores de Veículos Elétricos, the Portuguese EV-user association), "Parque de Veículos Elétricos em Portugal" ([uve.pt/page/parque-ve-2024](https://www.uve.pt/page/parque-ve-2024/)), combining IMT (Instituto da Mobilidade e dos Transportes) historical registry data with ACAP registration statistics. Fleet-share denominator uses Portugal's light passenger vehicle fleet, reported at **5.8 million** in 2023 (APA, *Relatório do Estado do Ambiente*, [rea.apambiente.pt](https://rea.apambiente.pt/content/parque-rodovi%C3%A1rio)) and treated as approximately constant (~5.5–5.8M) across the decade for this share calculation — the fleet grew only slowly over this period relative to BEV growth, but this introduces a few percent of relative error in the earliest years and should be refined if a precise year-by-year fleet-size series is obtained.

| Year | BEV fleet (count) | Approx. stock share (BEV fleet / 5.8M) |
|------|-------------------:|----------------------------------------:|
| 2010 | 950 | 0.00016 |
| 2011 | 1,303 | 0.00022 |
| 2012 | 1,594 | 0.00027 |
| 2013 | 2,055 | 0.00035 |
| 2014 | 2,459 | 0.00042 |
| 2015 | 3,411 | 0.00059 |
| 2016 | 4,838 | 0.00083 |
| 2017 | 8,005 | 0.00138 |
| 2018 | 14,391 | 0.00248 |
| 2019 | 22,834 | 0.00394 |
| 2020 | 33,749 | 0.00582 |
| 2021 | 52,292 | 0.00902 |
| 2022 | 79,835 | 0.01377 |
| 2023 | 129,299 | 0.02229 |
| 2024 | 190,035 | 0.03277 |

This cross-checks against the independently reported "~3% of the circulating fleet is BEV as of 2024" figure ([Mobility Portal](https://mobilityportal.eu/portugal-historic-record-electric-vehicle/); [Razão Automóvel](https://www.razaoautomovel.com/noticias/automoveis-eletricos-circular-portugal-2024/)).

A machine-readable version is at [`outputs/portugal_ev_stock_share_targets.csv`](../outputs/portugal_ev_stock_share_targets.csv), in the `step,ev_adoption_share` format the `--targets` flag expects, with `step` as years since 2010 (0–14). To calibrate against a different EVAM start year, shift the `step` column accordingly.

## 3. Sales-share context (do not use as the primary calibration target, but useful for interpreting inflection points)

Source: [Autovista24](https://autovista24.autovistagroup.com/news/portugal-packs-a-punch-in-the-european-ev-market/); [Mobility Portal](https://mobilityportal.eu/portugal-historic-record-electric-vehicle/); [EAFO](https://alternative-fuels-observatory.ec.europa.eu/general-information/news/portugal-january-2025-bevs-reach-record-225-market-share).

- 2015: BEV sales share ≈ 0.5% (coincides with reintroduction of purchase incentives — a plausible policy-shock event to reproduce if EVAM is calibrated to this period).
- 2020: PHEV sales share 60.2% of the EV segment; BEV sales share lower than PHEV.
- 2022: BEVs overtake PHEVs in new-registration share for the first time.
- 2023: BEV sales share ≈ 20% (implied from adjacent-year figures); combined EV sales share ≈ 33%.
- 2024: BEV sales share 19.9–20%, 41,932 BEV registrations, 27,950 PHEV registrations; combined plug-in share 33.3% (69,882 units) of new light passenger cars.
- Jan 2025: BEV sales share hit a record 22.5%.
- Full-year 2025: BEV sales share 23.2%, PHEV 15.1%; combined rechargeable share ≈ 34%.

The 2015 incentive-reintroduction inflection and the 2022 BEV/PHEV crossover are the two clearest "policy-pattern" candidates for the ODD "Purpose and Patterns" reproduction test recommended in the SOTA benchmark report (see `SOTA_BENCHMARK_REPORT.md`, recommendation 3).

## 4. Portuguese EV purchase subsidy (for the `subsidy` parameter)

Source: [The Portugal Post](https://theportugalpost.com/posts/why-portugals-ev-subsidies-matter-more-as-european-car-sales-stall); [Mobility Portal](https://mobilityportal.eu/portugal-reopens-incentives-vehicles/); [EAFO](https://alternative-fuels-observatory.ec.europa.eu/general-information/news/portugal-launches-2025-incentive-programmes-boost-zero-emission-mobility).

- Administered through the **Fundo Ambiental** (Environmental Fund).
- Private-individual grant: **€2,000–€4,000** per BEV purchase depending on the programme year (2026 programme: up to €4,000).
- Eligibility caps: vehicle gross price ≤ €38,500 (≤ €55,000 for >5-seat EVs); requires scrapping a vehicle ≥10 years old in some programme years.
- Programme budget has varied sharply year to year and has been subject to funds-exhausted cutoffs mid-year: **€8.5M (2024)**, **€10M (2025 zero-emission passenger transport programme)**, **€17.6M (2026 tranche, open until 12 Feb 2026 or funds exhausted)**. This year-to-year discontinuity is itself a realistic feature (intermittent, capped subsidy availability) that EVAM's constant `subsidy` parameter does not currently capture — see the "time-varying prices" realism recommendation in the earlier model review.

## 5. Charging infrastructure (for `charger_expansion_rate` / `initial_charging_coverage` calibration)

Source: [V2Charge](https://v2charge.com/integration-mobi-e-portugal/); [Portugal Global](https://www.portugalglobal.pt/en/news/2024/april/portugal-leads-the-way-with-interoperable-ev-charging-network/); [EV Infrastructure News](https://www.evinfrastructurenews.com/ev-networks/mobi-e-maps-portugal-s-ev-success).

- **MOBI.E** is Portugal's single interoperable public charging network (any user can access any station regardless of operator).
- Mid-2024: **4,815 charging posts**, **10,208 plugs**, of which **1,695 (36%) are fast/ultra-fast**.
- 2023: >4,450 publicly accessible charging stations.
- Usage: >487,500 charging sessions in May 2024 alone; >3.276M sessions in the first 7 months of 2024 (+67% YoY) — this rapid usage growth is a proxy for the congestion dynamics EVAM's `charger_capacity`/congestion mechanism is designed to capture, and could motivate a non-infinite `charger_capacity` calibration run.

## 5b. Household income anchor (Eurostat EU-SILC, retrieved 2026-07-23)

Source: Eurostat `ilc_di03` (mean and median equivalised net disposable
income, EUR, sex = total, age = total) and `ilc_di12` (Gini coefficient of
equivalised disposable income), both for Portugal, retrieved via the
Eurostat API.

| Year | Mean equivalised income (EUR) | Median (EUR) |
|------|------------------------------:|-------------:|
| 2010 | 10,540 | 8,678 |
| 2011 | 10,407 | 8,410 |
| 2012 | 10,227 | 8,323 |
| 2013 | 9,899 | 8,177 |
| 2014 | 9,856 | 8,229 |
| 2015 | 9,996 | 8,435 |
| 2016 | 10,562 | 8,782 |
| 2017 | 10,863 | 9,071 |
| 2018 | 11,063 | 9,346 |
| 2019 | 11,786 | 10,023 |
| 2020 | 12,696 | 10,800 |
| 2021 | 13,113 | 11,089 |
| 2022 | 13,148 | 11,014 |
| 2023 | 14,368 | 11,824 |
| 2024 | 14,951 | 12,646 |

Period averages: mean **€11,565**, median **€9,656**, mean/median ratio
≈ 1.20. For a lognormal, mean/median = exp(σ²/2), giving **σ ≈ 0.60** —
independently cross-checked by the Gini coefficient (31.2–34.5 over
2014–2024, ≈ 33 mid-period; lognormal Gini = 2Φ(σ/√2) − 1 gives σ ≈ 0.60
as well). The two derivations agreeing supports the lognormal shape.

Model anchor: `income_mean = 11600`, `income_sd = 7600` with
`income_distribution = "lognormal"` — this reproduces σ ≈ 0.60 and a
median of ≈ €9,700 against the empirical ≈ €9,656.

Note: equivalised income is per adult-equivalent, not per household; the
household equivalence-scale factor (~1.6× for a typical household) is
deliberately absorbed into the fitted `income_budget_share` rather than
scaled into income, so the income distribution itself stays exactly as
published by Eurostat.

## 6b. Calibration result, round 2 (2026-07-23) — current defaults

Round 2 supersedes the round-1 fit below. Changes: (i) `income_mean`/
`income_sd` pinned to the Eurostat anchor of §5b (no longer searched);
only `income_budget_share` absorbs the affordability slack, and it fitted
to **0.108** — essentially the paper's 10% rule, now against empirical
income; (ii) the objective is **log-RMSE on 2010–2020 only** (floored at
half an agent's share), with **2021–2024 held out**; (iii) the scenario
seeds the 2010 stock (`initial_ev_share=0.00016` → 1 agent of 4,000).

Shipped values: `ev_purchase_price=44000`, `ice_purchase_price=23200`,
`ev_wright_learning_rate=0.18`, `ev_wright_reference_adopters=5`,
`charger_expansion_rate=1.86`, `adoption_threshold=0.02` (search floor —
the fitted regime is budget-gate-dominated), `income_budget_share=0.108`.

Results over 12 seeds: fit window (2010–2020) log-RMSE 0.36 / raw RMSE
0.0006; **hold-out (2021–2024) log-RMSE 0.29 / raw RMSE 0.006** — no
overfitting signal, with a systematic undershoot of the post-2020 surge
(2024: model ≈ 2.3% vs observed 3.28%) attributable to drivers outside
the model (model availability, fleet electrification, 2022 fuel-price
spike). Full write-up in `VALIDATION.md`.

## 6. Calibration result, round 1 (2026-07-22) — superseded

`EVParams` defaults were recalibrated against the Section 2 stock-share
series via a random-search + local-refinement fit
(`scripts/calibrate_portugal.py`): `income_mean`/`income_sd`/
`income_distribution`, `ev_purchase_price`, `ice_purchase_price`,
`ev_price_learning_model`/`ev_wright_learning_rate`/
`ev_wright_reference_adopters`, `income_budget_share`, `adoption_threshold`,
and `charger_expansion_rate`. A dedicated `"portugal_2010_2024"` scenario
additionally applies a smooth subsidy ramp (zero 2010–2014, linear
EUR500→EUR4,000 2015–2024, approximating the real 2015 incentive
reintroduction and the documented grant range) and the grid/agent scale the
search was run at (60×60 grid, 4,000 agents, 14 steps).

Result: RMSE ≈ 0.003 over 12 seeds (`python scripts/run_ev_experiments.py
--scenarios portugal_2010_2024 --seeds 1..12 --steps 14 --targets
outputs/portugal_ev_stock_share_targets.csv`), against target values
spanning 0.02%–3.3%. The model reproduces the near-zero early years and the
final-year level well; it rises faster than the target through the middle
of the period, a "backlog-then-burst" artifact of the one-shot-per-
replacement-cycle decision (agents who couldn't afford an EV at their first
opportunity keep re-evaluating every subsequent step, so a wave clears the
affordability bar together once the subsidy ramp/price decline catch up,
rather than diffusing as smoothly as the real market did). See
`VALIDATION.md` for the full write-up, including the scale-dependency
caveat (the fit does not hold at other `number_of_agents` without rescaling
`charger_expansion_rate`, since chargers are added at an absolute
per-step rate, not one scaled to population).

## 7. Caveats

- The stock-share series treats the Portuguese light-vehicle fleet as constant at 5.8M across 2010–2024; the true fleet size grew somewhat over this period (ACAP/APA report slow year-on-year growth), so early-year shares above are slightly overstated and later-year shares slightly understated. Refine with year-by-year fleet totals from ACAP/INE if higher precision is needed.
- Sales-share and stock-share numbers come from different reporting conventions (ACAP/EAFO for sales, UVE/IMT for stock) and are not perfectly reconciled against each other in the source material.
- All figures were retrieved via web search in July 2026 from secondary reporting (Mobility Portal, Autovista24, The Portugal Post, EAFO, V2Charge, Portugal Global, e-auto.pt) referencing UVE, ACAP, APA, and EAFO as primary sources; the primary UVE/ACAP publications were not independently downloaded and verified line-by-line — recommend a spot check against [uve.pt](https://www.uve.pt/page/parque-ve-2024/) and [acap.pt](https://acap.pt) before using in a manuscript.
