# Run the Model, Ep. 1: 1,000 Ice Age humans, one winter

This is the code behind the video *We Simulated 1,000 Ice Age Humans Surviving One Winter*.

1,000 people live through a 150-day winter, simulated one day at a time. Each person needs energy every day. Food comes from small game and stores (reliable, but it shrinks as winter goes on) and from big game (a gamble). When a person's body fat runs out, they die. The only thing we change between setups is how people live together: the size of a camp, and whether its families pool their food.

## Run it

```bash
pip install -r requirements.txt
python winter.py 100        # 100 runs per setup -> data/ep01_results.json
python sensitivity.py 100   # the ±30% check -> data/ep01_sensitivity.json
```

Run both from the repository root. The seed is fixed, so you should get exactly the numbers below.

## What it finds

Mean survivors out of 1,000 after 150 days, over 100 runs:

| Setup | Survivors |
|---|---|
| Families of 5, no sharing | 798 |
| Sharing camps of 10 / 25 / 50 / 100 / 200 | 853 / **906** / 868 / 573 / 283 |
| Camps of 25, no sharing | 753 |
| Families of 5, no hunter ever hurt | 905 |

## The rules, and which are guesses

All parameters are at the top of `winter.py`.

| Parameter | Value | Basis |
|---|---|---|
| Energy need | 3,200 kcal/person/day (average incl. children) | Adults 3,360–4,480 (Steegmann et al., 2002) |
| Hunters | 1 per family of 5 | Assumption |
| Hunt success | 8% per hunter per day at full game | Assumption; most Hadza big-game hunts fail (Gurven et al., 2015) |
| Meat per reindeer | 70,000 kcal | **Assumption**, see below |
| Small game, fish, stores | 2,200 → 1,200 kcal/person/day over winter | Assumption |
| Autumn stores | 15 days of need | Assumption |
| Body fat | 50,000–110,000 kcal | Assumption |
| Hunter injury | 0.15% per day, no hunting until spring | Assumption |
| Animals per territory | 250. Below 35% the camp moves (3 days, no hunting, ×1.2 need), up to 3 times | Assumption |
| Sharing | On: one pot per camp. Off: one pot per family of 5 | Ache: over 90% of a family's food from others (Kaplan et al., 2012) |

## What the model doesn't know

This is a toy model. `sensitivity.py` moves the three biggest guesses (meat per reindeer, injury rate, animals per territory) by ±30% and checks whether the *shape* survives. The shape is: the best camp holds a few dozen people (25–50), and camps of 200 do worse than families alone.

- The shape holds in 6 of 7 variants.
- It breaks if a reindeer gives less meat. It holds from about 63,000 kcal per animal. At 56,000 the peak shrinks to camps of 10. At 49,000 there is no sweet spot at all.
- A rough real-world range: lean caribou meat is 127 kcal per 100 g (USDA FDC 173853). Winter body weight is about 85 kg for females and 109 kg for males. Depending on which animals were hunted, that puts a reindeer anywhere between roughly 54,000 and 99,000 kcal. The edible-meat fraction we used for this range (~50% of live weight) is itself an unsourced assumption.

So read the numbers as illustrations of a mechanism, not as history.

## Sources

- Steegmann, Cerny & Holliday (2002). Neandertal cold adaptation. https://pubmed.ncbi.nlm.nih.gov/12203812/
- Froehle & Churchill (2009). Energetic competition between Neandertals and anatomically modern humans. https://works.bepress.com/andrew-froehle/42
- Marlowe (2005), as tabulated in Smith et al. (2010). Forager camp sizes, median 27. https://pmc.ncbi.nlm.nih.gov/articles/PMC2999363
- Gurven et al. (2015). Hadza hunting. https://www.gurven.anth.ucsb.edu/sites/secure.lsit.ucsb.edu.anth.d7_gurven/files/sitefiles/papers/gurvenetal2015he.pdf
- Kaplan et al. (2012). Ache food sharing. https://pmc.ncbi.nlm.nih.gov/articles/PMC3385467
- Gurven (2004). Sharing as risk reduction. https://gurven.anth.ucsb.edu/sites/secure.lsit.ucsb.edu.anth.d7_gurven/files/sitefiles/papers/gurvenBES2004.pdf

Break it, change the numbers, and tell us what you find.

## License

MIT, see `LICENSE`.
