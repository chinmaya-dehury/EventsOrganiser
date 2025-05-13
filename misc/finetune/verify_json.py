import os, json, traceback

def verify_json(dir):
    if(os.path.isfile(dir)):
        try:
            with open(dir, encoding="UTF-8") as f:
                content = f.read().split("!<-=->!")
                d = json.loads(content[3].strip())
        except:
            print(traceback.format_exc())
            print(f"JSON error in file {dir}")
            
        return
            
    for file in os.listdir(dir):
        verify_json(f"{dir}/{file}")
                
verify_json("./training_data/val/ut/")