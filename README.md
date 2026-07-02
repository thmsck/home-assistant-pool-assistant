# Pool Assistant for Home Assistant

Pool Assistant calculates active chlorine speciation from existing pool water
measurement entities.

The integration is intended as an assistant, not as a blind pool controller. It
uses measured values from integrations such as PoolLab and creates a separate
calculated device with chemistry-model sensors.

## Model

The chemistry model is based on the O'Brien/USEPA free chlorine and cyanuric
acid equilibrium model documented by the USEPA simulator:

- Known inputs: pH, free chlorine, total chlorine, cyanuric acid, alkalinity,
  optional temperature, pool volume
- Calculated outputs: HOCl, OCl-, unbound chlorine, CYA-bound chlorine and
  chlorine/cyanurate species percentages
- Additional checks: bound chlorine, measurement age and measurement
  synchronization status

The cyanuric-acid equilibrium constants are the O'Brien/USEPA constants for
25 °C. The HOCl/OCl pKa is temperature-adjusted.

See `docs/pool-water-chemistry.md` for the chemistry background, working
thresholds and assessment rationale.

## Sensors

The integration creates these sensors:

- `Aktives Chlor HOCl`
- `Hypochlorit OCl`
- `Gebundenes Chlor`
- `Ungebundenes Chlor`
- `An CYA gebundenes Chlor`
- `Chlor-Spezies`
- `Desinfektionsstatus`
- `Messalter`
- `Messstatus`
- `Belastungsstatus`
- `Algenrisiko`
- `Poolchemie-Index`
- `Poolstatus`

## Configuration

Add the integration from Home Assistant's UI and select:

- name
- pool volume in m³
- pH sensor
- free chlorine sensor
- total chlorine sensor
- cyanuric acid sensor
- alkalinity sensor
- temperature sensor, optional. If omitted, `25 °C` is used.

Example source entities:

- `sensor.out_garden_meter_pool_water_ph`
- `sensor.out_garden_meter_pool_water_free_chlorine`
- `sensor.out_garden_meter_pool_water_total_chlorine`
- `sensor.out_garden_meter_pool_water_cyanuric_acid`
- `sensor.out_garden_meter_pool_water_total_alkalinity`

## Validation case

Reference case from PoolLab screenshots:

- pH: `6.9`
- free chlorine: `3.0 mg/l`
- CYA: `140 mg/l`
- temperature: `26 °C`

Expected output:

- HOCl: about `0.0126 mg/l`
- unbound chlorine: about `0.52 %`
- CYA-bound chlorine: about `99.48 %`

## HACS

This repository is structured for HACS as a custom integration repository.

```text
custom_components/pool_assistant
hacs.json
```

During development, copy or symlink `custom_components/pool_assistant` into your
Home Assistant `custom_components` directory and restart Home Assistant.

For local SSHFS-based Home Assistant config mounts, use:

```bash
scripts/deploy-local.sh ../ha-config
```

## Development

Run tests:

```bash
python3 -m pytest
```

Validate Python syntax:

```bash
python3 -m py_compile custom_components/pool_assistant/*.py
```
