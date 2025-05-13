from llama_cpp import LlamaGrammar
from . import json_schema_to_grammar

__PARSING_PROMPT = \
'''
You are an AI assistant whose job is to examine an email and parse the events in that mail into JSON format.

If no events were identified in the email, output an empty JSON array
Otherwise, for every identified event, you need to create a JSON object. Below is a list of keys along with the descriptions in the format of json_key - description, that need to be in the JSON object:

event_name - string, the title of the event describing the event in a maximum of 20 words
start_date - optional IF event is a deadline; date formatted using ISO 8601 format; only include the timezone if it has been explicitly defined in the email; it is possible that the date is described with words like 'tomorrow', 'in 3 days' etc and you will need to deduce the start date based on the email sending date
end_date - date formatted ISO 8601 format; only include the timezone if it has been explicitly defined in the email; some details might be missing from the end date and you will need do deduce it from the email sending date; if event happens on a single day, treat the end time as the end of the day at 23:59
country - name of the country where an event is taking place; empty string if country is not mentioned
city - name of the city where an event is taking place; empty string if country is not mentioned
address - the street and building number of where the event is taking place; building name if no street is mentioned; empty string if none of the details are mentioned;
room_nr - number of the room the event is taking place; empty string if not specified
tags - a JSON list of tags that best describe what the event is about; empty list if no tags match the event content

Assignable tags are: %s

Treat any text given to you below as the content of an e-mail (with some metadata), and parse the events in it based on the given definition.
If an event's date needs to be confirmed by the reader, then only parse that event if the reader has given confirmation. Otherwise, you should always parse events that happen regardless of reader confirmation.
'''

def format_event_parse_prompt(tags: list[str]) -> str:
    return __PARSING_PROMPT % ", ".join(tags)

def get_parse_output_grammar(tags: list[str]) -> LlamaGrammar:
    date_regex = "[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])"
    time_regex = "([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    timezone_regex = "(Z|(\\+|-)([01][0-9]|2[0-3]):[0-5][0-9])"
    datetime_regex = f"({date_regex}(T{time_regex}({timezone_regex})?)?)"

    grammar_obj = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "event_name": {
                    "type": "string",
                },
                "start_date": {
                    "type": ["string", "null"],
                    "pattern": f"^{datetime_regex}?$"
                },
                "end_date": {
                    "type": "string",
                    "pattern": f"^{datetime_regex}$"
                },
                "country": {
                    "type": "string",
                },
                "city": {
                    "type": "string",
                },
                "address": {
                    "type": "string",
                },
                "room": {
                    "type": "string",
                },
                "tags": {
                    "type": "array",
                    "items": {
                        "enum": tags
                    },
                    "maxItems": len(tags)+1
                },
            },
            "required": [
                "event_name", 
                "start_date", 
                "end_date", 
                "country", 
                "city", 
                "address", 
                "room", 
                "tags"
            ]
        }
    }

    return LlamaGrammar.from_string(
        json_schema_to_grammar.generate(grammar_obj)
    )
    