import openai
import json
from typing import Dict, Any
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

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
        # ИСПРАВЛЕНО: используй openai.ChatCompletion.create (старый синтаксис)
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content)
    except Exception as e:
        print(f"AI vacancy generation error: {e}")
        return {"description": None, "requirements": None, "salary": None}






def get_questions_ai_suggestions(title: str, description: str, requirements: str, n: int = 7):
    prompt = f"""
Ты — профессиональный HR-ассистент с опытом планирования и проведения собеседований, в том числе технических. У тебя есть вакансия:

Название: "{title}"

Описание:
{description}

Требования:
{requirements}

Сгенерируй {n} вопросов для собеседования — от вводных до технических.
Для каждого вопроса укажи:
- question_text: сам вопрос (строка)
- competence: какую компетенцию проверяет (строка)
- weight: важность от 0 до 1 (число с плавающей точкой)

Верни строго JSON-массив объектов без лишнего текста.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        content = response.choices[0].message.content.strip()

        # Убираем возможное оформление
        content = content.strip("` \n")
        if content.lower().startswith("json"):
            content = content[4:].strip()

        return json.loads(content)

    except Exception as e:
        print(f"AI questions generation error: {e}")
        return []
