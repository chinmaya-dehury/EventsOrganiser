from dataclasses import dataclass
from datetime import datetime
import json

import email
import email.utils, email.policy


@dataclass
class Email:
    id: str
    title: str
    content: str
    send_date: datetime
    sender_email: str # Usually the same as reader email, but can be something different from the original sender, if that person is using a mailing list
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

    @staticmethod
    def from_raw_str(email_data: str, reader_email: str):
        #global email # py it thinks its some other variable if it isnt global
        mail = email.message_from_string(email_data, policy=email.policy.default)

        recipients: list[str] = []
        for name, email_addr in email.utils.getaddresses(mail.get_all("to", [])):
            recipients.append(email_addr)

        
        content = ""
        if(mail.is_multipart()):
            for part in mail.get_payload():
                if(part.get_content_type() == "text/plain"):
                    content += part.get_payload() + "\n"
        else:
            content = mail.get_payload()

        return Email(
            id=mail["Message-ID"],
            title=mail["Subject"],
            content=content,
            send_date=email.utils.parsedate_to_datetime(mail["Date"]),
            sender_email=email.utils.parseaddr(mail["From"]),
            from_email=email.utils.parseaddr(mail["From"]),
            recipient_emails=recipients,
            reader_email=reader_email,
            mail_link="",
            is_draft=False
        )

def str_to_mail(mail_data: str, reader_email: str) -> Email:
    try:
        return Email.from_outlook_json(json.loads(mail_data), reader_email)
    except:
        pass

    try:
        return Email.from_raw_str(mail_data, reader_email)
    except:
        pass

    raise ValueError("Unable to identify mail provider by string, mail: ", mail_data)

def format_email_for_llm(email: Email) -> str:
    prepared_content = f"Email reader: {email.reader_email}\n"
    prepared_content += f"Email sender: {email.sender_email}\n"
    prepared_content += f"Email from: {email.from_email}\n"
    prepared_content += f"Email recipients: {', '.join(email.recipient_emails)}\n"
    prepared_content += f"Send time: {email.send_date.isoformat()}\n"
    prepared_content += f"Title: {email.title}\n"
    prepared_content += f"Content:\n{email.content}"

    return prepared_content

def parse_outlook_emails_from_file(filename: str, reader_email: str) -> list[Email]:
    emails: list[Email] = []
    with open(filename, "r", encoding="UTF-8") as f:
        emails_json = json.load(f)
        emails = [Email.from_outlook_json(data, reader_email) for data in emails_json["value"]]
        return emails
