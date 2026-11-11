"""Run the Model — Ep.1 toy model: 1,000 Ice Age foragers, one 150-day winter.
All parameters are labelled assumptions; sourced ones noted in the doc."""
import numpy as np

DAYS = 150
N = 1000
NEED = 3200            # kcal/person/day, avg incl. children (assumption; adults 3,360-4,480 per Steegmann 2002)
HUNTER_FRAC = 0.2      # one hunter per family of 5 (hunters sit on every 5th seat, see run())
P_KILL = 0.08          # daily success per hunter at full game density (Hadza big game ~4%/hunt)
KILL_KCAL = 70000      # edible kcal per reindeer-sized kill (assumption)
SMALL_START, SMALL_END = 2200, 1200   # kcal/person/day from small game, fish, stores, declining (assumption)
STORE_DAYS = 15        # autumn stores, days of need
FAT_LO, FAT_HI = 50000, 110000      # usable body reserves kcal (assumption ~6.5-14 kg fat)
INJURY = 0.0015        # hunter daily chance of injury -> stops hunting for winter
G0_PER_TERRITORY = 250 # big animals reachable per band territory (assumption)
MAX_MOVES = 3

def run(band, share, rng, injury=INJURY, trace=False):
    """trace=True also returns per-agent injury day and daily fat (for the video's close-ups); RNG use is identical either way."""
    nb = N // band
    hunters = max(1, round(band * HUNTER_FRAC))
    fam = 5
    # people arrays [nb, band]
    fat = rng.uniform(FAT_LO, FAT_HI, (nb, band))
    alive = np.ones((nb, band), bool)
    # food pots: if share -> one pot per band; else one pot per family of 5
    nf = band // fam if not share else 1
    unit = band // nf
    pot = np.full((nb, nf), STORE_DAYS * NEED * unit, float)
    hunter_ok = np.zeros((nb, band), bool)
    # hunter i belongs to family i*fam//... : put hunters spread one per family first
    idx = np.arange(band)
    hunter_slots = (idx % fam == 0) if band >= fam else idx == 0
    hunter_slots &= np.cumsum(hunter_slots) <= hunters
    hunter_ok[:] = hunter_slots
    game = np.full(nb, float(G0_PER_TERRITORY))
    moves = np.zeros(nb, int)
    moving = np.zeros(nb, int)
    deaths_day = np.zeros(DAYS)
    injury_day = np.full((nb, band), -1)
    fat_hist = np.zeros((DAYS, nb * band)) if trace else None
    pot_hist = np.zeros((DAYS, nb)) if trace else None  # food left in each band's pots after eating, summed per band
    kill_hist = np.zeros((DAYS, nb * band), bool) if trace else None  # who brought in big game, day by day
    game_hist = np.zeros((DAYS, nb)) if trace else None  # animals left in each band's territory at day's end (before any move)
    move_hist = np.zeros((DAYS, nb), bool) if trace else None  # the band packs up and moves on this day
    death_day = np.full((nb, band), -1)  # per-agent day of death, -1 = survived (for the video)
    for d in range(DAYS):
        small = SMALL_START + (SMALL_END - SMALL_START) * d / DAYS
        dens = game / G0_PER_TERRITORY
        active = hunter_ok & alive & (moving[:, None] == 0)
        kills = rng.random((nb, band)) < P_KILL * dens[:, None]
        kills &= active
        game -= kills.sum(1)
        game = np.maximum(game, 0)
        # injuries
        was_ok = hunter_ok.copy()
        hunter_ok &= ~(rng.random((nb, band)) < injury)
        injury_day[was_ok & ~hunter_ok] = d + 1
        # income to pots
        unit_of = (idx // unit).clip(max=nf - 1)
        for u in range(nf):
            m = unit_of == u
            pot[:, u] += kills[:, m].sum(1) * KILL_KCAL
            pot[:, u] += (alive[:, m].sum(1)) * small * (0.5 if False else 1.0) * (moving == 0)
        # eat: each unit splits pot among living members up to NEED
        need_mult = np.where(moving > 0, 1.2, 1.0)
        for u in range(nf):
            m = unit_of == u
            n_alive = alive[:, m].sum(1)
            want = n_alive * NEED * need_mult
            eat = np.minimum(pot[:, u], want)
            pot[:, u] -= eat
            per = np.where(n_alive > 0, eat / np.maximum(n_alive, 1), 0)
            deficit = NEED * need_mult - per
            fat[:, m] -= deficit[:, None] * alive[:, m]
        fat = np.minimum(fat, FAT_HI)
        if trace:
            fat_hist[d] = np.maximum(fat, 0).ravel()
            pot_hist[d] = pot.sum(1)
            kill_hist[d] = kills.ravel()
        died = alive & (fat <= 0)
        deaths_day[d] = died.sum()
        death_day[died] = d + 1
        alive &= ~died
        # camp move when game thin
        moving = np.maximum(moving - 1, 0)
        go = (dens < 0.35) & (moves < MAX_MOVES) & (moving == 0)
        if trace:
            game_hist[d] = game
            move_hist[d] = go
        moves += go
        moving[go] = 3
        game[go] = G0_PER_TERRITORY * 0.8
    if trace:
        return alive.sum(), deaths_day, death_day.ravel(), injury_day.ravel(), fat_hist, pot_hist, kill_hist, game_hist, move_hist
    return alive.sum(), deaths_day, death_day.ravel()

if __name__ == "__main__":
    import json, sys
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    out = {}
    for share in (False, True):
        for band in (5, 10, 25, 50, 100, 200):
            if not share and band != 5 and band not in (25, 100):
                continue
            rng = np.random.default_rng(1)
            surv = []; dd = np.zeros(DAYS); traces = []
            for r in range(R):
                s, d, t = run(band, share, rng); surv.append(s); dd += d; traces.append(t)
            surv = np.array(surv)
            half = None
            key = f"band{band}_{'share' if share else 'family'}"
            out[key] = dict(mean=float(surv.mean()), p10=float(np.percentile(surv,10)),
                            p90=float(np.percentile(surv,90)), min=int(surv.min()), max=int(surv.max()),
                            deaths_by_day=(dd/R).round(2).tolist(),
                            # the run closest to the mean, agent by agent: agent i lives in camp i // band
                            example_run_index=int(np.argmin(np.abs(surv - surv.mean()))) + 1,
                            example_run=traces[int(np.argmin(np.abs(surv - surv.mean())))].tolist(),
                            runs_survivors=surv.tolist(),
                            # 5 runs spread from worst to best (sorted-survivor quantiles 0, .25, .5, .75, 1), for the run-flash montage
                            spread_runs=[dict(index=int(i) + 1, survivors=int(surv[i]), trace=traces[i].tolist())
                                         for i in sorted(np.argsort(surv, kind='stable')[np.linspace(0, R - 1, 5).round().astype(int)])])
            print(key, round(surv.mean()), np.percentile(surv,[10,90]), surv.min(), surv.max())
    # Ep.1 Run 1 close-up: replay the families example run with tracing (same seed, same draws) and pick the hunter
    # injured closest to day 40 (the script's "Day forty"); whatever happens to that family is what the video shows.
    fam = out["band5_family"]; rng = np.random.default_rng(1)
    for _ in range(fam["example_run_index"]):
        s, _, dd, inj, fat, pots, *_ = run(5, False, rng, trace=True)
    assert dd.tolist() == fam["example_run"]
    cands = np.where((np.arange(N) % 5 == 0) & (inj > 0))[0]
    h = int(min(cands, key=lambda i: abs(inj[i] - 40)))
    fam["injury_day"] = inj.tolist()
    fam["pots"] = (pots.T / 100).round().astype(int).tolist()  # per family, per day, hundreds of kcal
    # the same winter with injuries switched off: identical random draws, so the difference is exactly what injuries cost here
    rng = np.random.default_rng(1)
    for _ in range(fam["example_run_index"] - 1):
        run(5, False, rng)
    fam["example_run_noinjury"] = run(5, False, rng, injury=0)[2].tolist()
    fam["story"] = dict(hunter=h, injury_day=int(inj[h]), family=list(range(h, h + 5)),
                        fat=fat[:, h:h + 5].T.round(-2).astype(int).tolist())  # kcal per day, rounded to 100
    # Ep.1 Run 2 close-up ("Same twisted ankle"): replay the groups-of-25 sharing example run and pick the hunter injured
    # closest to the Run 1 story's injury day; export his camp's kills (who fed the shared pot, when), pot and his family's fat.
    g = out["band25_share"]; rng = np.random.default_rng(1)
    for _ in range(g["example_run_index"]):
        s2, _, dd2, inj2, fat2, pots2, kills2, *_ = run(25, True, rng, trace=True)
    assert dd2.tolist() == g["example_run"]
    hs = np.where((np.arange(N) % 5 == 0) & (inj2 > 0))[0]
    h2 = int(min(hs, key=lambda i: (abs(inj2[i] - inj[h]), i)))
    camp = h2 // 25; members = np.arange(camp * 25, camp * 25 + 25)
    kd, ka = np.nonzero(kills2[:, members])
    g["injury_day"] = inj2.tolist()
    g["story"] = dict(hunter=h2, camp=int(camp), injury_day=int(inj2[h2]), family=list(range(h2, h2 + 5)),
                      hunters=[int(i) for i in members if i % 5 == 0],
                      kills=[[int(d) + 1, int(members[a])] for d, a in zip(kd, ka)],  # [day, agent]
                      pot=(pots2[:, camp] / 100).round().astype(int).tolist(),
                      fat=fat2[:, h2:h2 + 5].T.round(-2).astype(int).tolist())
    print("run2 story hunter", h2, "camp", camp, "injured day", inj2[h2], "camp kills", len(kd), "family deaths", dd2[h2:h2 + 5].tolist())
    # Ep.1 Run 3 (camps of 200): how fast each camp eats its territory and when it has to move
    b = out["band200_share"]; rng = np.random.default_rng(1)
    for _ in range(b["example_run_index"]):
        s3, _, dd3, *_, game3, move3 = run(200, True, rng, trace=True)
    assert dd3.tolist() == b["example_run"]
    b["game"] = game3.T.round().astype(int).tolist()  # per camp, per day
    b["moves"] = [[int(d) + 1 for d in np.nonzero(move3[:, c])[0]] for c in range(move3.shape[1])]  # move days per camp
    print("run3 move days per camp", b["moves"])
    # "if no hunter ever got hurt": families of 5, injury chance 0
    rng = np.random.default_rng(1)
    s0 = np.array([run(5, False, rng, injury=0)[0] for _ in range(R)])
    out["band5_family_noinjury"] = dict(mean=float(s0.mean()), p10=float(np.percentile(s0, 10)), p90=float(np.percentile(s0, 90)))
    print("story hunter", h, "injured day", inj[h], "| no-injury mean", s0.mean())
    out["params"] = dict(DAYS=DAYS, N=N, NEED=NEED, HUNTER_FRAC=HUNTER_FRAC, P_KILL=P_KILL, KILL_KCAL=KILL_KCAL,
                         INJURY=INJURY, G0_PER_TERRITORY=G0_PER_TERRITORY, RUNS=R,
                         SMALL_START=SMALL_START, SMALL_END=SMALL_END, STORE_DAYS=STORE_DAYS, FAT_LO=FAT_LO, FAT_HI=FAT_HI)
    import os; os.makedirs("data", exist_ok=True)
    json.dump(out, open("data/ep01_results.json", "w"))
