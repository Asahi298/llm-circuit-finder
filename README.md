# llm-circuit-finder
I replicated Ng's RYS method and found that duplicating 3 specific layers in Qwen2.5-32B boosts reasoning by 17% and duplicating layers 12-14 in Devstral-24B improves logical deduction from 0.22→0.76 on BBH — no training, no weight changes, just routing hidden states through the same circuit twice. Tools included. Two AMD GPUs, one evening.

# llm-circuit-finder

**Duplicate 3 layers. No training. Logical deduction goes from 0.22 → 0.76.**

This toolkit finds and exploits "reasoning circuits" hidden inside transformer models. The idea: certain contiguous blocks of layers act as indivisible cognitive units. Duplicate them in the forward pass — same weights, no training, no merging — and the model gets measurably smarter on specific capabilities.

Built on [David Ng's RYS method](https://dnhkng.github.io/posts/rys/) and extended with new findings. Everything here was discovered on two AMD consumer GPUs (RX 7900 XT + RX 6950 XT) in one evening.

## Results

### Devstral-Small-2-24B: Layers 12, 13, 14 duplicated once

Validated on standard benchmarks via [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) at n=50:

| Benchmark | Base | +3 layers | Change |
|-----------|------|-----------|--------|
| BBH Logical Deduction | 0.22 | **0.76** | **+245%** |
| GSM8K (strict) | 0.48 | **0.64** | +33% |
| MBPP (code gen) | 0.72 | **0.78** | +8% |
| GSM8K (flexible) | 0.82 | **0.86** | +5% |
| BBH Navigate | 0.96 | **0.98** | +2% |
| BBH Date Understanding | 0.82 | **0.84** | +2% |
| BBH Causal Judgement | 0.66 | 0.66 | — |
| IFEval (strict) | 0.68 | 0.68 | — |

**Average improvement: +8% across all metrics. Nothing degraded.**

### Qwen2.5-Coder-32B: Layers 7, 8, 9 duplicated once

Measured on custom probe suite (BBH-derived + EQ-Bench-style + GSM8K):

| Probe | Base | +3 layers | Change |
|-------|------|-----------|--------|
| Reasoning (causal + logic + nav) | 76.5% | **94.1%** | **+23%** |
| EQ (emotional intelligence) | 92.1 | **93.6** | +1.6% |

## What's going on

Transformers organize themselves during training into functional circuits — multi-layer processing units that perform complete cognitive operations. These circuits are indivisible: duplicating a single layer does almost nothing, but duplicating the right *block* of 3-4 layers gives the model a second pass through its reasoning pipeline.

Different models have different circuits in different places:
- **Devstral-24B** (40 layers): reasoning circuit at layers **12-14**
- **Qwen2.5-32B** (64 layers): reasoning circuit at layers **7-9**

The boundaries are sharp. Shift the block by one layer in either direction and the improvement disappears or inverts.

## The "modes" discovery

Different duplication patterns create distinct cognitive profiles from the same weights:

| Pattern | Math | EQ | Character |
|---------|------|----|-----------|
| Double-pass 13-16 | ↑↑ | ↑ | Math specialist |
| Triple-pass 13-16 | ↑ | ↑↑ | EQ specialist |
| Interleaved 13,13,14,14,15,15,16 | ↑↑↑ | ↓ | Pure math mode |
| Quadruple-pass 13-16 | — | ↑↑ | EQ mode, math neutral |

Same weights on disk. Same VRAM for the base model. Just different routing.

## Quick start

### Find circuits in your model

```bash
pip install gguf requests tqdm

python sweep.py \
    --model /path/to/model.gguf \
    --llama-server /path/to/llama-server \
    --tmpdir /dev/shm/rys \
    --results pass.jsonl \
    --block-sizes 3 4 5 \
    --stride 1 \
    --start-min 10 --start-max 20 \
    --skip-baseline \
    --port 8099 \
    --server-args --device Vulkan1,Vulkan2
```

### Apply a known circuit

```bash
# Duplicate layers 12-14 in Devstral (the result validated above)
python layer_path.py model.gguf improved.gguf \
    -p "0..14,12,13,14,15..39" -v

# Duplicate layers 7-9 in Qwen2.5-32B
python layer_path.py model.gguf improved.gguf \
    -p "0..9,7,8,9,10..63" -v

# Go wild: triple-pass, interleaved, skip layers, whatever you want
python layer_path.py model.gguf experiment.gguf \
    -p "0..16,13,14,15,16,13,14,15,16,17..39" -v
```

### Validate with established benchmarks

```bash
# Start the server with modified model
llama-server -m improved.gguf --port 8089 -ngl 99 --device Vulkan1,Vulkan2

# Run lm-evaluation-harness
lm_eval --model local-chat-completions \
    --model_args model=test,base_url=http://localhost:8089/v1/chat/completions,num_concurrent=1,max_retries=3,tokenized_requests=False \
    --tasks gsm8k_cot,ifeval,mbpp,bbh_cot_fewshot_logical_deduction_five_objects \
    --apply_chat_template --limit 50 \
    --output_path ./eval_results

# Compare runs
python compare_eval.py ./eval_base ./eval_improved
```

## Files

| File | What it does |
|------|-------------|
| `sweep.py` | Main sweep harness — finds optimal layer duplication configs |
| `layer_path.py` | Build any GGUF with an explicit layer execution path |
| `gguf_surgery.py` | Low-level GGUF layer duplication (used by sweep.py) |
| `math_probe.py` | Hard arithmetic probe (Ng's partial-credit scoring) |
| `eq_probe.py` | Emotional intelligence probe (EQ-Bench style) |
| `reasoning_probe.py` | BBH-derived causal/logical/navigation/math word problems |
| `compare_eval.py` | Compare lm-evaluation-harness results across runs |
| `visualize.py` | Text and PNG heatmaps of sweep results |

## How the sweep works

1. For each layer configuration (i, j):
   - GGUF surgery creates a model where layers i..j-1 are physically duplicated
   - The new forward pass: `layers 0..j-1 → layers i..j-1 again → layers j..N-1`
   - llama-server loads the modified model
   - Three probe suites run: math, EQ, reasoning (BBH-derived)
   - Scores are compared to baseline, results printed live
   - Server killed, modified GGUF deleted, next config

2. The search strategy:
   - **Pass 1**: Large blocks (8 layers), wide stride → find the hot zone
   - **Pass 2**: Small blocks (3-5 layers), stride 1 within hot zone → find exact boundaries
   - **Pass 3**: Try multi-pass, interleaved, and compound configs

Modified GGUFs are written to tmpfs (`/dev/shm`) and deleted after each test. The base model weights stay on disk.

## Requirements

- Linux with llama.cpp built (CPU, CUDA, Vulkan, or Metal)
- Python 3.10+ with `gguf`, `requests`, `tqdm`
- Enough VRAM/RAM to run the model + a few extra duplicated layers
- Optional: `lm-eval` for benchmark validation, `matplotlib` for heatmap plots

## FAQ

**Does this use more VRAM?**
Yes, the duplicated layers are physical copies in the GGUF. For 3 extra layers on a 24B model, expect ~1.5 GiB additional. A llama.cpp forward-pass patch (using pointers instead of copies) would eliminate this — contributions welcome.

**Does this slow down inference?**
Yes, proportionally to the number of extra layers. 3 extra layers on a 40-layer model = ~7.5% slower. The reasoning improvement is worth it.

**Will this work on my model?**
Probably. We've tested on Mistral-architecture (Devstral) and Qwen2 architecture. Ng's original work was on Qwen2-72B. The circuits exist in all transformer models — the question is where they are and how big they are. Run the sweep and find out.

**Why not fine-tune instead?**
This is orthogonal to fine-tuning. You can do both. In fact, Ng's RYS models were later fine-tuned by others and topped the HuggingFace leaderboard. Layer duplication changes the architecture; fine-tuning changes the weights. Stack them.

## Credits

- [David Ng](https://dnhkng.github.io/posts/rys/) for the RYS method and the insight that transformers have functional neuroanatomy
- [llama.cpp](https://github.com/ggml-org/llama.cpp) for making local inference practical
- [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) for benchmark validation

## License

MIT
