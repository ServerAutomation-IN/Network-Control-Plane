"""Ollama Local LLM Provider Adapter — Network Control Plane"""

from typing import Optional, Dict, Any
import httpx
from app.ai.providers.base import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    """Adapter for local Ollama LLM endpoint."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def get_provider_name(self) -> str:
        return f"Ollama ({self.model})"

    async def verify_connection(self) -> Dict[str, Any]:
        """Verify reachability and model availability via /api/tags in milliseconds without cold-start inference lag."""
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    raw_models = resp.json().get("models", [])
                    models_list = []
                    for m in raw_models:
                        name = m.get("name") or m.get("model") or ""
                        if name and name not in models_list:
                            models_list.append(name)

                    # Match exact model name or prefix (e.g. qwen2.5-coder:7b or qwen2.5-coder)
                    model_found = any(
                        self.model == m or m.startswith(f"{self.model}:") or self.model.startswith(m.split(":")[0])
                        for m in models_list
                    )

                    installed_str = ", ".join(models_list[:6])
                    if model_found:
                        return {
                            "success": True,
                            "message": f"Ollama Server Online. Verified model '{self.model}' among {len(models_list)} installed model(s): [{installed_str}].",
                        }
                    elif len(models_list) > 0:
                        return {
                            "success": True,
                            "message": f"Ollama Server Online at {self.base_url}. Model '{self.model}' is not installed. Available model(s): [{installed_str}].",
                        }
                    return {
                        "success": True,
                        "message": f"Ollama Server Online at {self.base_url}, but no models are currently installed.",
                    }
                return {"success": False, "message": f"[Ollama Error {resp.status_code}] Failed to inspect tags."}
        except httpx.ConnectError:
            return {
                "success": False,
                "message": f"[Ollama Connection Refused] Could not connect to {self.base_url}. Ensure Ollama is running with OLLAMA_HOST=0.0.0.0.",
            }
        except httpx.TimeoutException:
            return {"success": False, "message": f"[Ollama Timeout] Server at {self.base_url} did not respond within 10s."}
        except Exception as exc:
            return {"success": False, "message": f"[Ollama Connection Failed] {str(exc)}"}

    async def generate_completion(
        self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.2
    ) -> str:
        url = f"{self.base_url}/api/generate"
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": 1024},
        }
        try:
            # 120s timeout to allow large models (e.g. 20B/32B parameters) to load into VRAM/RAM
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    res_json = resp.json()
                    content = res_json.get("response") or res_json.get("thinking") or ""
                    if not content and "message" in res_json:
                        content = res_json.get("message", {}).get("content", "")
                    return content.strip()
                error_detail = resp.json().get("error", resp.text)
                return f"[Ollama Error {resp.status_code}] {error_detail}"
        except httpx.TimeoutException:
            return f"[Ollama Timeout] Model '{self.model}' at {self.base_url} took longer than 120s to respond."
        except httpx.ConnectError:
            return f"[Ollama Connection Refused] Could not connect to {self.base_url}. Ensure Ollama is running with OLLAMA_HOST=0.0.0.0."
        except Exception as exc:
            return f"[Ollama Offline] Connection failed: {str(exc)}"
