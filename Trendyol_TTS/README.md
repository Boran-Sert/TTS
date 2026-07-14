---
license: mit
language:
- tr
base_model:
- openbmb/VoxCPM2
pipeline_tag: text-to-speech
tags:
- text-to-speech
- speech-synthesis
- turkish
- voxcpm2
- lora
- merged-lora
- trendyol-tts
---

# Trendyol-TTS

**Trendyol-TTS** is a Turkish text-to-speech research model built on top of **openbmb/VoxCPM2**. It is based on the Trendyol Turkish TTS LoRA training run and uses the manually selected `step_0002000` checkpoint as the released default. The repository contains a merged standalone model artifact: the Turkish LoRA adapter was applied to the VoxCPM2 base weights, while the original LoRA adapter files are kept for provenance and auditability. The model is optimized for Turkish speech synthesis experiments, evaluation, and controlled prototyping rather than general-purpose production serving.

---

## 🔑 Highlights

* **Turkish Text-to-Speech** - Fine-tuned for Turkish speech generation using a private Turkish voice dataset.
* **VoxCPM2-Based** - Built from `openbmb/VoxCPM2` and released as a merged model artifact for simpler loading.
* **Selected `step_0002000` Checkpoint** - Chosen as the default after manual listening and checkpoint comparison.
* **LoRA Provenance Preserved** - Includes the merged weights and the original LoRA adapter directory for traceability.
* **Recommended Clean Inference** - Current default setting is `cfg_value=2.0` with `inference_timesteps=16`.
* **Research-Oriented Release** - Intended for evaluation, demos, and controlled experimentation before any production deployment.

### Basic Usage with VoxCPM2

Install the VoxCPM2 runtime requirements on a GPU-capable environment, then load the merged model directly from the Hub.

```python
import soundfile as sf
from voxcpm.core import VoxCPM

model_id = "Trendyol/Trendyol-TTS"
model = VoxCPM.from_pretrained(
    hf_model_id=model_id,
    load_denoiser=False,
    optimize=True,
)

audio = model.generate(
    text="Merhaba, Trendyol TTS modelinden bir Türkçe ses örneği dinliyorsunuz.",
    cfg_value=2.0,
    inference_timesteps=16,
    max_len=4096,
    normalize=True,
    denoise=False,
)

sf.write("trendyol_tts_sample.wav", audio, model.tts_model.sample_rate)
```

---

### Recommended Inference Settings

The currently recommended clean default is:

```text
cfg_value = 2.0
inference_timesteps = 16
```

A more expressive setting worth testing is:

```text
cfg_value = 1.5
inference_timesteps = 16
```

Avoid using `cfg_value=2.5` as a general production default. Internal proxy checks showed some generated samples peaking too close to `0 dBFS`, even when the measured clipping fraction was zero.

## Model Details

* **Model type:** Turkish text-to-speech / speech synthesis
* **Base model:** `openbmb/VoxCPM2`
* **Released checkpoint:** `step_0002000`
* **Fine-tuning method:** LoRA adapter merged into base model weights
* **Training dataset:** `+20 Hours Turkish Speak`
* **Primary language:** Turkish (`tr`)
* **Repository contents:** merged model weights, tokenizer/runtime files, `merge_manifest.json`, and preserved `lora_adapter/` files

## Evaluation Notes

The `step_0002000` checkpoint was selected as the default based on manual listening preference, response quality, and available audio-quality checks. Later continuation checkpoints such as `step_0002250` and `step_0002500` were healthy training runs, but they did not replace `step_0002000` as the recommended release default.

Evaluation artifacts used during development include checkpoint sweeps, inference-parameter sweeps, and blind-listening package tooling. This model card should not be read as a claim of formal MOS, large-scale production stress testing, or complete downstream safety validation.

## Limitations, Risks, Bias, and Ethical Considerations

### Limitations and Known Biases

- **Research artifact:** Trendyol-TTS is a research and prototyping artifact, not a managed production endpoint.
- **Language scope:** The model is intended for Turkish speech synthesis. Performance on other languages, mixed-language text, slang, abbreviations, unusual names, numbers, or long-form text may be weaker.
- **Audio quality variance:** Generated speech may contain pronunciation errors, prosody issues, normalization mistakes, pauses, or synthesis artifacts.
- **Evaluation coverage:** Formal MOS studies, broad ASR/CER semantic regression checks, large-scale load tests, and production monitoring validation are not included in this repository.
- **Dataset constraints:** The training data is a private Turkish speech dataset. Users must respect the dataset owner policies and any applicable usage restrictions.

### Risks and Ethical Considerations

- **Voice misuse:** Do not use this model for impersonation, deception, unauthorized voice cloning, fraud, harassment, or any use that violates applicable law or platform policy.
- **Generated content risk:** Text-to-speech systems can amplify harmful, misleading, or abusive text supplied by users. Application-level content moderation may be required.
- **Deployment responsibility:** Developers are responsible for evaluating quality, consent, safety, abuse prevention, monitoring, and legal compliance before customer-facing deployment.

### Recommendations for Safe and Ethical Usage

- **Human oversight:** Use a human review layer for sensitive, public-facing, or brand-critical generated speech.
- **Application-specific testing:** Validate pronunciation, prosody, latency, throughput, stability, and failure modes on the exact serving stack and target use case.
- **Responsible deployment:** Add safeguards for consent, logging, rate limits, abuse reporting, and prompt/content filtering before exposing the model to end users.

## License

The model card declares MIT metadata following the upstream VoxCPM2 model metadata where applicable. Users are responsible for checking the licenses and usage terms of `openbmb/VoxCPM2`, the private training dataset, and any downstream deployment environment.