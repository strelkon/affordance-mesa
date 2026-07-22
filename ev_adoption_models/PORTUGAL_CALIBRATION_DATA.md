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

## 6. Caveats

- The stock-share series treats the Portuguese light-vehicle fleet as constant at 5.8M across 2010–2024; the true fleet size grew somewhat over this period (ACAP/APA report slow year-on-year growth), so early-year shares above are slightly overstated and later-year shares slightly understated. Refine with year-by-year fleet totals from ACAP/INE if higher precision is needed.
- Sales-share and stock-share numbers come from different reporting conventions (ACAP/EAFO for sales, UVE/IMT for stock) and are not perfectly reconciled against each other in the source material.
- All figures were retrieved via web search in July 2026 from secondary reporting (Mobility Portal, Autovista24, The Portugal Post, EAFO, V2Charge, Portugal Global, e-auto.pt) referencing UVE, ACAP, APA, and EAFO as primary sources; the primary UVE/ACAP publications were not independently downloaded and verified line-by-line — recommend a spot check against [uve.pt](https://www.uve.pt/page/parque-ve-2024/) and [acap.pt](https://acap.pt) before using in a manuscript.
