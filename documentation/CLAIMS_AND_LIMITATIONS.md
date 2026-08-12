# Claims and Limitations

## Claims the paper can make

### 1. A positive differential absence pattern exists under the original advance-TV definition
With player and team-season fixed effects, full controls, and player+game clustered standard errors, the focal DDD is **+3.15 percentage points** (95% CI **+0.57 to +5.73**, p = **0.0167**).

The estimand is: after the PPP, the star-relative change in new-absence-onset probability was 3.15 pp larger in advance-announced national-TV games than in non-national-TV games.

This is a statement about a difference-in-difference-in-differences, not a raw star absence rate.

### 2. The pattern is not obviously driven by a single season, player trend, or conventional clustering choice
Legacy-TV leave-one-season-out estimates remain positive; player-specific linear trends yield **+3.26 pp** (p = **0.0136**); and the legacy estimate remains conventionally significant across the tested clustering structures.

The joint pre-trend test does not reject (p ≈ **0.433**), and fake pre-policy PPP dates are not significant.

These are supportive diagnostics, not proof of causal identification.

### 3. The result is measurement-sensitive
Using a harmonized national-TV definition, the preferred latest-pre-tip estimate falls to **+1.77 pp** (95% CI **-0.80 to +4.35**, p = **0.177**).

Using cadence-harmonized injury-report snapshots, the legacy-TV estimate is **+2.63 pp** (p = **0.046**), while using both harmonized TV and harmonized report timing gives **+1.24 pp** (p = **0.347**).

Therefore the paper should foreground **measurement sensitivity** rather than treat +3.15 pp as invariant.

### 4. The current data do not support a vague-injury relabeling mechanism
Conditional on a new injury-labeled onset, the vague-versus-specific DDD is **-8.42 pp** (95% CI **-23.96 to +7.12**, p = **0.288**). The player + team-season FE version is **-7.18 pp** (p = **0.387**).

Nonlinear checks also remain negative, and the multinomial decomposition does not show a distinctive shift into vague rather than specific injuries.

### 5. No predeclared subgroup has robust heterogeneity
Back-to-back status, weak-opponent status, recent workload, and proximity to the 65-game threshold show no statistically detectable DDD heterogeneity after BH correction.

### 6. The explicit-rest category result is a sparse-cell diagnostic, not a substantive star-TV increase
The explicit-rest category has a positive adjusted category coefficient, but the focal star-national-TV cells contain essentially no explicit-rest onsets: **0 before PPP and 1 after PPP**. The coefficient arises from relative changes in comparison cells and should not be interpreted as stars increasingly resting explicitly on national TV.

## Claims the paper should NOT make

- **Do not claim the PPP caused star absences to increase.** National-TV exposure is observational, policy timing is not randomized, and the estimate is sensitive to measurement definitions.
- **Do not claim teams disguised load management as vague injuries.** The vague-versus-specific mechanism test is null and points in the opposite direction.
- **Do not claim the effect is concentrated on back-to-backs, weak opponents, high workload, or near 65 games.** The heterogeneity tests do not support those subgroup claims.
- **Do not claim explicit rest increased in the focal star-TV cell.** The raw counts are approximately zero.
- **Do not describe the taxonomy validation as independent external human double-coding.** See the validation provenance note.
- **Do not present the randomization-style permutation p-value as an exact Fisher randomization test.** National-TV assignment was never random.

## Most defensible high-level conclusion

> Across six NBA regular seasons, the original advance-national-TV specification shows a positive post-PPP differential in new star absence onsets, but the magnitude and statistical precision are sensitive to how national-TV exposure and injury-report timing are harmonized. The data do not provide evidence that the observed absence pattern operated through a shift from specific to vague injury wording. The results therefore support a cautious claim about differential absence behavior, not a causal claim of disguised load management.
