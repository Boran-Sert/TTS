# Modernized Text Normalizer incorporating Native Banking TN Engine
import re
from .banking_tn import NativeBankingTextNormalizer

class TextNormalizer:
    def __init__(self, tokenizer=None):
        self.tokenizer = tokenizer
        self.banking_tn = NativeBankingTextNormalizer()

    def normalize(self, text: str, split: bool = False) -> str:
        if not text:
            return ""
        # 1. Clean basic extra whitespace & newlines
        text = text.replace("\n", " ").replace("\t", " ")
        text = re.sub(r"\s+", " ", text).strip()
        
        # 2. Apply Native Banking & Financial Market Normalization
        text = self.banking_tn.normalize(text)
        
        return text
