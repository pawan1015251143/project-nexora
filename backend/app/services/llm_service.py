import asyncio
from abc import ABC, abstractmethod
import logging
from app.core.config import settings
from typing import Tuple, List, Dict

logger = logging.getLogger(__name__)

class BaseLLMService(ABC):
    @abstractmethod
    async def generate_response(self, system_prompt: str, user_prompt: str, conversation_history: List[Dict[str, str]] = None) -> Tuple[str, bool]:
        """
        Generate a response using an LLM.
        Returns:
            Tuple[str, bool]: The answer text, and a boolean indicating if it grounded itself in context.
        """
        pass

    @abstractmethod
    async def translate_notice(self, content: str, mode: str) -> str:
        """
        Translate or annotate a notice based on the mode.
        mode: "hi_annotated" or "hi_full"
        """
        pass

    @abstractmethod
    async def extract_notice_info(self, message_text: str, attachment_content: str = "") -> dict:
        """
        Extract structured information from a notice message.
        Returns a dict with keys: title, summary, notice_type, department, audience,
        important_dates, deadline, instructions, contact_info, semester
        IMPORTANT: Preserve all official identifiers, names, dates, numbers exactly.
        """
        pass

class MockLLMService(BaseLLMService):
    async def generate_response(self, system_prompt: str, user_prompt: str, conversation_history: List[Dict[str, str]] = None) -> Tuple[str, bool]:
        """
        Mock LLM that simulates responses based on prompt keywords to pass automated tests.
        """
        # Simulated responses for tests
        if "irrelevant" in user_prompt.lower():
            return "I cannot verify the information based on the provided context.", False
        if "forget" in user_prompt.lower() or "ignore" in user_prompt.lower():
            return "I am an AI assistant bounded by Nexora's guidelines and cannot comply with that request.", False
        if "Context:\n\n" in system_prompt or "Context:\n" in user_prompt:
            if "Context:\n\nUser:" in system_prompt or "Context:\nUser:" in system_prompt: 
                pass 
        if "EMPTY_CONTEXT_FLAG" in user_prompt:
             return "I cannot verify the information based on the provided context.", False
        if "TIMEOUT_SIMULATION" in user_prompt:
            raise RuntimeError("AI provider is currently unavailable. Please try again later.")
        if "API_ERROR_SIMULATION" in user_prompt:
            raise RuntimeError("AI provider is currently unavailable. Please try again later.")

        return "This is a mocked answer grounded in the retrieved documents.", True

    async def translate_notice(self, content: str, mode: str) -> str:
        if "API_ERROR_SIMULATION" in content:
            raise RuntimeError("AI provider is currently unavailable. Please try again later.")
        if mode == "hi_annotated":
            return content + "\n\n(Mocked Annotation)"
        elif mode == "hi_full":
            return "(Mocked Hindi Translation)"
        return content

    async def extract_notice_info(self, message_text: str, attachment_content: str = "") -> dict:
        """Mock extraction returns structured demo data."""
        return {
            "title": "Notice: " + message_text[:60].strip(),
            "summary": "This notice has been received from ABC College Official Notices group.",
            "notice_type": "General",
            "department": "All Departments",
            "audience": "All Students",
            "important_dates": [],
            "deadline": None,
            "instructions": message_text,
            "contact_info": None,
            "semester": None,
        }

class OpenAILLMService(BaseLLMService):
    def __init__(self):
        self.model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini"
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not configured. OpenAI calls will fail.")
            self.client = None
            return

        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None

    def _ensure_client(self):
        if not self.client or not settings.OPENAI_API_KEY:
            logger.error("Attempted OpenAI API call without client or valid OPENAI_API_KEY.")
            raise RuntimeError("AI provider is currently unavailable. Please try again later.")

    async def generate_response(self, system_prompt: str, user_prompt: str, conversation_history: List[Dict[str, str]] = None) -> Tuple[str, bool]:
        self._ensure_client()
            
        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_prompt})
            
        try:
            import openai
            
            # Implementing a 15-second timeout for the LLM response
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.0
                ),
                timeout=15.0
            )
            
            answer = response.choices[0].message.content or ""
            
            is_grounded = True
            lower_answer = answer.lower()
            if (
                "cannot verify the information" in lower_answer
                or "do not have sufficient information" in lower_answer
                or "insufficient information" in lower_answer
                or "cannot verify" in lower_answer
            ):
                is_grounded = False
                
            return answer, is_grounded
            
        except asyncio.TimeoutError:
            logger.error("LLM Provider Timeout")
            raise RuntimeError("AI provider is currently unavailable. Please try again later.")
        except Exception as e:
            import openai
            if isinstance(e, (openai.OpenAIError, openai.APIError, openai.APIConnectionError, openai.RateLimitError, openai.AuthenticationError)):
                logger.error(f"LLM API Error ({type(e).__name__}): {e}")
                raise RuntimeError("AI provider is currently unavailable. Please try again later.")
            elif isinstance(e, RuntimeError):
                raise
            else:
                logger.error(f"Unexpected LLM Error: {e}")
                raise RuntimeError("AI provider is currently unavailable. Please try again later.")

    async def translate_notice(self, content: str, mode: str) -> str:
        self._ensure_client()
            
        if mode == "hi_annotated":
            system_prompt = (
                "You are an assistant for a college notice board. Your task is to take the original English notice and return it exactly as is, "
                "but add Hindi meanings in parentheses next to difficult English words, academic terms, or formal administrative language. "
                "Rules:\n"
                "1. Keep the original English sentence structure.\n"
                "2. Add Hindi meanings only for useful/difficult words or phrases (e.g., 'Internal Assessment (आंतरिक मूल्यांकन)').\n"
                "3. Do not modify dates, names, department names, examination codes, room numbers, URLs, emails, or phone numbers.\n"
                "4. Preserve all original punctuation and formatting.\n"
                "Output the final text only."
            )
        elif mode == "hi_full":
            system_prompt = (
                "You are an assistant for a college notice board. Your task is to provide a complete, natural, and easy-to-understand Hindi translation of the English notice. "
                "Rules:\n"
                "1. Preserve all meaning, dates, times, names, locations, department names, examination info, instructions, contact info, and numerical values accurately.\n"
                "2. Do not invent or alter factual information.\n"
                "3. For technical or official terms, you may preserve the English term alongside Hindi if it aids understanding.\n"
                "Output the final Hindi text only."
            )
        else:
            return content
            
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Notice Content:\n\n{content}"}
        ]
        
        try:
            import openai
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.0
                ),
                timeout=15.0
            )
            return response.choices[0].message.content or ""
        except asyncio.TimeoutError:
            logger.error("LLM Provider Timeout in translation")
            raise RuntimeError("AI provider is currently unavailable. Please try again later.")
        except Exception as e:
            import openai
            if isinstance(e, (openai.OpenAIError, openai.APIError, openai.APIConnectionError, openai.RateLimitError, openai.AuthenticationError)):
                logger.error(f"LLM Translation Error ({type(e).__name__}): {e}")
                raise RuntimeError("AI provider is currently unavailable. Please try again later.")
            elif isinstance(e, RuntimeError):
                raise
            else:
                logger.error(f"Unexpected LLM Error in translation: {e}")
                raise RuntimeError("AI provider is currently unavailable. Please try again later.")

    async def extract_notice_info(self, message_text: str, attachment_content: str = "") -> dict:
        """Use OpenAI to extract structured information from a notice."""
        self._ensure_client()

        combined = message_text
        if attachment_content:
            combined += f"\n\nAttachment Content:\n{attachment_content}"

        system_prompt = (
            "You are an assistant for a college administrative system. "
            "Extract structured information from the following college notice. "
            "CRITICAL RULES:\n"
            "1. Preserve ALL official identifiers EXACTLY: names, dates, exam codes, room numbers, "
            "URLs, emails, phone numbers, registration numbers, numerical values.\n"
            "2. Do NOT invent or hallucinate any information.\n"
            "3. If a field cannot be found, return null for that field.\n"
            "4. Return ONLY a valid JSON object with these exact keys:\n"
            "   title, summary, notice_type, department, audience, important_dates (list), "
            "deadline, instructions, contact_info, semester\n"
            "5. notice_type should be one of: Examination, Assessment, Placement, Academic, Holiday, Administrative, General"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Notice Content:\n\n{combined}"}
        ]

        try:
            import openai
            import json
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.0,
                    response_format={"type": "json_object"}
                ),
                timeout=20.0
            )
            result = json.loads(response.choices[0].message.content or "{}")
            return result
        except asyncio.TimeoutError:
            logger.error("LLM Provider Timeout in notice extraction")
            raise RuntimeError("AI provider is currently unavailable. Please try again later.")
        except Exception as e:
            import openai
            if isinstance(e, (openai.OpenAIError, openai.APIError, openai.APIConnectionError, openai.RateLimitError, openai.AuthenticationError)):
                logger.error(f"LLM Extraction Error ({type(e).__name__}): {e}")
                raise RuntimeError("AI provider is currently unavailable. Please try again later.")
            elif isinstance(e, RuntimeError):
                raise
            else:
                logger.error(f"Notice extraction error: {e}")
                raise RuntimeError("AI provider is currently unavailable. Please try again later.")

def get_llm_service() -> BaseLLMService:
    provider = settings.LLM_PROVIDER.lower()
    if provider == "openai":
        return OpenAILLMService()
    else:
        return MockLLMService()
