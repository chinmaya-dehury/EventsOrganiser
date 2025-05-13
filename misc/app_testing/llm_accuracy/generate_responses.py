# Generates a dataset of parsed event responses 
# from the LLM output, which are used to compare the LLM's accuracy
# against expected responses

import os, json, random
from dataclasses import dataclass
from includes.model import Llama3Model
from includes.email_data import str_to_mail
import traceback, sys

LLM = Llama3Model("./llm/Llama3.2-3B-Instruct-finetuned-2025-04-19.gguf")
DATASET_LOC = "./_testing_dataset"
OUTPUT_LOC = "./_after_finetune_responses"
INPUT_OUTPUT_SEPARATOR = "!<-=->!" # for simplicity we use text files which contain stuff separated by this token (input above, output below)
                                   # this will also be the exact same separator for output, which contains generated stuff
MAX_SEQ_LENGTH = 32768
ANSWERS_TO_GENERATE = 3 # how many times should the LLM use the same email to find events
with open(f"{DATASET_LOC}/SYS_PROMPT.txt", "r", encoding="UTF-8") as f:
    SYS_PROMPT = f.read()

@dataclass
class TrainingData:
    file_location: str
    filename: str
    comment: str
    categories: list[str]
    reader_email: str
    mail_data: str
    expected_output: list[dict[str]]

def read_prompt_file(loc: str) -> TrainingData:
    with open(f"{loc}", "r", encoding="UTF-8") as f:
        content = f.read().split(INPUT_OUTPUT_SEPARATOR)

        return TrainingData(
            file_location=loc,
            filename=os.path.basename(loc),
            comment=content[0].strip(),
            categories=[category.strip() for category in content[1].split(";") if len(category.strip()) > 0],
            reader_email=content[2],
            mail_data=content[3].strip(),
            expected_output=json.loads(content[4])
        )

def read_all_prompts(dir: str) -> list[TrainingData]:
    metadatas = []
    for filename in os.listdir(dir):
        obj_loc = f"{dir}/{filename}"

        if(not os.path.isfile(obj_loc)):
            metadatas += read_all_prompts(obj_loc)
        elif(filename != "SYS_PROMPT.txt"):
            metadatas.append(
                read_prompt_file(f"{dir}/{filename}")
            )

    return metadatas

def get_all_unique_categories(metadatas: list[TrainingData]) -> list[str]:
    categories = set()
    for metadata in metadatas:
        for tag in metadata.categories:
            if(tag.strip() != ""):
                categories.add(tag)

    return list(categories)

dataset = read_all_prompts(DATASET_LOC)
all_categories = get_all_unique_categories(dataset)

for data in dataset:
    with open(f"{OUTPUT_LOC}/{data.filename}", "w", encoding="UTF-8") as f:
        categories = data.categories.copy()
        if(len(categories) == 0):
            categories = all_categories.copy()

        f.write(data.mail_data)
        f.write(f"\n{INPUT_OUTPUT_SEPARATOR}\n")
        f.write(json.dumps(categories, indent="\t"))

        f.write(f"\n{INPUT_OUTPUT_SEPARATOR}\n")
        f.write(json.dumps(data.expected_output, indent="\t"))

        random.shuffle(categories) # for LLM to get a different order of categories every time

        for _ in range(ANSWERS_TO_GENERATE):
            f.write(f"\n{INPUT_OUTPUT_SEPARATOR}\n")

            while True:
                try:
                    email = str_to_mail(data.mail_data, data.reader_email)
                    response = LLM.parse_events_from_email(email, categories)
                    f.write(json.dumps(response, indent="\t"))
                    break
                except KeyboardInterrupt:
                    sys.exit(0)
                except:
                    traceback.print_exc()
                    print("Redoing this e-mail")
                    continue