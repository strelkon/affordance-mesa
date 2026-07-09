# EV Adoption Extension Coding Brief

> **Status (July 2026): implemented and superseded.** This brief guided the
> first version of the EV extension. The model has since grown well beyond it
> (fixed home locations, scenario presets, probabilistic adoption, demand-driven
> expansion, congestion, supply limits, price learning, social diffusion, and a
> calibration workflow). For the current model, read `EV_MODEL_DESCRIPTION.md`;
> the Main Rule below still applies to all future work.

This brief describes how to extend the Mesa affordance model toward EV adoption
without changing the conceptual logic of the original affordance-landscape port.

## Main Rule

Do not modify the original affordance model first. Keep
`affordance_mesa/model.py` and `affordance_mesa/agents.py` conceptually intact.
The EV model should be added as an extension layer using subclasses.

Useful background on inheritance:

- Official Python tutorial: https://docs.python.org/3/tutorial/classes.html#inheritance
- Practical guide: https://realpython.com/inheritance-composition-python/

## New Files

Create these files:

```text
affordance_mesa/ev_model.py
affordance_mesa/ev_agents.py
affordance_mesa/ev_costs.py
tests/test_ev_model.py
```

Do not put all EV logic into the existing `model.py`.

## Step 1: Add An EV Agent Subclass

In `ev_agents.py`, create an `EVConsumerAgent` class that inherits from
`ConsumerAgent`.

It should keep the existing `pro_env`, `non_env`, movement, learning, and
social-learning behavior.

Add EV-specific attributes:

```text
income
annual_mileage
vehicle_age
replacement_interval
home_charging_access
environmental_concern
price_sensitivity
range_anxiety
peer_sensitivity
ev_adopted
last_adoption_score
```

Do not rewrite `behave()` initially. Instead, override `step()` conceptually
like this:

```python
def step(self):
    super().step()
    self.vehicle_age += 1

    if self.vehicle_age >= self.replacement_interval and not self.ev_adopted:
        self.consider_ev_adoption()
```

The `super().step()` call means: first run the parent class behavior, then add
the EV-specific behavior.

## Step 2: Add Cost Logic Separately

In `ev_costs.py`, define small pure functions:

```python
def ev_tco(...):
    ...

def ice_tco(...):
    ...

def economic_score(ev_tco, ice_tco):
    ...
```

Keep this file independent from Mesa so it is easy to test.

A simple first formula is:

```python
economic_score = (ice_tco - ev_tco) / ice_tco
```

Positive means EV is economically attractive.

## Step 3: Add An EV Model Subclass

In `ev_model.py`, create an `EVAdoptionModel` class that inherits from
`AffordanceLandscapeModel`.

This class should:

1. Use `EVConsumerAgent` instead of `ConsumerAgent`.
2. Add a second spatial layer:

```python
self.charging_access = np.zeros((width, height), dtype=float)
```

3. Add EV policy/scenario parameters:

```text
subsidy
fuel_price
electricity_price
charger_expansion_rate
adoption_threshold
```

4. Track EV outcomes:

```text
ev_adoption_count
ev_adoption_share
mean_adoption_score
mean_charging_access
mean_tco_gap
```

## Step 4: Keep The Adoption Rule Simple

The first adoption rule should be transparent:

```python
adoption_score = (
    economic_weight * economic_score
    + charging_weight * charging_score
    + environmental_weight * environmental_concern
    + peer_weight * peer_adoption_share
    - range_anxiety_weight * range_anxiety
)
```

Then:

```python
if adoption_score >= adoption_threshold:
    ev_adopted = True
```

Do not add discrete choice, utility noise, or calibration yet. First make the
deterministic mechanism work.

## Step 5: Use The Existing Network Code

Peer influence should reuse the existing network:

```python
neighbours = self.model.network_neighbours(self)
peer_adoption_share = adopted_neighbours / total_neighbours
```

No new network implementation is needed.

## Step 6: Add Tests Before UI

In `tests/test_ev_model.py`, add tests for:

```text
EV model runs for 10 steps.
EV adoption share stays between 0 and 1.
Higher subsidy does not reduce adoption under the same seed.
Higher charging access does not reduce adoption under the same seed.
Base AffordanceLandscapeModel still runs unchanged.
```

These tests matter more than UI controls at first.

## Step 7: Only Then Update Solara

After the model works, add a separate EV dashboard or an EV mode toggle. Do not
overload the current Solara controls immediately.

Suggested first EV controls:

```text
Scenario: baseline / subsidy / infrastructure / combined
Subsidy
Fuel price
Electricity price
Charging coverage
Adoption threshold
```

Suggested EV plots:

```text
EV adoption share over time
Mean adoption score
Mean TCO gap
Mean charging access
```

## Implementation Order

1. `ev_costs.py`
2. `EVConsumerAgent`
3. `EVAdoptionModel`
4. `tests/test_ev_model.py`
5. Command-line runner, for example `scripts/run_ev_model.py`
6. Solara UI extension

The key design principle is this: the current model remains the abstract
affordance landscape. The EV model is a subclassed application of that logic to
charging, cost, peer effects, and vehicle replacement.
