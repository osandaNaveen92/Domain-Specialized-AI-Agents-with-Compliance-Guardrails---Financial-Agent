from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()  # IMPORTANT

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_explanation(entry):
    try:
        if not os.getenv("OPENAI_API_KEY"):
            raise Exception("No API key")

        prompt = f"""
        Explain this journal entry clearly:

        Debit: {entry['debit_account']}
        Credit: {entry['credit_account']}
        Amount: {entry['amount']}
        Reason: {entry['reason']}
        """

        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        # Fallback explanation (deterministic)
        return f"Entry records {entry['amount']} from {entry['credit_account']} to {entry['debit_account']} due to {entry['reason']}."