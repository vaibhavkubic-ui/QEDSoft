from __future__ import annotations

import re

from .common import sanitize_identifier


class LeanExpressionTranslator:
    """Translate a conservative MATLAB/SystemVerilog expression subset to Lean4.

    The translator is intentionally small and deterministic. Unsupported syntax
    is normalized into comments by callers instead of guessed.
    """

    TOKEN = re.compile(r"(?<![A-Za-z0-9_])([A-Za-z_]\w*)(?![A-Za-z0-9_])")

    def translate(
        self,
        expression: str,
        scopes: dict[str, str],
        constants: set[str] | None = None,
    ) -> str:
        constants = constants or set()
        expr = expression.strip().rstrip(";")
        expr = self._normalize_literals(expr)
        expr = self._normalize_operators(expr)

        def repl(match: re.Match[str]) -> str:
            token = match.group(1)
            lowered = token.lower()
            if lowered in {"true", "false"}:
                return lowered
            if token in constants:
                return sanitize_identifier(token)
            if token in {"if", "then", "else", "and", "or", "not"}:
                return token
            if token in scopes:
                return f"{scopes[token]}.{sanitize_identifier(token)}"
            return sanitize_identifier(token)

        return self.TOKEN.sub(repl, expr)

    def _normalize_literals(self, expr: str) -> str:
        expr = expr.replace("'0", "0").replace("'1", "1")
        expr = re.sub(r"\d+'[bB]([01_xXzZ]+)", lambda m: self._verilog_bits_to_int(m.group(1)), expr)
        expr = re.sub(r"\btrue\b", "true", expr, flags=re.I)
        expr = re.sub(r"\bfalse\b", "false", expr, flags=re.I)
        return expr

    def _normalize_operators(self, expr: str) -> str:
        expr = expr.replace("~=", "!=")
        expr = expr.replace("&&", " && ")
        expr = expr.replace("||", " || ")
        expr = re.sub(r"(?<![=!<>])!(?!=)", "!", expr)
        expr = re.sub(r"(?<![A-Za-z0-9_])~\s*", "!", expr)
        expr = re.sub(r"(?<!&)&(?!&)", " && ", expr)
        expr = re.sub(r"(?<!\|)\|(?!\|)", " || ", expr)
        return re.sub(r"\s+", " ", expr).strip()

    def _verilog_bits_to_int(self, bits: str) -> str:
        cleaned = bits.replace("_", "").lower()
        if any(ch in cleaned for ch in "xz"):
            return "0"
        return str(int(cleaned, 2))
