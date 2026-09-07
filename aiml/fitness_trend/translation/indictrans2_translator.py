"""
IndicTrans2 Translation Service Wrapper.
Provides translation for Indian languages using AI4Bharat's IndicTrans2 models.
Includes safe initialization with graceful fallback when models or deep learning
frameworks (torch, transformers) are not installed in the environment.
"""

import logging
from .language_config import get_indictrans_code, is_supported_language

logger = logging.getLogger("fitness_trend.translation.indictrans2")


class IndicTrans2Translator:
    """
    Modular wrapper for AI4Bharat IndicTrans2 model inference.
    Handles device placement, tokenizer, batching, and beam search decoding.
    """
    def __init__(self, model_name="ai4bharat/indictrans2-en-indic-dist-200M"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.device = "cpu"
        self._initialized = False
        self._available = False

    def check_availability(self):
        """
        Checks if required deep learning libraries (torch, transformers)
        are importable in the current Python environment.
        """
        try:
            import torch
            import transformers
            return True
        except ImportError as e:
            logger.info(f"IndicTrans2 dependencies not found ({e}). Fallback translator will be used.")
            return False

    def initialize(self):
        """
        Attempts to load IndicTrans2 weights and tokenizer.
        Guaranteed not to raise an unhandled exception or crash the application.
        """
        if self._initialized:
            return self._available

        self._initialized = True
        if not self.check_availability():
            self._available = False
            return False

        try:
            import torch
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading IndicTrans2 model '{self.model_name}' on device '{self.device}'...")
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name, trust_remote_code=True).to(self.device)
            self.model.eval()
            self._available = True
            logger.info("IndicTrans2 loaded successfully.")
            return True
        except Exception as e:
            logger.warning(f"Could not load IndicTrans2 model ({e}). Controlled fallback translator will be active.")
            self._available = False
            return False

    def is_available(self):
        """Returns True if IndicTrans2 is loaded and ready for inference."""
        if not self._initialized:
            self.initialize()
        return self._available

    def translate_batch(self, sentences, src_lang="en", tgt_lang="hi"):
        """
        Translates a list of sentences from src_lang to tgt_lang using IndicTrans2.
        Returns None if IndicTrans2 is unavailable or translation fails.
        """
        if not sentences or src_lang == tgt_lang:
            return sentences

        if not self.is_available():
            return None

        try:
            import torch
            src_code = get_indictrans_code(src_lang)
            tgt_code = get_indictrans_code(tgt_lang)

            # Preprocess inputs with language tags
            inputs = self.tokenizer(
                sentences,
                src_lang=src_code,
                tgt_lang=tgt_code,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=256
            ).to(self.device)

            with torch.no_grad():
                generated_tokens = self.model.generate(
                    **inputs,
                    use_cache=True,
                    min_length=0,
                    max_length=256,
                    num_beams=4,
                    num_return_sequences=1
                )

            translations = self.tokenizer.batch_decode(
                generated_tokens,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )
            return translations
        except Exception as e:
            logger.error(f"IndicTrans2 batch inference error: {e}", exc_info=True)
            return None
