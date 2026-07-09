"""Custom tokenizer for VoxCPM2 that splits multi-character Chinese tokens.

VoxCPM2 was trained with ``mask_multichar_chinese_tokens`` which splits
multi-character Chinese tokens (e.g. "你好" -> ["你", "好"]) into individual
character IDs before embedding.  The base LlamaTokenizerFast produces
multi-character Chinese tokens that the model has never seen during training,
yielding garbled Chinese audio output in downstream inference frameworks.

This module provides ``VoxCPM2Tokenizer`` which transparently applies the
character splitting inside ``encode()`` and ``__call__()``, so any downstream
consumer (vLLM, vLLM-Omni, Nano-vLLM, etc.) gets correct single-character
IDs without code changes.
"""

from transformers import LlamaTokenizerFast


class VoxCPM2Tokenizer(LlamaTokenizerFast):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._split_map = self._build_split_map()

    def _build_split_map(self) -> dict[int, list[int]]:
        vocab = self.get_vocab()
        split_map: dict[int, list[int]] = {}
        for token, tid in vocab.items():
            clean = token.replace("\u2581", "")
            if len(clean) >= 2 and all(self._is_cjk(c) for c in clean):
                char_ids = self.convert_tokens_to_ids(list(clean))
                if all(c != self.unk_token_id for c in char_ids):
                    split_map[tid] = char_ids
        return split_map

    @staticmethod
    def _is_cjk(c: str) -> bool:
        return (
            "\u4e00" <= c <= "\u9fff"
            or "\u3400" <= c <= "\u4dbf"
            or "\uf900" <= c <= "\ufaff"
            or "\U00020000" <= c <= "\U0002a6df"
        )

    def _expand_ids(self, ids: list[int]) -> list[int]:
        result: list[int] = []
        for tid in ids:
            expansion = self._split_map.get(tid)
            if expansion is not None:
                result.extend(expansion)
            else:
                result.append(tid)
        return result

    def encode(self, text, *args, **kwargs):
        ids = super().encode(text, *args, **kwargs)
        return self._expand_ids(ids)

    def __call__(self, text, *args, **kwargs):
        result = super().__call__(text, *args, **kwargs)
        if hasattr(result, "input_ids"):
            ids = result["input_ids"]
            if isinstance(ids, list) and ids and isinstance(ids[0], list):
                result["input_ids"] = [self._expand_ids(x) for x in ids]
                if "attention_mask" in result:
                    result["attention_mask"] = [
                        [1] * len(x) for x in result["input_ids"]
                    ]
            elif isinstance(ids, list):
                result["input_ids"] = self._expand_ids(ids)
                if "attention_mask" in result:
                    result["attention_mask"] = [1] * len(result["input_ids"])
        return result
