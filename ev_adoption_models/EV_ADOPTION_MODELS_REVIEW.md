# EV Adoption Model Literature Review

This review summarizes six related model families for electric vehicle adoption,
with emphasis on mechanisms that could inform an affordance-based agent model.
The structured research outputs are in `ev_adoption_models/results/` and all
passed the local `fields.yaml` validation script.

## Scope

The literature on EV adoption models is broad, but six model families are most
relevant for extending an affordance landscape model:

1. Agent-based and microsimulation models.
2. Diffusion and system dynamics models.
3. Discrete choice and hybrid choice models.
4. Social network and peer-effect models.
5. Charging infrastructure and spatial adoption models.
6. Policy and total cost of ownership models.

## High-Level Findings

EV adoption is usually not modeled as a single consumer-choice event. The
stronger models combine several mechanisms: household heterogeneity, price and
total-cost barriers, charging access, social visibility, policy incentives,
technology learning, and vehicle replacement timing. For an affordance model,
the most transferable idea is to treat EV adoption as the result of both
objective action opportunities and perceived feasibility.

The closest analogue to the current affordance model is the agent-based EV
adoption literature. Studies such as Eppstein et al. on PHEV market penetration,
McCoy and Lyons on Irish microsimulation, Brown's mixed-logit ABM, and Kangur et
al.'s psychologically grounded ABM all represent heterogeneous agents who update
or act under social and contextual influence. Useful sources include
[Eppstein et al. 2011](https://doi.org/10.1016/j.enpol.2011.04.007),
[McCoy and Lyons 2014](https://doi.org/10.1016/j.erss.2014.07.008),
[Brown 2013](https://doi.org/10.18564/jasss.2127), and
[Kangur et al. 2017](https://doi.org/10.1016/j.jenvp.2017.01.002).

Aggregate diffusion and system dynamics models are useful for feedback
structure, not micro-behavioral detail. They emphasize reinforcing loops among
adoption, infrastructure, cost reductions, legitimacy, and policy support.
Representative sources include
[Struben and Sterman 2008](https://doi.org/10.1068/b33022t),
[Shepherd et al. 2012](https://doi.org/10.1016/j.tranpol.2011.12.006),
[Pasaoglu et al. 2016](https://doi.org/10.1016/j.techfore.2015.11.028), and the
review by [Gnann et al. 2018](https://doi.org/10.1016/j.rser.2018.03.055).

Discrete choice and hybrid choice models provide the strongest empirical
foundation for purchase probabilities. They estimate willingness to pay for
price, range, charging time, fuel/electricity cost, infrastructure, incentives,
and latent attitudes. Representative work includes Brownstone, Bunch, and Train
on joint RP/SP mixed logit, Hidrue et al. on willingness to pay, Glerum et al.
on hybrid choice, Helveston et al. on U.S. and China preferences, and Axsen et
al. on lifestyle heterogeneity. Relevant links include
[Hidrue et al. 2011](https://www.sciencedirect.com/science/article/pii/S0928765511000200),
[Glerum et al. 2014](https://doi.org/10.1287/trsc.2013.0487), and
[Helveston et al. 2015](https://www.cmu.edu/me/ddl/publications/2015-TRA-Helveston-etal-EVs-in-China-US.pdf).

Social network and peer-effect studies show that EV uptake is socially
interdependent. Peer adoption, local visibility, word of mouth, and perceived
normality shift the effective choice set. This maps directly onto social
learning in the affordance model. Useful sources include
[McCoy and Lyons 2014](https://www.sciencedirect.com/science/article/pii/S2214629614000863),
[Kangur et al. 2017](https://research.rug.nl/en/publications/an-agent-based-model-for-diffusion-of-electric-vehicles),
[Liu et al. 2017](https://www.sciencedirect.com/science/article/pii/S1361920916301031),
and [Edelenbosch et al. 2018](https://dspace.library.uu.nl/handle/1874/375563).

Charging infrastructure and spatial adoption models are central for an
affordance framing. Charging availability is not just an explanatory variable;
it is a local opportunity structure. Stronger studies distinguish charger
counts, accessibility, fast-charging corridors, home charging, land-use context,
and spatial spillovers. Representative sources include
[Sierzchula et al. 2014](https://doi.org/10.1016/j.enpol.2014.01.043),
[Li et al. 2017](https://doi.org/10.1086/689702),
[Narassimhan and Johnson 2018](https://doi.org/10.1088/1748-9326/aad0f8),
[White et al. 2022](https://doi.org/10.1016/j.erss.2022.102663), and
[Qian et al. 2024](https://doi.org/10.1016/j.trd.2024.104400).

Policy and total cost of ownership models are the best source for cost
mechanisms. They translate purchase subsidies, taxes, fuel prices, electricity
prices, charging costs, depreciation, maintenance, and vehicle lifetime into
adoption conditions. Useful sources include
[Langbroek et al. 2016](https://doi.org/10.1016/j.enpol.2016.03.050),
[Danielis et al. 2018](https://doi.org/10.1016/j.enpol.2018.04.024),
[Munzel et al. 2019](https://doi.org/10.1016/j.eneco.2019.104493),
and [Noll et al. 2024](https://doi.org/10.1016/j.apenergy.2024.124838).

## Transferable Mechanisms For An Affordance-Based EV ABM

The most useful model design is modular:

1. Affordance layer: local charging access, home charging, public charging,
   fast-charging corridors, dealership/model availability, parking access, and
   financial affordability.
2. Personal-state layer: environmental orientation, innovation affinity, risk
   tolerance, range anxiety, price sensitivity, and EV familiarity.
3. Choice layer: probability of EV purchase conditional on replacement need,
   affordability, charging feasibility, and perceived usefulness.
4. Social layer: peer exposure, neighborhood visibility, word of mouth, and
   social norm updating.
5. Policy layer: purchase subsidies, taxes, fuel/electricity prices, charging
   infrastructure support, and information campaigns.
6. Feedback layer: adoption increases visibility, encourages charger rollout,
   reduces perceived risk, and may reduce costs through technology learning.

For the existing Mesa affordance model, the most natural extension is not to
replace the behavior rule with a full vehicle-choice model immediately. A safer
first step is to add EV-specific affordance fields and let them modify the
probability of pro-EV behavior:

```text
effective_EV_propensity =
    personal_EV_state
    + peer_exposure_effect
    + charging_affordance_effect
    - price_or_TCO_barrier
    - range_anxiety_barrier
```

This preserves the affordance logic while allowing empirical mechanisms from EV
adoption models to enter as interpretable modules.

## Specific Design Guidance

For price mechanisms, use TCO literature to represent cost as more than upfront
price. Include purchase price, subsidy, expected fuel savings, electricity or
charging price, annual mileage, maintenance, home charger cost, and depreciation
where data are available. Price should affect feasibility and adoption
probability, not simply subtract from environmental attitude.

For infrastructure, avoid using only a global charger count. Treat charging as a
spatial affordance with home access, nearby public access, destination access,
fast-charging corridor access, reliability, and congestion if possible.

For social learning, use local adoption exposure or network-neighbor adoption to
change perceived feasibility, risk, and normality. Peer effects should be
allowed to amplify infrastructure and policy effects.

For heterogeneity, represent households by at least income or budget, dwelling
type, annual mileage, car replacement timing, environmental preference, and
innovation affinity. These are repeatedly important across choice, ABM, TCO,
and infrastructure studies.

## Key Gaps In The Literature

Several gaps are relevant for a new research contribution:

1. Many models still weakly connect micro-level social influence with spatial
   charging access.
2. Used EV markets, resale value, vehicle availability, and supply constraints
   are under-modeled.
3. Home charging, renter status, multifamily housing, and equity constraints
   are often too coarse.
4. Public charging is often represented as station count, not reliability,
   congestion, price, or practical accessibility.
5. Preference updating after trial, ownership experience, and peer information
   remains simplified.
6. Policy interactions are usually clearer in system dynamics and TCO models
   than in household-level ABMs.

## Structured Outputs

Validated JSON files:

- `Agentbased_EV_adoption_models.json`
- `Diffusion_and_system_dynamics_EV_adoption_models.json`
- `Discrete_choice_and_hybrid_choice_EV_adoption_models.json`
- `Social_network_and_peer_effects_EV_adoption_models.json`
- `Charging_infrastructure_and_spatial_EV_adoption_models.json`
- `Policy_and_total_cost_of_ownership_EV_adoption_models.json`

Validation result: 6 of 6 passed with 100 percent required-field coverage.

Uncertainty flags: only the agent-based item has fields marked uncertain:
`spatial_or_infrastructure_representation`, `calibration_or_estimation`, and
`validation_approach`. This reflects heterogeneity across ABM papers rather than
failure to identify the model family.
