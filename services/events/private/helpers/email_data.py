from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class Email:
    id: str
    title: str
    content: str
    send_date: datetime
    sender_email: str # Usually the same, but can be something different from the original sender, if that person is using a mailing list
    from_email: str # Original sender's email
    recipient_emails: list[str]
    reader_email: str
    mail_link: str
    is_draft: bool

    @staticmethod
    def from_outlook_json(email_data: dict, reader_email: str):
        if(email_data["body"]["contentType"] != "text"):
            raise ValueError(f"email data for {email_data['id']} is {email_data['body']['contentType']}, but expected 'text'")
        
        recipients: list[str] = []
        for recipient in email_data["toRecipients"]:
            try:
                recipients.append(recipient["emailAddress"]["address"])
            except KeyError:
                continue
            
        sender_email = None if email_data["isDraft"] else email_data["sender"]["emailAddress"]["address"]
        from_email = None if email_data["isDraft"] else email_data["from"]["emailAddress"]["address"]

        return Email(id=email_data["id"],
                    title=email_data["subject"],
                    send_date=datetime.strptime(email_data["sentDateTime"], "%Y-%m-%dT%H:%M:%SZ"),
                    content=email_data["body"]["content"],
                    sender_email=sender_email,
                    from_email=from_email,
                    recipient_emails=recipients,
                    reader_email=reader_email,
                    mail_link=email_data["webLink"],
                    is_draft=email_data["isDraft"]
                    )
