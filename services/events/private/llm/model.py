import json

from pydantic import BaseModel
from . import prompt_config
from llama_cpp import Llama

from common import models
from helpers.email_data import Email

class Llama3Model():
    MAX_GENERATED_TOKENS = 6000

    def __init__(self, model_location, **kwargs) -> None:
        self.model = Llama(
            n_ctx=32768,
            n_gpu_layers=-1,
            model_path=model_location, 
            chat_format="llama-3",
            **kwargs
        )

    def format_email_for_llm(self, email: Email) -> str:
        prepared_content = f"Email reader: {email.reader_email}\n"
        prepared_content += f"Email sender: {email.sender_email}\n"
        prepared_content += f"Email from: {email.from_email}\n"
        prepared_content += f"Email recipients: {', '.join(email.recipient_emails)}\n"
        prepared_content += f"Send time: {email.send_date.isoformat()}\n"
        prepared_content += f"Title: {email.title}\n"
        prepared_content += f"Content:\n{email.content}"

        return prepared_content
    
    def parse_events_from_email(self, email: Email, tags: list[str]) -> list[dict[str]]:
        events: list[dict[str]] = []
        prompt = prompt_config.format_event_parse_prompt(tags)
        prepared_content = self.format_email_for_llm(email)

        chat_output = self.model.create_chat_completion(
            messages = [
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": prepared_content
                },
            ],
            grammar=prompt_config.get_parse_output_grammar(tags),
            max_tokens=self.MAX_GENERATED_TOKENS,
            temperature=0.6
        )

        try:
            events = json.loads(chat_output["choices"][0]["message"]["content"], strict=False)
        except json.decoder.JSONDecodeError:
            raise ValueError(f'Error decoding AI generated string {chat_output["choices"][0]["message"]["content"]}')

        return events