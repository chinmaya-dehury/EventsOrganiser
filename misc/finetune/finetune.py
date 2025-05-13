import dotenv
dotenv.load_dotenv(".env")
import json
import copy
import random

from dataclasses import dataclass
import torch, os, datasets, unsloth
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel
import unsloth.save

import email_data
from email_data import Email

DATASET_LOC = "./training_data/" 
INPUT_OUTPUT_SEPARATOR = "!<-=->!" # treeningandmete & testandmestiku failis erinevate sektsioonide eraldaja
MAX_SEQ_LENGTH = 32768 # keelemudeli maksimaalne genereeritav tekstipikkus treenimise ajal
BATCH_SIZE = 8 # e-kirjade arv, mis keelemudelile korraga antakse
with open(f"{DATASET_LOC}/SYS_PROMPT.txt", "r", encoding="UTF-8") as f:
    SYS_PROMPT = f.read()

@dataclass
class TrainingData:
    comment: str
    categories: list[str]
    reader_email: str
    mail_data: str
    expected_output: list[dict[str]]

def read_prompt_file(loc: str) -> TrainingData:
    with open(f"{loc}", "r", encoding="UTF-8") as f:
        content = f.read().split(INPUT_OUTPUT_SEPARATOR)

        return TrainingData(
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
        else:
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

def generate_chats_from_prompts(metadatas: list[TrainingData]) -> list[str]:
    # siin teisendatakse
    global SYS_PROMPT

    # kõikide treeningandmete põhjal leitakse kõik kategooriad, mis
    # lisatakse ühte hulka
    # seega jäävad alles ainult unikaalsed kategooriad
    default_categories = get_all_unique_categories(metadatas)

    chats = []
    for metadata in metadatas:
        email = email_data.str_to_mail(metadata.mail_data, metadata.reader_email)

        # järgnevalt luuakse ühest treeninandme failist 1 viip keelemudelile
        # kusjuures kategooriate järjekord muudetakse ära, kuna keelemudel
        # võib järjekorra põhjal leida mingeid seoseid sündmustega, mis
        # keelemudeli tööd sündmuste leidmisel halvavad
        sys_part = {
            "role": "system",
            "content": ""
        }
        categories = metadata.categories.copy()
        if(len(categories) == 0):
            categories = default_categories.copy()
        random.shuffle(categories)

        sys_part["content"] = SYS_PROMPT % ",".join(categories)

        user_part = {
            "role": "user",
            "content": email_data.format_email_for_llm(email)
        }
        response_part = {
            "role": "assistant",
            "content": ""
        }

        chat_ = {
            "messages": [
                sys_part,
                user_part,
                response_part
            ]
        }

        chat_["messages"][2]["content"] = json.dumps(metadata.expected_output)
        chats.append(
            copy.deepcopy(chat_)
        )

    return chats

def begin_training():
    def formatting_prompts_func(data):
        nonlocal tokenizer 
    
        convos = data["messages"]
        # see teisendab HuggingFace'i conversational formaadi viiba tavatekstiks, milles on spetsiaalsete sõnedega (nagu "<|start_header_id|>system<|end_header_id|>", tähistab süsteemiviiba osa pikemas viibas) tähistatud erinevaid rolle viibas
        texts = [tokenizer.apply_chat_template(convo, tokenize = False, add_generation_prompt = False) for convo in convos]
        return { "text" : texts, }

    # laeb nii mudeli kui ka teksti tokeniseerija
    # paraku on see vaja hiljem unsloth teegiga uuesti laadida
    model, tokenizer = FastLanguageModel.from_pretrained(
        "./trainable_llm/llama3.2-3b-instruct",
        max_seq_length=MAX_SEQ_LENGTH,
        load_in_4bit=False,
        load_in_8bit=True, # originaalne keelemudel (täpsemalt selle kaalud, aktivatsioonid jms) kvantiseeritakse 8-bitiste täisarvude peale
        dtype=torch.bfloat16 # PEFT kihi mudeli puhul kasutatakse 16-bitist brainfloati andmetüüpi, samas kui kvantiseeritud mudeli puhul jäävad andmetüübid ikka 8-bitise täisarvu peale
    )

    # PEFT = performance-efficient fine tuning
    # get_peft_model loob enne viimast keelemudeli kihti paar lisakihti
    # need lisakihid on treenitavad, samas kui keelemudeli originaalseid kihte ei treenita
    model = FastLanguageModel.get_peft_model( # argumendid on jäetud samaks, mis olid unslothi Llama 3.2 peenhäälestamise juhendis https://colab.research.google.com/github/unslothai/notebooks/blob/main/nb/Llama3.2_(1B_and_3B)-Conversational.ipynb
        model,
        r = 16, # Choose any number > 0 ! Suggested 8, 16, 32, 64, 128
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj",],
        lora_alpha = 16,
        lora_dropout = 0, # Supports any, but = 0 is optimized
        bias = "none",    # Supports any, but = "none" is optimized
        # [NEW] "unsloth" uses 30% less VRAM, fits 2x larger batch sizes!
        use_gradient_checkpointing = "unsloth", # True or "unsloth" for very long context
        random_state = 3407,
        use_rslora = False,  # We support rank stabilized LoRA
        loftq_config = None, # And LoftQ
    )
    # see chat template sobib kõigile Llama 3nda generatsiooni keelemudelitele
    tokenizer = unsloth.chat_templates.get_chat_template(
        tokenizer,
        chat_template = "llama-3.1",
    )
    training_prompts = read_all_prompts(f"{DATASET_LOC}/train")
    validation_prompts = read_all_prompts(f"{DATASET_LOC}/train")

    # treeningandmed teisendatakse HuggingFace'i conversational formaati
    # ning peale seda teisendatakse see HuggingFace'i standard formaati
    training_ds = datasets.Dataset.from_list(generate_chats_from_prompts(training_prompts))
    training_ds = training_ds.map(formatting_prompts_func, batched=True)
    # sama tehakse testandmestikuga
    validation_ds = datasets.Dataset.from_list(generate_chats_from_prompts(validation_prompts))
    validation_ds = validation_ds.map(formatting_prompts_func, batched=True)

    trainer = SFTTrainer(
        model=model, 
        tokenizer=tokenizer,
        train_dataset=training_ds, 
        eval_dataset=validation_ds,
        args=TrainingArguments(
            # need 2 argumenti panevad SFTTraineri salvestama keelemudeli (täpsemalt PEFT vahekihi)
            # ainult siis, kui selle kaofunktsiooni väärtus on testandmetel
            # väiksem võrreldes eelmiste epohhidega
            # sedasi salvestatakse selline mudel, mis ei ole treeningandmetel ülesobitatud
            save_strategy="best",
            metric_for_best_model="eval_loss",
            # korraga treenitakse keelemudelit 8 e-kirja peal
            # see hoiab mälu kokku, kuid siiski on ühes 'batchis' on mitu eksemplari
            # mis aitab keelemudelil paremini õppida sündmusi leidma
            # mitu eksemplari
            per_device_train_batch_size = BATCH_SIZE,
            gradient_accumulation_steps = 4,
            num_train_epochs=100.0,
            learning_rate = 2e-4,
            fp16 = not unsloth.is_bfloat16_supported(),
            bf16 = unsloth.is_bfloat16_supported(),
            logging_steps = 1,
            optim = "adamw_8bit",
            weight_decay = 0.01,
            lr_scheduler_type = "linear",
            seed = 3407,
            output_dir = "outputs",
            report_to = "none", # Use this for WandB etc

            # sellega hoitakse natuke VRAMi (graafikakaarti mälu) kokku
            # testandmestiku peal kasutab keelemudel 16-bitiseid floate, mitte 32-bitiseid
            fp16_full_eval = True,
            per_device_eval_batch_size = BATCH_SIZE, 
            # peale igat treeningepohhi testitakse mudelit
            eval_strategy = "epoch"
        )
    )
    trainer.train()

    # salvestab kõige viimase mudeli (mis ei pruugi parim olla)
    unsloth.save.unsloth_save_pretrained_merged(model, "./outputs/merged_model", tokenizer)
    #unsloth.save.unsloth_save_pretrained_gguf(model, "./outputs/gguf", tokenizer)

def merge_lora_checkpoint(checkpoint_dir):
    # see funktsioon liidab treenitud PEFT mudeli kihid ning 
    # originaalse keelemudeli kihid kokku
    lora_model, tokenizer = FastLanguageModel.from_pretrained(
        checkpoint_dir,
        max_seq_length=MAX_SEQ_LENGTH,
        load_in_4bit=False,
        load_in_8bit=True,
        dtype=torch.bfloat16
    )

    unsloth.save.unsloth_save_pretrained_merged(lora_model, "./outputs/merged_model_2025_04_19", tokenizer)

# followed https://huggingface.co/docs/trl/en/sft_trainer#supervised-fine-tuning-trainer
# and https://colab.research.google.com/github/unslothai/notebooks/blob/main/nb/Llama3.2_(1B_and_3B)-Conversational.ipynb
if __name__ == "__main__":
    #merge_lora_checkpoint("./outputs/checkpoint-210")
    begin_training()
