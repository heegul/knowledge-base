# Post-training a small language model for wireless scheduling

This is a reproducible toy experiment in which a pretrained 135M-parameter language model learns a two-resource-block wireless scheduling task. The project compares the untouched model, full-parameter supervised fine-tuning (SFT), and a **solver-reward GRPO adaptation**. An exact solver checks every generated allocation. The point is to expose the training signals and failure modes, not to claim a production scheduler or a reproduction of a large-model paper.

## Task and verifier

Each prompt gives the achievable rate, in Mbps, for each user on two orthogonal resource blocks (RB1 and RB2). The model must answer exactly `RB1=Ux,RB2=Uy`. Each RB goes to one user, and the two users must be distinct. The objective is to maximize `rate[RB1 user][RB1] + rate[RB2 user][RB2]`.

`problem.py` enumerates all `n(n-1)` feasible assignments (six for three users, twelve for four) and returns an exact optimum for this **independently designed discrete task**. It also checks format and constraints. Feasible assignments receive reward `achieved rate / optimal rate`; malformed or infeasible responses receive zero. Multiple assignments can tie for the optimum. The exhaustive solver is a reference for this tiny task, not a replacement implementation of any cited wireless optimization algorithm.

Example:

```text
U0: RB1=5, RB2=9
U1: RB1=8, RB2=2
U2: RB1=3, RB2=4
```

The exact optimum is `RB1=U1,RB2=U0`, totaling 17 Mbps.

## Results

Greedy decoding, maximum 32 new tokens, strict output parsing, one seed. Each test has 64 disjoint examples. A response is *optimal* if it is feasible and reaches the solver's maximum sum rate.

| Held-out test | Pretrained base | After SFT | After solver-reward GRPO |
|---|---:|---:|---:|
| Three users, rates 1–9 Mbps | 0/64 (0%) | 55/64 (85.9%) | 56/64 (87.5%) |
| OOD: rates 10–30 Mbps | 0/64 (0%) | 32/64 (50.0%) | 41/64 (64.1%) |
| OOD: four users, rates 1–9 Mbps | 0/64 (0%) | 21/64 (32.8%) | 18/64 (28.1%) |

| Test | Base feasible | SFT feasible | GRPO feasible | SFT mean optimum ratio | GRPO mean optimum ratio |
|---|---:|---:|---:|---:|---:|
| Three users | 0/64 | 64/64 | 64/64 | 0.982 | 0.979 |
| Higher rates | 0/64 | 64/64 | 64/64 | 0.904 | 0.939 |
| Four users | 0/64 | 64/64 | 59/64 | 0.795 | 0.745 |

The base model generally continued the placeholder `RB1=Ux,RB2=Uy` rather than choosing users, so its zero score combines format failure and task failure. SFT learned the format and much of the small optimization rule. GRPO's in-distribution exact gain was **one case out of 64**, while its mean optimality ratio was slightly lower. The higher-rate test improved by nine net cases (10 SFT errors fixed, one new error). The four-user test regressed by three net cases and lost feasibility. These are small, single-seed synthetic tests; the results do not establish broad wireless or reasoning gains.

The synthetic rate table omits interference, power control, fairness, temporal traffic, and channel-estimation error. The two OOD tests change only one dimension each. All results are saved as raw responses and solver scores under `results/run_001/`; `summarize.py` recomputes every score before emitting `summary.json`. The data generator is deterministic, but exact GPU training results may vary across systems or CUDA kernels.

## Training stages

1. **Pretrained base:** [`HuggingFaceTB/SmolLM2-135M`](https://huggingface.co/HuggingFaceTB/SmolLM2-135M), Apache-2.0, revision `93efa2f097d58c2a74874c7e644dbc9b0cee75a2`.
2. **SFT:** 512 solver-labeled examples, three epochs, full-parameter FP32 AdamW. Response tokens alone contribute to the cross-entropy loss. This run made 192 updates in 38.5 seconds of training-loop time; peak PyTorch allocation was 3,213 MiB.
3. **Solver-reward GRPO adaptation:** starts from the SFT checkpoint. It samples eight responses per prompt, normalizes rewards within each group, applies the token-level clipped GRPO surrogate and a reference-policy KL penalty, and uses two policy iterations per sampled group. The reference remains the frozen SFT model. Hyperparameters: `epsilon=0.2`, `beta=0.04`, learning rate `1e-5`, 120 groups. Of these, 84 had equal rewards and supplied no relative signal; the other 36 yielded 72 policy updates. The RL loop took 109.4 seconds; peak PyTorch allocation was 3,599 MiB.

The GRPO objective follows [DeepSeekMath, Section 4.1, Equations 3–4](https://arxiv.org/html/2402.03300v3). **The solver reward and wireless domain are user-requested adaptations of its learned-reward math experiment.** See [METHOD_FIDELITY.md](METHOD_FIDELITY.md) for the exact differences and limitations. This repository does not label the run as a faithful DeepSeekMath reproduction. `train_grpo.py` implements the objective directly instead of relying on changing trainer defaults.

## Reproduce

Tested on Windows, Python 3.13.11, RTX 2080 Ti (11 GB), CUDA-enabled PyTorch 2.7.1+cu118, Transformers 4.57.6. Install a CUDA-capable PyTorch build suitable for your hardware first; then install `requirements.txt`. Do not accidentally replace CUDA PyTorch with a CPU-only wheel.

```powershell
python -m pip install -r requirements.txt
hf download HuggingFaceTB/SmolLM2-135M --revision 93efa2f097d58c2a74874c7e644dbc9b0cee75a2 --local-dir model
python -m unittest -v test_problem test_grpo
python train_sft.py --model-dir model --run-dir runs/run_001
python evaluate.py --checkpoint model --run-dir runs/run_001 --stage base
python evaluate.py --checkpoint runs/run_001/checkpoints/sft --run-dir runs/run_001 --stage sft
python train_grpo.py --run-dir runs/run_001 --groups 120 --group-size 8
python evaluate.py --checkpoint runs/run_001/checkpoints/grpo --run-dir runs/run_001 --stage grpo
python summarize.py --run-dir runs/run_001
python export_public_results.py --run-dir runs/run_001 --output-dir results/run_001
```

The scripts generate deterministic, deduplicated splits: 512 SFT training, 160 separate RL prompts, 64 validation (not used for model selection), and three held-out tests of 64 each. Neither training stage reads test labels. The local model and full-parameter checkpoints are excluded from Git because they are large; public raw JSON results and dataset hashes are retained. Run evaluations in separate processes to keep GPU memory use predictable. The exact settings and sample outputs are in `results/run_001/`.

## Project context

This is the wireless extension of a personal post-training learning project. An earlier arithmetic lab on Qwen3-0.6B-Base taught response-only SFT with LoRA; the wireless experiment starts afresh from SmolLM2-135M and trains all parameters to keep the GRPO policy update directly inspectable. The earlier lab's arithmetic scores are **not** included in the wireless comparison.
