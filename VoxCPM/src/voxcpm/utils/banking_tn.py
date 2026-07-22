"""
Dynamic Native Banking & Financial Market Text Normalizer
---------------------------------------------------------
License: MIT / Apache 2.0 Compliant (Zero External Dependencies)
Design Pattern: Chain of Responsibility & Plug-and-Play Registry (SOLID)
"""

from abc import ABC, abstractmethod
import re

def number_to_turkish_words(n: int) -> str:
    """0 - 999.999.999.999 arası tam sayıları Türkçe okunuşa çevirir (O(1))."""
    if n == 0: return "sıfır"
    units = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
    tens = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
    scales = ["", "bin", "milyon", "milyar"]
    
    words = []
    scale_idx = 0
    while n > 0:
        chunk = n % 1000
        if chunk > 0:
            c_words = []
            h = chunk // 100
            t = (chunk % 100) // 10
            u = chunk % 10
            if h > 0: c_words.append("yüz" if h == 1 else units[h] + " yüz")
            if t > 0: c_words.append(tens[t])
            if u > 0: c_words.append(units[u])
                
            chunk_str = " ".join(c_words)
            if scale_idx == 1 and chunk_str == "bir":
                words.insert(0, "bin")
            elif scale_idx > 0:
                words.insert(0, chunk_str + " " + scales[scale_idx])
            else:
                words.insert(0, chunk_str)
        n //= 1000
        scale_idx += 1
    return " ".join(words)


class CurrencyInfo:
    def __init__(self, code: str, name_tr: str, sub_unit_tr: str = "", symbol: str = None):
        self.code = code
        self.name_tr = name_tr
        self.sub_unit_tr = sub_unit_tr
        self.symbol = symbol


class CurrencyRegistry:
    """Registry Pattern: Dinamik para birimi kaydı"""
    def __init__(self):
        self.currencies = {}
        self.symbols = {}
        self._register_defaults()

    def register(self, curr: CurrencyInfo):
        self.currencies[curr.code.upper()] = curr
        if curr.symbol: self.symbols[curr.symbol] = curr

    def _register_defaults(self):
        # Klasik Para Birimleri
        self.register(CurrencyInfo("TRY", "Türk Lirası", "kuruş", "₺"))
        self.register(CurrencyInfo("TL", "lira", "kuruş"))
        self.register(CurrencyInfo("USD", "Amerikan Doları", "sent", "$"))
        self.register(CurrencyInfo("EUR", "Avro", "cent", "€"))
        self.register(CurrencyInfo("GBP", "İngiliz Sterlini", "pence", "£"))
        self.register(CurrencyInfo("JPY", "Japon Yeni", "", "¥"))
        self.register(CurrencyInfo("CHF", "İsviçre Frangı", "rappen"))
        self.register(CurrencyInfo("CAD", "Kanada Doları", "sent"))
        self.register(CurrencyInfo("AUD", "Avustralya Doları", "sent"))
        self.register(CurrencyInfo("CNY", "Çin Yuanı", "fen"))
        self.register(CurrencyInfo("RUB", "Rus Rublesi", "kopek"))
        self.register(CurrencyInfo("SAR", "Suudi Arabistan Riyali", "halala"))
        self.register(CurrencyInfo("AED", "Birleşik Arap Emirlikleri Dirhemi", "fils"))
        # Kriptolar
        self.register(CurrencyInfo("BTC", "Bitcoin", "satoshi", "₿"))
        self.register(CurrencyInfo("ETH", "Ethereum", "gwei", "Ξ"))
        self.register(CurrencyInfo("USDT", "Tether", "sent"))
        self.register(CurrencyInfo("XRP", "Ripple", "damla"))
        self.register(CurrencyInfo("AVAX", "Avalanche", ""))
        self.register(CurrencyInfo("SOL", "Solana", "lamport"))


class INormalizationRule(ABC):
    @abstractmethod
    def apply(self, text: str) -> str: pass


class DynamicCurrencyRule(INormalizationRule):
    """Dinamik Para Birimleri ve Kuruş/Sent Okuyucu"""
    def __init__(self, registry: CurrencyRegistry):
        self.registry = registry

    def apply(self, text: str) -> str:
        # Ondalıklı tutarlar (1.250,50 TL veya 100,50 USD veya 500,00 ₺)
        pattern_decimal = r"(-?)\b(\d{1,3}(?:\.\d{3})*|\d+),(\d{2})\s*([A-Za-z]{2,4}|[₺$€£¥₿Ξ])\b"
        def repl_decimal(match):
            is_neg = match.group(1) == "-"
            lira_val = int(match.group(2).replace(".", ""))
            kurus_val = int(match.group(3))
            curr_code = match.group(4)
            
            info = self.registry.currencies.get(curr_code.upper()) or self.registry.symbols.get(curr_code)
            if not info:
                return match.group(0)
                
            curr_name = info.name_tr
            sub_name = info.sub_unit_tr
            
            res = "eksi " if is_neg else ""
            res += f"{number_to_turkish_words(lira_val)} {curr_name}"
            if kurus_val > 0 and sub_name:
                res += f" {number_to_turkish_words(kurus_val)} {sub_name}"
            return res

        # Tam tutarlar (18.450 TL / 100 USD)
        pattern_whole = r"(-?)\b(\d{1,3}(?:\.\d{3})+|\d+)\s*([A-Za-z]{2,4}|[₺$€£¥₿Ξ])\b"
        def repl_whole(match):
            is_neg = match.group(1) == "-"
            lira_val = int(match.group(2).replace(".", ""))
            curr_code = match.group(3)
            info = self.registry.currencies.get(curr_code.upper()) or self.registry.symbols.get(curr_code)
            if not info:
                return match.group(0)
                
            curr_name = info.name_tr
            res = "eksi " if is_neg else ""
            res += f"{number_to_turkish_words(lira_val)} {curr_name}"
            return res

        text = re.sub(pattern_decimal, repl_decimal, text)
        text = re.sub(pattern_whole, repl_whole, text)
        return text


class PercentageRule(INormalizationRule):
    """Yüzde Oranları Okuyucu (%2,5 -> yüzde iki virgül beş / %15 -> yüzde on beş)"""
    def apply(self, text: str) -> str:
        # Ondalıklı yüzde (%15,5 veya %2,5)
        pattern_dec = r"%(\d+),(\d+)"
        def repl_dec(match):
            whole = number_to_turkish_words(int(match.group(1)))
            dec = number_to_turkish_words(int(match.group(2)))
            if match.group(2) == "5":
                return f"yüzde {whole} buçuk"
            return f"yüzde {whole} virgül {dec}"

        # Tam sayı yüzde (%15)
        pattern_whole = r"%(\d+)"
        def repl_whole(match):
            val = number_to_turkish_words(int(match.group(1)))
            return f"yüzde {val}"

        text = re.sub(pattern_dec, repl_dec, text)
        text = re.sub(pattern_whole, repl_whole, text)
        return text


class StockTickerRule(INormalizationRule):
    """BIST 100 ve Global Hisse Senedi Kodları Okuyucu (THYAO hissesi -> T H Y A O hissesi)"""
    CONTEXT = r"(hissesi|hisseleri|payı|payları|senedi|kontratı|varantı|fiyatı|portföyü|tavan|taban|lot)"
    def __init__(self):
        self.aliases = {
            "THYAO": "T H Y A O", "GARAN": "G A R A N", "AKBNK": "A K B N K",
            "EREGL": "E R E G L", "SISE": "Ş İ Ş E", "AAPL": "A A P L",
            "NVDA": "N V D A", "TSLA": "T S L A", "MSFT": "M S F T"
        }

    def register_alias(self, ticker: str, spoken_name: str):
        self.aliases[ticker.upper()] = spoken_name

    def apply(self, text: str) -> str:
        pattern = r"\b([A-Z]{3,5})\b(\s+" + self.CONTEXT + r")"
        def repl(match):
            ticker = match.group(1)
            ctx = match.group(2)
            spelled = self.aliases.get(ticker, " ".join(list(ticker)))
            return f"{spelled}{ctx}"
        return re.sub(pattern, repl, text)


class MarketIndicesRule(INormalizationRule):
    LEXICON = {
        r"\bBIST\s*100\b": "Bist yüz", r"\bBIST\s*30\b": "Bist otuz",
        r"\bVIOP\b": "Vi op", r"\bNASDAQ\b": "Nasdak",
        r"\bS&P\s*500\b": "Es en Pi beş yüz", r"\bDOW\s*JONES\b": "Dav Cans",
        r"\bGYO\b": "Ge ye o", r"\bBYF\b": "Be ye fe", r"\bTEFAS\b": "Te fas",
    }
    def apply(self, text: str) -> str:
        for pattern, repl in self.LEXICON.items():
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
        return text


class IBANRule(INormalizationRule):
    def apply(self, text: str) -> str:
        pattern = r"\b(TR\d{2})\s*(\d{4})\s*(\d{4})\s*(\d{4})\s*(\d{4})\s*(\d{4})\s*(\d{2})\b"
        def spell_digits(s: str) -> str:
            m = {'0':'sıfır','1':'bir','2':'iki','3':'üç','4':'dört','5':'beş','6':'altı','7':'yedi','8':'sekiz','9':'dokuz'}
            return " ".join([m[d] for d in s])
        def repl(m):
            g = m.groups()
            return f"{g[0][0]} {g[0][1]} {spell_digits(g[0][2:])} , " + " , ".join([spell_digits(x) for x in g[1:]])
        return re.sub(pattern, repl, text)


class CardMaskRule(INormalizationRule):
    def apply(self, text: str) -> str:
        pattern = r"\b(\d{4})\s*\*+\s*\*+\s*(\d{4})\b"
        def repl(match):
            p1 = number_to_turkish_words(int(match.group(1)))
            p2 = number_to_turkish_words(int(match.group(2)))
            return f"{p1} ile başlayan ve sonu {p2} ile biten kartınız"
        return re.sub(pattern, repl, text)


class AcronymRule(INormalizationRule):
    LEXICON = {
        r"\bEFT\b": "e fe te", r"\bFAST\b": "fast", r"\bBDDK\b": "be de de ka",
        r"\bBSMV\b": "be se me ve", r"\bKKDF\b": "ka ka de fe", r"\bKDV\b": "ka de ve",
        r"\bATM\b": "a te me", r"\bPOS\b": "pos", r"\bIBAN\b": "i ban", r"\bTCKN\b": "te ce ka ne",
        r"\bKMH\b": "ka me ha", r"\bHGS\b": "ha ge se", r"\bOGS\b": "o ge se",
    }
    def apply(self, text: str) -> str:
        for p, r in self.LEXICON.items(): text = re.sub(p, r, text)
        return text


class PhonemeLexiconRule(INormalizationRule):
    LEXICON = {
        r"\bStarbucks\b": "starbaks", r"\bNetflix\b": "netfliks", r"\bApple\b": "epıl",
        r"\bAmazon\b": "amazon", r"\bSpotify\b": "spotifay", r"\bUber\b": "uber",
        r"\bkar payı\b": "kâr payı", r"\bkar oranı\b": "kâr oranı",
    }
    def apply(self, text: str) -> str:
        for p, r in self.LEXICON.items(): text = re.sub(p, r, text, flags=re.IGNORECASE)
        return text


class NativeBankingTextNormalizer:
    """SOLID Chain of Responsibility Executor"""
    def __init__(self, rules: list[INormalizationRule] = None):
        self.currency_registry = CurrencyRegistry()
        self.stock_rule = StockTickerRule()
        if rules is None:
            self._rules = [
                DynamicCurrencyRule(self.currency_registry),
                PercentageRule(),
                self.stock_rule,
                MarketIndicesRule(),
                IBANRule(),
                CardMaskRule(),
                AcronymRule(),
                PhonemeLexiconRule(),
            ]
        else: self._rules = rules

    def add_rule(self, rule: INormalizationRule):
        self._rules.append(rule)

    def register_currency(self, code: str, name_tr: str, sub_unit_tr: str = "", symbol: str = None):
        self.currency_registry.register(CurrencyInfo(code, name_tr, sub_unit_tr, symbol))

    def register_stock_alias(self, ticker: str, spoken_name: str):
        self.stock_rule.register_alias(ticker, spoken_name)

    def normalize(self, text: str) -> str:
        for rule in self._rules: text = rule.apply(text)
        return text
