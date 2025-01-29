import json
from . import prompt_config
from llama_cpp import Llama

from helpers.email_data import Email

class Llama3Model():
    MAX_GENERATED_TOKENS = 4096

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
    
    def parse_events_from_email(self, email: Email) -> list[dict]:
        events: list[dict] = []
        prompt = prompt_config.format_event_parse_prompt()
        
        # TODO: make a better function for this
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
            response_format=prompt_config.get_parse_prompt_format_rules(),
            max_tokens=self.MAX_GENERATED_TOKENS
        )
        events = json.loads(chat_output["choices"][0]["message"]["content"], strict=False)

        return events