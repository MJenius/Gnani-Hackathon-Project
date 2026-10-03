# Evon local development decision

Requested model: `gnani/gnani-evon-v3.3-30B-A3B`. The official [model card](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B) describes Transformers, vLLM and SGLang inference. Some examples use the sibling `gnani/gnani-evon-v3.3` identifier; preserve the requested repository and verify the actual served model alias separately.

Observed laptop: Windows, Intel i5-1240P, 15.7 GB RAM, Iris Xe integrated graphics, no nvidia-smi, 45.9 GB free disk. HF metadata reports 31,749,972,288 parameters, overwhelmingly BF16: approximately 63.5 GB decimal (59.1 GiB) for weights before runtime overhead. Active parameters per token do not remove the need to store all experts. The official BF16 inference paths are impractical; 13 weight shards would also exceed available disk. Even a theoretical 4-bit weight floor is roughly 15.9 GB before overhead. No weights, quantizations, CUDA frameworks or remote model code were downloaded/executed.

Token validation, model/config access and a weight shard HEAD returned HTTP 200. Hugging Face's inference-provider mapping is empty. File access does not provide an inference service. No hosted endpoint was invented.

Current development path: community GGUF/llama.cpp gates in an authenticated free Kaggle dual-T4 notebook. See [the free notebook investigation](evon-free-notebook.md) for actual gate status and CUDA-path recovery. No paid host, Space or tunnel is used. HF_TOKEN is for gated weight access; GNANI_API_KEY is for speech. Neither is reused for an inference endpoint.

Model-card vLLM guidance: `vllm>=0.12.0`, `trust_remote_code`, `enable-auto-tool-choice`, `tool-call-parser=qwen3_coder`, `reasoning-parser=nano_v3`. Review remote code before execution. Short structured-answer settings in our adapter follow the card: temperature 0.6, top_p 0.95, repetition penalty 1.1, reasoning off, capped 512 output tokens. Choose a small serving context for this mission rather than blindly allocating 128K.

`EvonClient(completion=...)` validates both the legacy Plan and frozen v1 mission graph. V2 live voice calls `plan_mission` through this adapter when explicitly configured. Unknown tools/malformed graphs fail closed; exact action confirmations remain owned by policy. General-language inference and a remote deployment remain unverified, while MockEvon supplies finite signature fixtures.

Run `python -m app.evaluation.runners.gnani_smoke --evon` after provision to check real English/Kannada output and exact synthetic contact/delay. Current real tests are blocked. Offline callback contract tests pass and are not inference proof. No large-scale model evaluation begins before real smoke tests pass.
