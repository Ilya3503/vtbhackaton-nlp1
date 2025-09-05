from openai import OpenAI
import json
from typing import Optional, Dict, Any

client = OpenAI(api_key="")

def generate_ai_vacancy_suggestions(title: str) -> Dict[str, Any]:
    prompt = f"""
Ты — HR-ассистент. По названию вакансии: "{title}"
Сгенерируй JSON с ключами:
- description: краткое описание вакансии
- requirements: список основных требований (в одном тексте, с разделителями)
- salary: примерная рыночная зарплата в рублях (целое число)

Формат ответа строго JSON без лишнего текста.
Пример:
{{
  "description": "Краткое описание...",
  "requirements": "Требование 1; Требование 2; Требование 3",
  "salary": 120000
}}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        content = response.choices[0].message.content.strip()

        return json.loads(content)
    except Exception as e:
        print(f"AI vacancy generation error: {e}")
        return {"description": None, "requirements": None, "salary": None}
