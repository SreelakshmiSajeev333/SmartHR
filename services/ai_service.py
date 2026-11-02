from google import genai
from google.genai import types

from flask import current_app


def generate_hr_response(question, relevant_chunks):

    """
    Generate an HR policy answer using Gemini
    and retrieved policy document information.
    """

    api_key = current_app.config.get("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("Gemini API key is not configured.")

    if not relevant_chunks:
        return (
            "I could not find sufficient information in the "
            "available HR policy documents. Please contact HR "
            "for clarification."
        )

    context = "\n\n".join(
        [
            f"Policy: {chunk['policy_title']}\n"
            f"Content: {chunk['content']}"
            for chunk in relevant_chunks
        ]
    )

    prompt = f"""
You are SmartHR, an AI-powered HR policy assistant.

Answer employee questions using ONLY the HR policy
information provided below.

Instructions:

1. Provide clear and professional answers.
2. Do not invent company policies.
3. Do not assume information that is not provided.
4. If the information is insufficient, clearly say so.
5. Do not make final decisions on sensitive HR matters.
6. Recommend contacting HR when human assistance is required.

HR POLICY INFORMATION:

{context}

EMPLOYEE QUESTION:

{question}

Provide a helpful and accurate response.
"""

    try:

        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=30000,
                retry_options=types.HttpRetryOptions(
                    attempts=1
                )
            )
        )

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        answer = response.text

        if not answer:
            raise ValueError("Gemini returned an empty response.")

        return answer.strip()

    except Exception as error:

        current_app.logger.exception(
            "Gemini API error: %s",
            error
        )

        raise RuntimeError(
            "Unable to generate an AI response. Please try again."
        ) from error