# Stats about the languages in the email content
# and the amount of emails with events & no events

# Useful to try and balance out the dataset

import email_data
from finetune import read_prompt_file, TrainingData

from collections import defaultdict
import os
import langdetect

def get_languages(metadata: TrainingData) -> str:
    mail = email_data.str_to_mail(metadata.mail_data, "")
    detected_languages = langdetect.detect_langs(mail.content)

    language_names = [lang.lang for lang in detected_languages if lang.prob > 0.2]
    language_names.sort()
    return ",".join(language_names)

def get_language_stats(dir: str) -> defaultdict:
    stats = defaultdict(int)

    for obj in os.listdir(dir):
        obj_path = f"{dir}/{obj}"
        if(not os.path.isfile(obj_path)):
            dir_stats = get_language_stats(obj_path)
            for key in dir_stats.keys():
                stats[key] += dir_stats[key]
        else:
            language = get_languages(read_prompt_file(obj_path))
            if(language == "en,et" or language == "et,en"):
                print(obj_path)

            stats[language] += 1

    return stats

def get_event_count_stats(dir: str) -> defaultdict:
    stats = {
        "none": 0,
        "1+": 0
    }
    for obj in os.listdir(dir):
        obj_path = f"{dir}/{obj}"
        if(not os.path.isfile(obj_path)):
            dir_stats = get_event_count_stats(obj_path)
            for key in dir_stats.keys():
                stats[key] += dir_stats[key]
        else:
            if(obj.startswith("0")):
               stats["none"] += 1
            else:
               stats["1+"] += 1

    return stats

print(get_language_stats("training_data/train"))
print(get_event_count_stats("training_data/train"))