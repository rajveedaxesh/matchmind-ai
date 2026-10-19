# MatchMind AI - Evaluation report (synthetic data)

Generated 2026-10-19T06:48:39+00:00 by `scripts/evaluate.py` in 3.8s. Seed 42.

> All jobs, candidates and relevance labels are synthetic and rule-generated. Results show how the pipeline works, not real hiring accuracy.

**Dataset:** 32 jobs x 122 candidates (18 hand-written + 104 generated), 3904 labelled pairs. Grade distribution: {'0': 3013, '1': 535, '2': 125, '3': 231}.

**Labels:** grade = 0.35*role_family_match (1 same, 0.5 adjacent, 0 otherwise) + 0.50*true_required_skill_coverage + 0.15*experience_in_loose_range + Gaussian noise (sd 0.05); grade 3 if >= 0.80, 2 if >= 0.62, 1 if >= 0.40, else 0. Relevant (for Precision/Recall/MRR) means grade >= 2.

## Recruiter direction

Recruiter task: for each job, rank all candidates.
Queries evaluated: 32 (skipped, no relevant item: 0).

| Method | precision@3 | precision@5 | precision@10 | recall@3 | recall@5 | recall@10 | ndcg@3 | ndcg@5 | ndcg@10 | mrr |
|---|---|---|---|---|---|---|---|---|---|---|
| Random (seeded) | 0.073 | 0.075 | 0.084 | 0.020 | 0.032 | 0.073 | 0.060 | 0.060 | 0.085 | 0.198 |
| TF-IDF baseline | 0.979 | 0.969 | 0.866 | 0.278 | 0.457 | 0.810 | 0.905 | 0.899 | 0.917 | 1.000 |
| TF-IDF + semantic (LSA) | 0.958 | 0.963 | 0.844 | 0.269 | 0.453 | 0.791 | 0.892 | 0.889 | 0.900 | 1.000 |
| Skills only | 0.958 | 0.963 | 0.819 | 0.272 | 0.457 | 0.768 | 0.897 | 0.889 | 0.881 | 1.000 |
| Hybrid (MatchMind) | 0.969 | 0.963 | 0.875 | 0.274 | 0.452 | 0.819 | 0.900 | 0.902 | 0.927 | 1.000 |

Paired difference, Hybrid minus TF-IDF baseline (95% bootstrap CI):

- ndcg@3: -0.004 [-0.040, +0.028] (CI includes 0)
- ndcg@5: +0.003 [-0.015, +0.020] (CI includes 0)
- ndcg@10: +0.009 [-0.018, +0.037] (CI includes 0)
- mrr: +0.000 [+0.000, +0.000] (CI includes 0)

## Seeker direction

Job-seeker task: for each candidate, rank all jobs.
Queries evaluated: 122 (skipped, no relevant item: 0).

| Method | precision@3 | precision@5 | precision@10 | recall@3 | recall@5 | recall@10 | ndcg@3 | ndcg@5 | ndcg@10 | mrr |
|---|---|---|---|---|---|---|---|---|---|---|
| Random (seeded) | 0.093 | 0.097 | 0.100 | 0.094 | 0.157 | 0.350 | 0.108 | 0.146 | 0.221 | 0.232 |
| TF-IDF baseline | 0.757 | 0.510 | 0.282 | 0.835 | 0.908 | 0.977 | 0.920 | 0.910 | 0.920 | 0.986 |
| TF-IDF + semantic (LSA) | 0.724 | 0.503 | 0.277 | 0.803 | 0.897 | 0.965 | 0.895 | 0.895 | 0.904 | 0.982 |
| Skills only | 0.792 | 0.544 | 0.288 | 0.868 | 0.951 | 0.992 | 0.935 | 0.933 | 0.938 | 0.996 |
| Hybrid (MatchMind) | 0.811 | 0.554 | 0.290 | 0.881 | 0.965 | 0.997 | 0.958 | 0.955 | 0.955 | 1.000 |

Paired difference, Hybrid minus TF-IDF baseline (95% bootstrap CI):

- ndcg@3: +0.037 [+0.020, +0.056] (CI excludes 0)
- ndcg@5: +0.045 [+0.030, +0.061] (CI excludes 0)
- ndcg@10: +0.035 [+0.024, +0.046] (CI excludes 0)
- mrr: +0.014 [+0.000, +0.030] (CI includes 0)

## Caveats

- All jobs, candidates and relevance labels are synthetic and rule-generated. Results show how the pipeline works, not real hiring accuracy.
- Labels use concepts (skills, role family, experience) that the hybrid scorer also uses, so it has a structural advantage over the text-only baseline.
- Candidate profiles are small (tens to ~120), so confidence intervals are wide; read differences together with the CIs.
- No protected attributes (age, gender, ethnicity, photo, ...) exist in the data or are used by any method.
