# llm-circuit-finder
I replicated Ng's RYS method and found that duplicating 3 specific layers in Qwen2.5-32B boosts reasoning by 17% and duplicating layers 12-14 in Devstral-24B improves logical deduction from 0.22→0.76 on BBH — no training, no weight changes, just routing hidden states through the same circuit twice. Tools included. Two AMD GPUs, one evening.
