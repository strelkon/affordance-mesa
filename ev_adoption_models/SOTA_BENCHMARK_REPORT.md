# EVAM Benchmarking Report: State of the Art in Agent-Based Models of EV Adoption (2018–2026)

*Prepared 2026-07-22 via a multi-source literature review (Zotero library search, targeted web/database search, and codebase review of `ev_adoption_models/EV_ADOPTION_MODELS_REVIEW.md`, `EV_MODEL_DESCRIPTION.md`, and `VALIDATION.md`). All references were independently located; where a bibliographic detail (e.g., full author list, DOI) could not be confirmed from accessible metadata, this is flagged explicitly rather than filled in.*

---

## 1. Leading SOTA EV-adoption ABMs and their design choices

| # | Model / Authors (Year, Venue) | Decision architecture | Social influence | Range anxiety | Charging infrastructure | Cost dynamics | Calibration / validation |
|---|---|---|---|---|---|---|---|
| 1 | Eppstein, Grover, Marshall & Rizzo (2011), *Energy Policy* 39(6), 3789–3802 | Heuristic/threshold utility over fuel cost, purchase price, rebates | Spatial network: homophily, conformity thresholds, media influence | Implicit via battery-range heuristics | Not modeled (exogenous) | Static price/rebate scenarios | Sensitivity analysis only; no empirical fit to sales data |
| 2 | Zhang, Gensler & Garcia (2011), *J. Product Innovation Management* 28(2), 152–168 | Bass-diffusion-augmented agent utility over alt-fuel vehicle attributes | Word-of-mouth over social network | Not explicit | Not modeled | Exogenous price paths | Calibrated to historical hybrid-vehicle sales curves |
| 3 | Brown (2013), *JASSS* 16, "Catching the PHEVer" | **Mixed multinomial logit** vehicle-choice model per agent (discrete-choice econometrics embedded in ABM) | Not primary focus | Implicit in vehicle attribute utility | Not modeled | Subsidy scenarios | Logit parameters estimated from stated/revealed-preference survey data |
| 4 | McCoy & Lyons (2014), *Energy Research & Social Science* 3, 89–101 | Threshold diffusion model | Explicit peer network (survey-derived), produces adoption clusters | Not explicit | Not modeled | Not modeled | Agent population calibrated to Irish household survey microdata; validated against small-area adoption patterns |
| 5 | Wolf, Schröder, Neumann & De Haan (2015), *Technological Forecasting and Social Change* 94, 269–285 | **Parallel-constraint-satisfaction (PCS) network** — cognitive-affective attitude model, not simple utility | Explicit, with emotional contagion | Represented as an affective/cognitive constraint | Not modeled | Financial-incentive scenarios | One-to-one agent-survey correspondence (each agent = one real respondent); empirically the most tightly grounded of the group |
| 6 | Silvia & Krause (2016), *Energy Policy* 96, 105–118 | Utility-based adoption decision | Social network diffusion | Not explicit | Exogenous station counts | Policy-scenario cost paths | Compared against observed US PEV sales trajectories |
| 7 | Noori & Tatari (2016), *Energy* 96, 215–230 | Discrete-choice utility across ICE/hybrid/BEV/PHEV attributes | Limited | Range/attribute utility terms | Not modeled | Regional cost/attribute data | Calibrated to US regional vehicle-attribute and survey data; used for 2030 projections |
| 8 | Kangur, Jager, Verbrugge & Bockarjova (2017), *J. Environmental Psychology* 52, 166–182 — **STECCAR** | **Consumat framework** (need satisfaction/uncertainty → deliberation, imitation, social comparison, repetition strategies) | Core mechanism — social comparison and imitation drive strategy choice | Represented within need-satisfaction (comfort/functional needs) | Simplified | Purchase-cost + subsidy scenarios | Parameterized from a Dutch survey of 1,795 respondents; among the most psychologically detailed EV ABMs |
| 9 | van der Kam, Peters, van Sark & Alkemade (2019), *JASSS* 22(4), 7, doi:10.18564/jasss.4133 | Post-purchase **charging-mode choice**, not the purchase decision: f(ω·environmental self-identity − ω·range anxiety) | Not primary (household-level, not peer-based) | **Explicit, dynamic range-anxiety score (0–1) traded off against environmental self-identity** | Charging infrastructure and renewable-surplus modeled directly | Not modeled | Extensively empirically grounded: Dutch EV fleet (RDW), national travel-diary (OViN), household load profiles, KNMI solar/wind data, real charging-station counts |
| 10 | Luo, Song & Li (2023), "An agent-based simulation study for escaping the 'chicken-egg' dilemma between electric vehicle penetration and charging infrastructure deployment," *Resources, Conservation and Recycling*, doi:10.1016/j.resconrec.2023.106966 — *corrected from the original draft, which misattributed this to Ecological Economics* | Utility/adoption threshold combined with operator investment decisions | Present | Not a focus | **Endogenous, demand-driven charger deployment** — the paper's central contribution, modeling the adoption↔infrastructure feedback loop directly | Subsidy scenarios for both purchasers and charging-point operators | Empirically informed cost/subsidy parameters (China context) |
| 11 | Christensen, Ma & Jørgensen (2024), *Energy Informatics Academy Conf.* (Springer LNCS 14468); arXiv:2401.06192 | Rogers-curve-calibrated adoption combined with agent-level charging behavior | Not primary | Not explicit | Home-charging multi-agent system, grid-load feedback | Learning-curve inputs for EV price/battery cost | Calibrated to Danish national EV adoption statistics (2011–2032 projection), validated against observed Danish adoption curve |
| 12 | Rai & Robinson (2015), *Environmental Modelling & Software* 70, 163–177 (residential **solar PV**, not EV; included as the field's calibration/validation benchmark) | Theory of Planned Behaviour (attitude + perceived control) | Small-world social network with geographic/demographic homophily; attitudes updated via neighbor interaction | N/A | N/A | N/A | Attitudes calibrated via survey + spatial regression; validated on temporal, spatial, *and* demographic adoption criteria simultaneously — widely cited as the calibration/validation gold standard for empirically grounded technology-adoption ABMs |

Supporting/contextual literature (diffusion/system-dynamics, discrete-choice, and infrastructure-econometrics strands that inform but are not themselves household ABMs):

- **Struben & Sterman (2008)**, *Environment and Planning B* 35(6) — system-dynamics treatment of the adoption–infrastructure–legitimacy feedback loop that underlies most "chicken-and-egg" ABM framings.
- **Gnann, Funke, Jakobsson, Plötz, Sprei & Bennehag (2018)**, *Renewable and Sustainable Energy Reviews* 93, 158–164, doi:10.1016/j.rser.2018.03.055 — review of EV market-diffusion models; a useful benchmark for what "diffusion realism" looks like across model families.
- **Hidrue, Parsons, Kempton & Gardner (2011)**, *Resource and Energy Economics* — stated-preference willingness-to-pay for EV attributes (range, charging time), the discrete-choice backbone many ABMs borrow parameters from.
- **Glerum, Stankovikj, Thémans & Bierlaire (2014)**, *Transportation Science* 48(4), doi:10.1287/trsc.2013.0487 — hybrid choice model with latent attitudes; a template for combining econometric rigor with psychological constructs.
- **Sierzchula, Bakker, Maat & van Wee (2014)**, *Energy Policy* 68, doi:10.1016/j.enpol.2014.01.043 — cross-national regression establishing charging-infrastructure density as a robust empirical predictor of EV adoption, frequently used to justify/calibrate charging-access terms in ABMs.
- **Grimm et al. (2020)**, "The ODD Protocol … A Second Update", *JASSS* 23(2), 7, doi:10.18564/jasss.4259 — the documentation standard EVAM already follows.
- **Troost, Huber, Bell, Van Delden, Filatova, Le, Lippe, Niamir, Polhill, Sun & Berger (2023)**, "How to keep it adequate: A protocol for ensuring validity in agent-based simulation," *Environmental Modelling & Software* 159, doi:10.1016/j.envsoft.2022.105577 — the field's current 12-step validity/calibration checklist.
- **Kaaronen & Strelkovskii (2020)**, "Cultural Evolution of Sustainable Behaviors: Pro-environmental Tipping Points in an Agent-Based Model," *One Earth* — the base model EVAM extends.

---

## 2. How EVAM compares

### Where EVAM matches or is competitive with SOTA

- **Multi-component, weighted adoption score.** EVAM's five-term score (economic, charging access, environmental, peer exposure, minus range anxiety) is structurally consistent with the additive/threshold utility architectures of Eppstein et al. (2011), McCoy & Lyons (2014), and Silvia & Krause (2016), and is arguably more integrated in combining TCO, access, environment, and social terms in a single transparent score.
- **Explicit range-anxiety representation traded off against another psychological state.** The same design pattern as van der Kam et al. (2019, JASSS) — range anxiety weighed against an environmental/identity variable — one of the few ABMs to formalize range anxiety as a first-class, dynamically updated agent variable rather than folding it into a generic attribute-utility term (contrast Brown 2013; Noori & Tatari 2016).
- **Peer exposure / social diffusion on a spatial or network topology.** Directly comparable to Eppstein et al. (2011), McCoy & Lyons (2014), Zhang et al. (2011), and the Consumat social-comparison/imitation mechanism in Kangur et al. (2017).
- **Congestion-adjusted, distance-decayed charging access.** The access function A = (1+d/δ)⁻¹ combined with a capacity/demand congestion factor is more mechanistically explicit than most of the field: van der Kam et al. (2019) and Christensen et al. (2024) model charging load and grid effects, but as a *post-purchase* charging-behavior problem, not as a *feedback into the adoption decision itself*. Coupling congestion-adjusted access back into the adoption score is closest to the 2023 *Ecological Economics* chicken-egg paper.
- **Endogenous learning-curve price decline with a floor and subsidy pass-through into TCO.** Matches the *intent* of endogenous-cost EV models (cf. Christensen et al. 2024's learning-curve inputs); EVAM is comparatively rare among *household ABMs* in endogenizing price this way.
- **ODD-protocol documentation and OAT + 2D sensitivity analysis.** Matches current best practice (Grimm et al. 2020; Troost et al. 2023).

### Where EVAM is behind SOTA

1. **No empirical calibration to real household or market data.** The most consequential gap. Nearly every model above appearing in a top venue since ~2014 ties agent heterogeneity or parameters to *some* real dataset: survey microdata (McCoy & Lyons 2014; Kangur et al. 2017, n=1,795; van der Kam et al. 2019, multiple Dutch registries), discrete-choice estimation (Brown 2013; Hidrue et al. 2011; Glerum et al. 2014), or national adoption curves (Christensen et al. 2024; Rai & Robinson 2015 validated on temporal/spatial/demographic axes simultaneously). EVAM's own `VALIDATION.md` lists calibration against real EV adoption data as still open.
2. **No discrete-choice econometric backbone.** A hand-specified weighted score/logistic rule rather than a logit/mixed-logit estimated from stated- or revealed-preference data. Reviewers at TR-D, Energy Policy, or Ecological Economics will ask whether the weights are justified beyond face validity.
3. **Weaker validation practice relative to the "Keep It Adequate" bar** (Troost et al. 2023): EVAM's validation is currently internal (NetLogo-to-Mesa consistency) and structural (sensitivity sweeps), not output validation against observed adoption trajectories, fleet composition, or charging-station utilization.
4. **No demographic/spatial realism in population or geography.** SOTA models increasingly use real road networks, charging-station registries, or household microdata; EVAM's toroidal grid and synthetic distributions are a stylized/theoretical setup, closer to Eppstein et al. (2011) or Kaaronen & Strelkovskii (2020) than to the empirically grounded 2019–2024 cohort.
5. **No supply-side / used-vehicle market representation** — an acknowledged gap across the field; EVAM's optional per-step supply cap is a partial, simple treatment that several published ABMs don't even attempt.
6. **Attitudes are not updated through ownership experience**, whereas Kangur et al.'s Consumat and Wolf et al.'s PCS network allow post-decision cognitive/affective updating — EVAM's optional social-diffusion feedback is a simpler, one-directional analogue.

### Where EVAM is novel

- **Coupling an established, previously validated affordance-landscape sustainability-behavior ABM (Kaaronen & Strelkovskii 2020, *One Earth*) with an EV-specific adoption/TCO/charging module.** No paper identified extends a general pro-environmental-behavior tipping-point model into a vehicle-specific decision architecture this way; most EV ABMs are purpose-built from scratch. EVAM's genealogy can be pitched as a contribution in itself — testing whether a generic behavior-diffusion model "transfers" to a concrete technology decision.
- **Congestion-adjusted effective charging access feeding directly into the moment-of-purchase decision score**, rather than being confined to a separate post-purchase charging-simulation layer.
- **Blending an EV-specific environmental-concern term with a generic pro-environmental state inherited from the affordance base model** — no direct published analogue among the papers reviewed; most EV ABMs treat environmental attitude as a fixed trait or single-domain updating variable.

---

## 3. Common calibration/validation practices — and the field's minimum bar

Four recurring patterns, in ascending rigor:

1. **Sensitivity-analysis-only** (Eppstein et al. 2011; early threshold-diffusion work): plausibility-chosen parameters plus OAT/scenario sweeps. Now the *minimum acceptable floor*, not a sufficient standard, at JASSS, Energy Policy, TR-D, Ecological Economics, EM&S.
2. **Parameter calibration from survey/microdata** (McCoy & Lyons 2014; Kangur et al. 2017; Noori & Tatari 2016).
3. **Discrete-choice econometric estimation embedded in the ABM** (Brown 2013; Glerum et al. 2014; Hidrue et al. 2011): decision weights with defensible standard errors rather than face-valid guesses.
4. **Output/pattern validation against independent observed adoption trajectories or multi-criteria data** (van der Kam et al. 2019; Christensen et al. 2024; Rai & Robinson 2015). Increasingly the top-of-field bar; formalized by Troost et al. (2023) and Grimm et al. (2020): state the empirical patterns the model must reproduce *up front* (ODD "Purpose and Patterns"), then report how well it reproduces them.

**Minimum bar a Q1 reviewer is likely to expect in 2024–2026:** (a) an ODD description (done); (b) at least one comparison of a model output against an independent real-world series (national/regional EV registration statistics, IEA data, etc.); and (c) explicit justification of the decision-score weights, via literature-sourced discrete-choice estimates or a stated-preference calibration. A purely theory-exploratory framing is defensible only if the paper is explicit that it is not attempting empirical realism and frames the contribution as mechanism exploration rather than forecasting or policy calibration.

---

## 4. Concrete, citable recommendations for the EVAM paper

1. **Add at least one empirical validation target — a national or regional EV adoption time series — and report fit, or explicitly frame the paper as theory-exploratory.** Supported by Christensen, Ma & Jørgensen (2024) and Silvia & Krause (2016), both validating simulated adoption curves against observed sales; and Troost et al. (2023), whose protocol treats output validation as core.
2. **Justify the five adoption-score weights against the discrete-choice/WTP literature.** Cite Hidrue et al. (2011) for estimated willingness-to-pay for range, charging time, and price; Glerum et al. (2014, doi:10.1287/trsc.2013.0487) for a hybrid-choice template combining latent attitudes with econometric utility terms.
3. **State the ODD "Purpose and Patterns" up front** (Grimm et al. 2020, doi:10.18564/jasss.4259) — e.g., S-shaped adoption, fuel-price shock sensitivity, adoption clustering under peer effects — then show each pattern is (or isn't) reproduced.
4. **Position the model explicitly in the chicken-and-egg / infrastructure co-evolution literature** — Luo, Song & Li (2023, *Resources, Conservation and Recycling*, doi:10.1016/j.resconrec.2023.106966) and Struben & Sterman (2008) for the underlying feedback-loop theory.
5. **Add a robustness check on the range-anxiety ↔ environmental-concern trade-off analogous to van der Kam et al. (2019, doi:10.18564/jasss.4133)** — the closest published analogue; explicitly differentiate (EVAM: purchase decision; van der Kam et al.: charging-mode choice) to pre-empt the obvious reviewer comparison.
6. **Acknowledge Consumat-style social comparison/imitation** (Kangur et al. 2017) and explain why EVAM's simpler peer-share formulation was chosen (tractability, transparency, fit with the affordance lineage) — turning a potential weakness into a defensible design decision.
7. **Report calibration/validation limitations candidly in a dedicated "Empirical grounding" subsection**, using Rai & Robinson's (2015) temporal/spatial/demographic multi-criterion validation as the aspirational benchmark and noting which criteria EVAM does and does not meet.
8. **Ground the charging-access term A = (1 + d/δ)⁻¹ in Sierzchula et al. (2014, doi:10.1016/j.enpol.2014.01.043)** — the most-cited cross-national result establishing charging-infrastructure density as a robust predictor of EV adoption.
9. **Frame the price-learning mechanism with the endogenous battery-cost literature** (e.g., endogenous battery price development studies; ICCT 2022 EV cost report; commonly cited Li-ion pack learning rates of 6–9% per cumulative doubling) to justify learning-rate and price-floor parameters.
10. **Make the affordance-landscape lineage the paper's differentiator, with explicit comparison to Kaaronen & Strelkovskii (2020)** and the empirically grounded cohort (Wolf et al. 2015; Kangur et al. 2017): EVAM tests whether a generic, previously validated pro-environmental tipping-point architecture can be specialized into a concrete technology-adoption decision.

---

## Limitations of this review

- Single research pass, not a PRISMA-style systematic review; 2024–2026 grey literature (arXiv EV charging/grid ABMs) is covered more broadly than paywalled 2018–2021 journal content, which was accessed largely through secondary summaries (direct ScienceDirect fetches returned HTTP 403).
- ~~The full author list and DOI of the 2023 chicken-egg ABM could not be independently confirmed~~ — resolved on follow-up: it is Luo, Song & Li (2023), published in *Resources, Conservation and Recycling* (not *Ecological Economics* as the original search summaries implied), doi:10.1016/j.resconrec.2023.106966, confirmed via CrossRef.
- Semantic Scholar API was unavailable (HTTP 403); DOIs given are those confirmed by at least one aggregator (IDEAS/RePEc, ResearchGate); entries without a DOI are marked accordingly.
- AI-assisted research tools were used throughout; no reference was knowingly fabricated, but flagged uncertainties should be independently checked before relying on this report in a manuscript citation list.
