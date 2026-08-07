"""
PolyFlow @error-map Engine.

Translates cryptic language stack traces into plain English explanations and actionable guidance.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from polyflow.parser import ErrorMapping

@dataclass
class TranslatedError:
    raw_error: str
    translated_text: str
    severity: str = "warning"
    language: str = "generic"
    mapped: bool = False
    action: Optional[str] = None

class PolyErrorTranslator:
    def __init__(self, error_maps: Optional[List[ErrorMapping]] = None):
        self.error_maps = error_maps or []
        self.audit_log: List[Dict[str, Any]] = []

    def translate(self, raw_error: str, language: str = "generic") -> TranslatedError:
        if not raw_error:
            return TranslatedError(raw_error="", translated_text="No error recorded.", mapped=False)

        raw_clean = raw_error.strip()

        # Check in error maps matching language or generic
        for em in self.error_maps:
            if em.language.lower() in (language.lower(), "generic", "universal"):
                for pattern, translation in em.rules.items():
                    if self._match_pattern(pattern, raw_clean):
                        translated_txt = self._format_translation(translation, raw_clean)
                        severity = em.metadata.get("severity", "warning")
                        action = em.metadata.get("auto_action", None)

                        result = TranslatedError(
                            raw_error=raw_clean,
                            translated_text=translated_txt,
                            severity=severity,
                            language=language,
                            mapped=True,
                            action=action
                        )
                        self._log_translation(result)
                        return result

        # Built-in fallbacks for common raw stack traces
        builtin = self._check_builtin_rules(raw_clean, language)
        if builtin:
            self._log_translation(builtin)
            return builtin

        fallback = TranslatedError(
            raw_error=raw_clean,
            translated_text=f"Raw execution error: {raw_clean}",
            mapped=False
        )
        self._log_translation(fallback)
        return fallback

    def _match_pattern(self, pattern: str, raw_error: str) -> bool:
        # Pattern syntax support: "AttributeError:NoneType:strip" or regex or substring
        pattern_regex = pattern.replace(":", ".*").replace("*", ".*")
        try:
            return bool(re.search(pattern_regex, raw_error, re.IGNORECASE))
        except re.error:
            return pattern.lower() in raw_error.lower()

    def _format_translation(self, template: str, raw_error: str) -> str:
        # Extract line numbers if present in stack trace
        line_match = re.search(r"line\s+(\d+)", raw_error, re.IGNORECASE)
        line_num = line_match.group(1) if line_match else "unknown"
        return template.replace("{line}", line_num)

    def _check_builtin_rules(self, raw_error: str, language: str) -> Optional[TranslatedError]:
        if "AttributeError" in raw_error and "'NoneType'" in raw_error:
            return TranslatedError(
                raw_error=raw_error,
                translated_text="You called a method on a variable that has no value (None). Check if your database or helper query returned a valid object.",
                severity="warning",
                language=language,
                mapped=True
            )
        elif "ModuleNotFoundError" in raw_error or "ImportError" in raw_error:
            return TranslatedError(
                raw_error=raw_error,
                translated_text="A required package/module is missing. Verify standard dependencies in @standard or run installation.",
                severity="high",
                language=language,
                mapped=True
            )
        elif "ZeroDivisionError" in raw_error:
            return TranslatedError(
                raw_error=raw_error,
                translated_text="Division by zero occurred. Check mathematical calculations and input non-zero guards.",
                severity="warning",
                language=language,
                mapped=True
            )
        return None

    def _log_translation(self, trans: TranslatedError):
        self.audit_log.append({
            "raw": trans.raw_error,
            "translated": trans.translated_text,
            "severity": trans.severity,
            "mapped": trans.mapped,
            "action": trans.action
        })
