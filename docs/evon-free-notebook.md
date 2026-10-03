# Zero-cost Evon investigation

Status: **actual GPU inference unverified**. On 2026-10-03 an authenticated Kaggle notebook offered 30 free GPU hours and dual T4s. The prepared notebook was imported and run. CUDA configuration initially failed because CMake could not locate the mounted driver; supplying `/usr/local/nvidia/lib64` resolved configuration and compilation started. The runner now detects this driver path. English/Kannada model responses and a remote endpoint remain unverified until gates pass. No weights were downloaded to the laptop and no paid service was provisioned.

Use `notebooks/evon_free_gpu.ipynb` in an interactive free notebook. Its embedded runner matches `notebooks/evon_free_gpu.py`; it refuses to download on this Windows machine. Select free Kaggle T4 x2 if available, enable Internet, and run cells in order. Account GPU quota, verification and availability must be checked in the actual notebook. Never select paid compute. No HF token is needed: anonymous access to the pinned public GGUF file returned HTTP 200 during investigation.

## Model and runtime

This is [luminenio's community quantized conversion](https://huggingface.co/luminenio/gnani-evon-v3.3-30B-A3B-GGUF), not Gnani's original BF16 checkpoint or proof of its benchmark scores. The converter reports English/Hindi testing; Kannada remains an explicit smoke requirement. All experts still require storage despite the smaller active parameter count.

The runner pins conversion revision `ac033ad46d98503787500e0cb2295897b0b8c03b` and the converter-tested llama.cpp revision `8b4b3558f1459c13e4aa38d5c94d306a00dc6acd`. It verifies SHA256 and preserves license/notice files. It downloads one quant at a time to scratch storage and deletes failed quant files before trying another.

| Order | Quant | Weight size | Reason |
| --- | --- | --- | --- |
| 1 | Q3_K_S | 16.84 GiB | Requested initial candidate |
| 2 | Q3_K_M | 18.62 GiB | Higher Q3 quality candidate |
| 3 | IQ4_XS | 17.09 GiB | Smaller alternate when Q3_K_M cannot fit or pass |

Actual quality and reliable loading must be measured; the order makes no guarantee. The runner builds only llama-server, uses a 2,048-token context, one request slot and small batches. Two GPUs use layer splitting. A single GPU uses partial CPU offload; a failed load retries fewer GPU layers. CPU-only inference is skipped unless available RAM can hold the selected quant plus overhead. CUDA/compiler or download errors require resolving the environment before inference can proceed.

## Free environment constraints

[Kaggle's notebook documentation](https://www.kaggle.com/docs/notebooks) lists free P100 or dual T4 GPU configurations and session/storage limits. Dual T4 is the strongest candidate because Q3_K_S exceeds one 16 GB GPU before runtime overhead. Splitting across GPUs still needs an actual load test. Use scratch storage rather than saving the large model into notebook output; free sessions and quotas do not provide a persistent service.

[Colab's official FAQ](https://research.google.com/colaboratory/faq.html) gives no fixed free hardware guarantee and restricts remote control and primarily using its free runtime through an external web UI. Use Colab for interactive smoke only. This notebook deliberately prohibits remote exposure from Colab. A single T4 plus standard host RAM may struggle; no inference success is assumed.

## Smoke and endpoint gates

The two synthetic requests are English and native Kannada versions of notifying Ananya of a 25-minute delay. The runner asks for schema-constrained JSON through [llama.cpp's OpenAI-compatible server](https://github.com/ggml-org/llama.cpp/blob/8b4b3558f1459c13e4aa38d5c94d306a00dc6acd/tools/server/README.md), disables reasoning, then checks exact tool/contact/delay, confirmation state, goal length and Kannada script. A truncated response fails. Results include quant, hardware, latency, token usage and correctness; no credentials are written. A two-request smoke demonstrates feasibility only, not broad Kannada quality or production reliability.

After basic English and Kannada pass, Gate D compares six outputs against known expected plans: English negotiation/calendar acceptance dependency, parking/detour constraint, native Kannada negotiation, and three repetitions of the full signature graph. It compares exact actions/arguments and dependency meaning, not merely JSON validity. All checks must pass before a quant is accepted. No large-scale evaluation begins first.

Only after A–D pass does the runner leave llama-server running on notebook loopback. **No tunnel implementation remains in the notebook or runner. Gate E is deferred.** A future authenticated temporary HTTP path needs platform-use verification; do not tunnel free Colab. A free Cloudflare Quick Tunnel may be investigated later, but no endpoint has been obtained or tested. Never upload the local .env or use HF/speech tokens as endpoint credentials.

Keep EVON_MODE=mock for development. EVON_MODE=remote plus a separately verified EVON_BASE_URL/EVON_MODEL/EVON_API_KEY will be used for actual remote tests after Gate E. EvonClient owns both the initial notification contract and frozen v1 mission graph contract. The product graph uses MockEvon today; real v1 execution remains deliberately unconnected until verification. See evon-contract.md.
