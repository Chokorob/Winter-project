"""Run the Model - Ep.1 sensitivity check (CLAUDE.md rule 2).

The three guesses the voice names - meat per reindeer, how often hunters get hurt, how many animals a territory holds -
are each moved by -30% and +30% while everything else stays put. For each variant the full group-size "hill"
(sharing on, 5/10/25/50/100/200) is re-run with the same seed and run count as winter.py.
The video promises the shape, not the numbers; this file says whether the shape holds:
  peak at a few dozen people (25 or 50), collapse at 200 below families alone, peak above them.
A finer sweep over meat per reindeer (the guess the shape depends on) gives the threshold.
Writes data/ep01_sensitivity.json.   Usage: python sensitivity.py [runs]
"""
import json, sys
import numpy as np
import winter

R = int(sys.argv[1]) if len(sys.argv) > 1 else 100
SIZES = [5, 10, 25, 50, 100, 200]
KNOBS = {"KILL_KCAL": "meat per reindeer", "INJURY": "hunter injury per day", "G0_PER_TERRITORY": "animals per territory"}


def hill():
    out = []
    for band in SIZES:
        rng = np.random.default_rng(1)
        surv = np.array([winter.run(band, True, rng, injury=winter.INJURY)[0] for _ in range(R)])  # injury is a default arg: pass it
        out.append(dict(band=band, mean=float(surv.mean()), p10=float(np.percentile(surv, 10)), p90=float(np.percentile(surv, 90))))
    return out


def families():
    rng = np.random.default_rng(1)
    return float(np.mean([winter.run(5, False, rng, injury=winter.INJURY)[0] for _ in range(R)]))


def shape_holds(means, fam):
    return SIZES[int(np.argmax(means))] in (25, 50) and means[-1] < fam < max(means)


variants = [dict(knob=None, factor=1.0, label="as in the video")]
variants += [dict(knob=k, factor=f, label=f"{KNOBS[k]} {'-' if f < 1 else '+'}30%") for k in KNOBS for f in (0.7, 1.3)]
results = []
for v in variants:
    base = {k: getattr(winter, k) for k in KNOBS}
    if v["knob"]:
        setattr(winter, v["knob"], type(base[v["knob"]])(base[v["knob"]] * v["factor"]))
    h = hill()
    fam = families()
    for k, val in base.items():
        setattr(winter, k, val)
    means = [p["mean"] for p in h]
    peak = SIZES[int(np.argmax(means))]
    shape_ok = shape_holds(means, fam)
    results.append(dict(**v, hill=h, families=fam, peak=peak, shape_holds=bool(shape_ok)))
    print(f"{v['label']:32s} peak {peak:4d}  " + "  ".join(f"{p['band']}:{p['mean']:.0f}" for p in h) + f"  families {fam:.0f}  shape {'OK' if shape_ok else 'CHANGED'}")

# meat sweep: reuse the -30% / base / +30% runs, add -20% and -10%
sweep = {round(winter.KILL_KCAL * v["factor"]): v for v in results if v["knob"] in (None, "KILL_KCAL")}
base_kcal = winter.KILL_KCAL
for f in (0.8, 0.9):
    winter.KILL_KCAL = int(base_kcal * f)
    h = hill(); fam = families()
    means = [p["mean"] for p in h]
    sweep[winter.KILL_KCAL] = dict(hill=h, families=fam, peak=SIZES[int(np.argmax(means))], shape_holds=bool(shape_holds(means, fam)))
winter.KILL_KCAL = base_kcal
meat = [dict(kcal=k, peak=v["peak"], shape_holds=v["shape_holds"], hill=v["hill"], families=v["families"]) for k, v in sorted(sweep.items())]
holds = [m["kcal"] for m in meat if m["shape_holds"]]
breaks_below = [m["kcal"] for m in meat if not m["shape_holds"] and m["kcal"] < min(holds)]
threshold = dict(holds_from=min(holds), breaks_at=max(breaks_below) if breaks_below else None, model=base_kcal)
for m in meat:
    print(f"meat {m['kcal']:6d}: peak {m['peak']:3d}  shape {'OK' if m['shape_holds'] else 'CHANGED'}")
print("threshold", threshold)
json.dump(dict(runs=R, sizes=SIZES, variants=results, meat_sweep=meat, meat_threshold=threshold), open("data/ep01_sensitivity.json", "w"))
