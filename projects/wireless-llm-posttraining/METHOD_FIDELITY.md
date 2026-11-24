# Method fidelity and scope

**ALGORITHM MODIFICATION - This is not an unchanged implementation of the cited paper.**

## Original method

[DeepSeekMath, Section 4.1 and Equations 3–4](https://arxiv.org/html/2402.03300v3) defines Group Relative Policy Optimization (GRPO). For each prompt, an old policy samples a group of responses. The method forms relative advantages from the group rewards, then maximizes a token-level clipped policy-ratio surrogate while penalizing divergence from a reference policy with the paper's nonnegative KL estimator. Its reported math experiment uses a learned reward model. The paper also describes an iterative variant that retrains this reward model.

## User-requested adaptation

This project uses the same outcome-supervision GRPO objective, including group-mean/std normalization, per-token ratios and clipping, response-length normalization, and the paper's KL estimator. It replaces the learned math reward model with an exact, deterministic solver score for a separately designed wireless scheduling task. The reward is `achieved sum rate / exact optimal sum rate` for valid allocations and zero for malformed or infeasible responses. There is no reward-model fitting or iterative reward-model refresh because there is no learned reward model. The model is a 135M-parameter pretrained checkpoint, not DeepSeekMath's 7B model. Full model parameters are updated in both SFT and GRPO; there is no LoRA or quantization in this experiment.

The paper does not specify the degrees-of-freedom convention for group standard deviation; this implementation uses population standard deviation. A group with identical rewards has undefined normalized advantage, so the run records it and makes no policy update. The run uses group size 8, two policy iterations, clipping epsilon 0.2, KL coefficient beta 0.04, and FP32 AdamW with gradient clipping at norm 1.0. These settings are frozen in the run log. They differ from large-scale paper settings and can change the optimization trajectory.

## Consequences

- **Feasible set:** the wireless allocation task has its own feasible set: each of two RBs is assigned to a distinct user. It is independent of the paper's math task. The GRPO policy is a smaller model class than the published 7B system; no paper claim about reachable policies transfers.
- **Objective:** the algebraic GRPO surrogate and KL term are retained, but their reward input is different. The exact solver reward evaluates allocation quality and constraints rather than a learned math reward. The numerical optimization objective and learned behavior therefore differ from the paper's experiment.
- **Optimality guarantees:** the small exhaustive solver guarantees an optimum only for each tiny discrete scheduling instance. GRPO has no guarantee of learning that optimum, and the solver's guarantee does not extend to the language model.
- **Complexity:** the verifier enumerates `n(n-1)` allocations per response (six or twelve here) instead of running a reward model. Group size 8 reduces sampled responses and memory relative to the paper's larger groups, but also changes reward-diversity and gradient-variance behavior. Full-parameter updates retain optimizer-state costs.
- **Benchmark comparability:** the model, data, reward, hardware, scale, and evaluation differ. The measured scores cannot be compared numerically with DeepSeekMath's benchmarks or interpreted as its reproduction.
- **Unverified effects:** results use one training seed, 64 examples per test, deterministic greedy evaluation, synthetic rates, and short responses. Robustness across seeds, larger schedulers, realistic channels, and additional deployment constraints remains unknown.

The user's request explicitly specifies GRPO on resource allocation with a solver checking answers, authorizing the task/reward change. All artifacts call this a **solver-reward GRPO adaptation**. The exhaustive reference solver is explicitly labeled as independently designed.
