from __future__ import annotations
import os
import requests
from abc import ABC, abstractmethod
from typing import List, Dict


# === ABSTRACTION LAYER ===


class AIProvider(ABC):
    """Interfaz abstracta para proveedores de IA."""

    @abstractmethod
    def chat(
        self, messages: List[Dict[str, str]], system_instruction: str = None
    ) -> str:
        """
        Genera una respuesta de chat.

        Args:
            messages: Lista de mensajes [{"role": "user", "content": "..."}]
            system_instruction: Instrucción opcional del sistema.
        """
        pass

    @abstractmethod
    def generate_analysis(self, prompt: str, system_instruction: str = None) -> str:
        """
        Genera un análisis técnico (one-shot).
        """
        pass


# === DEEPSEEK IMPLEMENTATION (Legacy/Cost-Effective) ===


class DeepSeekProvider(AIProvider):
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.api_url = os.getenv(
            "DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions"
        )
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    def chat(
        self, messages: List[Dict[str, str]], system_instruction: str = None
    ) -> str:
        if not self.api_key:
            return "Error: DEEPSEEK_API_KEY no configurada."

        # Inyectar system message si existe
        full_messages = []
        if system_instruction:
            full_messages.append({"role": "system", "content": system_instruction})

        full_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": float(os.getenv("DEEPSEEK_TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("DEEPSEEK_MAX_TOKENS", "4000")),
        }

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            resp = requests.post(
                self.api_url, json=payload, headers=headers, timeout=30
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            return f"DeepSeek Error: {resp.status_code} - {resp.text[:100]}"
        except Exception as e:
            return f"DeepSeek Connection Error: {str(e)}"

    def generate_analysis(self, prompt: str, system_instruction: str = None) -> str:
        # Reutilizamos la lógica de chat para one-shot
        return self.chat([{"role": "user", "content": prompt}], system_instruction)


# === GEMINI IMPLEMENTATION (Multimodal/High-Logic) ===


class GeminiProvider(AIProvider):
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        # Gemini 1.5 Flash es el mejor balance costo/velocidad en Free Tier
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        self.genai = None
        if self.api_key:
            try:
                import google.generativeai as genai

                self.genai = genai
                self.genai.configure(api_key=self.api_key)
            except ImportError:
                print("[AI] ⚠️ google-generativeai module not found. Gemini Disabled.")

    def chat(
        self, messages: List[Dict[str, str]], system_instruction: str = None
    ) -> str:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY not configured")

        if not self.genai:
            raise ImportError("google-generativeai module not found")

        try:
            # Configurar modelo con system instruction
            model = self.genai.GenerativeModel(
                model_name=self.model_name, system_instruction=system_instruction
            )

            # Convertir historial al formato de Gemini
            # Gemini usa 'user' y 'model' (en lugar de 'assistant')
            gemini_history = []

            # Si el último mensaje es del usuario, ese es el prompt actual,
            # el resto es historia
            user_message = messages[-1]["content"]
            history_messages = messages[:-1]

            for msg in history_messages:
                role = "user" if msg["role"] == "user" else "model"
                gemini_history.append({"role": role, "parts": [msg["content"]]})

            chat_session = model.start_chat(history=gemini_history)
            response = chat_session.send_message(user_message)

            return response.text

        except Exception as e:
            error_msg = str(e).lower()
            # Detectar errores de cuota o rate limit o Server Error general (5xx)
            is_quota_error = (
                "429" in error_msg
                or "403" in error_msg
                or "quota" in error_msg
                or "rate limit" in error_msg
                or "exhausted" in error_msg
            )

            # [AGGRESSIVE FALLBACK] Try fallback for ANY generation error if key
            # is present
            if is_quota_error:
                print(
                    "[AI] ⚠️ Gemini Rate Limit/Quota Hit. "
                    f"Falling back to DeepSeek... (Error: {error_msg[:100]})"
                )
                try:
                    fallback = DeepSeekProvider()
                    return fallback.chat(messages, system_instruction)
                except Exception as fallback_err:
                    # Raise to be caught by router
                    raise RuntimeError(
                        f"Gemini & DeepSeek Failed: {str(e)} | {str(fallback_err)}"
                    )

            raise RuntimeError(f"Gemini Error: {str(e)}")

    def generate_analysis(self, prompt: str, system_instruction: str = None) -> str:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY not configured")

        if not self.genai:
            raise ImportError("google-generativeai module not found")

        try:
            model = self.genai.GenerativeModel(
                model_name=self.model_name, system_instruction=system_instruction
            )
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_msg = str(e)
            is_quota_error = (
                "429" in error_msg
                or "403" in error_msg
                or "quota" in error_msg.lower()
                or "resource" in error_msg.lower()
            )

            if is_quota_error:
                print(
                    "[AI] ⚠️ Gemini Rate Limit Hit during Analysis. Falling back to DeepSeek..."
                )
                try:
                    fallback = DeepSeekProvider()
                    return fallback.generate_analysis(prompt, system_instruction)
                except Exception as fb_e:
                    raise RuntimeError(
                        f"Gemini & DeepSeek Failed: {str(e)} | {str(fb_e)}"
                    )

            raise RuntimeError(f"Gemini Analysis Error: {str(e)}")


# === FACTORY ===


def get_ai_service() -> AIProvider:
    """
    Retorna el proveedor configurado en .env (AI_PROVIDER).
    Default: 'gemini' (Si hay key), sino 'deepseek'.
    """
    # Preferencia del usuario
    provider = os.getenv("AI_PROVIDER", "auto").lower()

    gemini_key = os.getenv("GEMINI_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")

    if provider == "gemini":
        return GeminiProvider()
    elif provider == "deepseek":
        return DeepSeekProvider()

    # Auto-selección: Preferimos DeepSeek por costo/estabilidad (User Request)
    if deepseek_key:
        print("[AI Service] Auto-selecting: DeepSeek")
        return DeepSeekProvider()
    elif gemini_key:
        print("[AI Service] Auto-selecting: Gemini")
        return GeminiProvider()

    # Fallback dummy si no hay nada
    print("[AI Service] ⚠️ NO KEYS FOUND. AI Service Disabled.")
    # Return a provider that always fails, or raise error.
    # To keep interface valid, we return DeepSeekProvider which checks key in methods.
    return DeepSeekProvider()
