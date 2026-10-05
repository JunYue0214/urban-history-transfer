# Gate 2 validation amendment and decision rules (execution 1005-9)

Filed BEFORE any Gate 2 model was run and before any thermal-response value
(`Annual_nig`, `Summer_day`) was joined to the analysis table. Historical
artifacts (1005-1 … 1005-8) are not edited; this file supplements them.

## A. Validation amendment (from the PI prompt)

* PRIMARY validation: spatially blocked 5-fold CV using the locked 10-degree
  tile design from 1005-8 (`gate2_support.tile_ids` + `balanced_group_folds`,
  k=5, applied to the cluster-level latitude/longitude).
* SECONDARY geographic robustness: leave-major-region-out for Asia, Africa,
  Europe, North America, South America. Oceania (N=21) is NOT merged with Asia,
  is reported descriptively only, and is never counted as evidence of
  cross-region reproduction. Oceania units are used as training rows when
  another region is held out (they are never relabelled); when Oceania is held
  out, the five other regions are the training set.
* The 1005-8 "merge Oceania into Asia for validation" device is not used.

## B. Counting rule adapted to five adequate regions

1005-6 required Delta R2 > 0 in at least 4 of 6 regions and treated
"negative in >= 4 regions" as evidence against. With Oceania excluded from
replication counting, the count is retained and the denominator reduced
(stricter, not looser): FOR requires Delta R2 > 0 in **>= 4 of 5** adequate
regions; AGAINST if Delta R2 < 0 in **>= 3 of 5**; 3 positive of 5 is mixed.

## C. Fixed decision rules (1005-6 thresholds unchanged)

Primary effect = pooled out-of-fold Delta R2 (M1 minus M0), random forest with
fixed hyperparameters (500 trees, min_samples_leaf=5, max_features=0.5,
seed 42), S3+C1, fixed-boundary 9-vector H, spatial 5-fold.

STRONG FOR requires ALL of:
1. Delta R2 >= +0.02 with the 95% spatial-block bootstrap CI excluding 0;
2. observed Delta above the 95th percentile of the shuffled-H null
   (300 permutations, seed 42, within region x size-tercile strata);
3. positive in >= 4 of 5 adequate regions;
4. Delta with S-derived pseudo-history < 80% of the observed Delta (so at least
   20% of the observed gain is not reproducible from S+C), and the redundant
   S-feature pseudo-history Delta below the observed Delta;
5. under C2 the Delta keeps its sign and >= 50% of its size, and the same under
   strict-precedence H<=2000 (see E);
6. Experiment 3: Delta RMSE_transfer < 0 and below the 5th percentile of the
   shuffled-H transfer null; Experiment 2: partial Spearman rho >= 0.05 with
   stratified-permutation p < 0.01.

AGAINST if ANY of: Delta R2 < 0.005 with the CI including 0; observed Delta
within the shuffled null (<= 95th percentile); pseudo-history Delta >= 80% of
the observed Delta; Delta < 0 in >= 3 of 5 regions; Delta collapsing under C2
(< 50% of the primary or sign change); Exp 2 rho <= 0.02 AND Exp 3 within null.

GATE 2 = PASS if all STRONG-FOR criteria hold; FAIL if the primary AGAINST
conditions hold (negligible gain, within null, or explained by pseudo-history);
MIXED for anything in between (channel-, region-, window-, model- or
specification-dependent); UNRESOLVED only for technical failure. The
thresholds are guidance, applied as written, and not changed after seeing R.

TRANSFERABILITY PROGRAM: CONTINUE if PASS, REVISE if MIXED, STOP if FAIL.

## D. Labels for the headline items (declared in advance)

* Strict-precedence (primary Delta = D1, H<=2000 Delta = D2, bootstrap CI for D2):
  SURVIVES if D2 >= max(0.005, 0.5*D1) with CI excluding 0; DISAPPEARS if
  D2 < 0.005 or the CI includes 0; otherwise WEAKENS. If D1 itself is < 0.005
  the label is DISAPPEARS (nothing to survive).
* Secondary Summer_day: an effect is "present" if Delta R2 >= 0.005 with the CI
  excluding 0. CONCORDANT = present for both responses; NULL = present for
  neither; DISCORDANT = present for exactly one.
* Ridge "supports the same qualitative conclusion" if its Delta R2 has the
  same sign and the CI excludes 0 in the same direction as the random forest.

## E. Temporal-precedence specifications

R is the 2003-2018 composite and overlaps H epochs 2005-2015.
* H_pre2000: B(t)/B(2000) for t in {1975,...,1995} (5 columns); no column built
  from a post-2000 epoch. Run with S3(2020) (primary strict test) and with
  S3(2000) (fully past-state variant); the first is the headline.
* T=2015: S at 2015 and H = B(t)/B(2015), t in {1975,...,2010} (8 columns).
Signals that exist only with the overlapping H are called "recent-development
association", never "historical legacy".

## F. Other fixed choices

* M0 and M1 are always compared on identical rows and identical folds.
* H representations: standardized raw 9-vector (primary); a PCA(3) variant fit
  on training-fold H only; four interpretable scalar descriptors.
* Tuning: none for the random forest; ridge uses `RidgeCV` (efficient
  leave-one-out inside each training fold only).
* Bootstrap: 2,000 resamples of 10-degree tiles with replacement, applied to
  stored out-of-fold predictions (this reflects evaluation-sample dependence
  and does not re-fit models; stated as a limitation).
* Twins: mutual k=10 nearest neighbours in the block-balanced standardized
  S3+C1 space, minimum separation 200 km, built from S/C only. D_H tertile cut
  points are taken from the pair D_H distribution (not D_R). Statistic =
  partial Spearman of D_R and D_H given D_SC and D_geo; inference via
  stratified (region x size tercile) permutation of unit-level H (1,000) and a
  tile-block bootstrap with pair weights.
* Transfer: K=10 inverse-distance-weighted donor mean, donors from training
  folds only, feature blocks z-scored on the training fold and rescaled to
  equal total variance per block.
* Moran's I on out-of-fold residuals (k-nearest-neighbour weights, k=8 and 20).
* The secondary response is analysed only after every primary output file has
  been written (enforced by a completion marker with file hashes).

## G. Disclosed defect in the 1005-8 common-support / twin-feasibility code

1005-8 computed `log(clip(density, lower=1))` for the S3 block. Cluster density
is 0.004-0.156 people per m2, so this column was constant (0) and was
effectively dropped from the Mahalanobis distance and from the twin-feasibility
block (the Mahalanobis feature block therefore had 8 effective dimensions instead of 9:
4 S3 columns + 5 C1 columns, one of them constant; the twin-feasibility S block had 3 of 4;
the reported 95th-percentile distance 4.53
and the feasibility pair counts come from that implementation). The design text
in 1005-8 specifies log(density). Resolution, fixed here before R is used:
* Primary common-support flag = the specification as written
  (true log density), S/C-only, own 95th percentile.
* The as-implemented 1005-8 flag is reproduced (checking that its threshold is
  4.53) and run as a second sensitivity.
* Twins and transfer use the correct S3 (including log density).
Neither flag uses R or model residuals. 1005-8 files are not edited.

## H. Clarification of the decision mapping (written before any R was joined)

"AGAINST if ANY of" in section C lists evidence flags. The GATE 2 label is
computed as follows, exactly and mechanically:

* FAIL if any of: (i) Delta R2 < 0.005 with the CI including 0; (ii) observed
  Delta not above the 95th percentile of the shuffled-H null; (iii) the
  S-derived pseudo-history Delta >= 80% of a positive observed Delta;
  (iv) twin rho <= 0.02 AND the transfer contrast inside its shuffled null.
* PASS only if every STRONG-FOR criterion (1-6) holds.
* Otherwise MIXED. Regional sign failures (>= 3 of 5 negative), C2 collapse and
  strict-precedence failure each prevent PASS and are reported as AGAINST
  flags, but do not by themselves produce FAIL.
* UNRESOLVED only if a required computation fails technically.
