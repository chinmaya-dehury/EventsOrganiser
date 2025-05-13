# Generates a dataset of parsed event responses 
# from the LLM output, which are used to compare the LLM's accuracy
# against expected responses

import os, json
import dataclasses
from dataclasses import dataclass
import statistics
from typing import TypeVar, Callable

RESPONSES_LOCATION = "./_after_finetune_responses"
GRADED_RESPONSES_LOCATION = "./_graded_before_finetune_responses"
INPUT_OUTPUT_SEPARATOR = "!<-=->!" # for simplicity we use text files which contain stuff separated by this token (input above, output below)
                                   # this will also be the exact same separator for output, which contains generated stuff

T = TypeVar("T")

@dataclass
class ResponseData:
    file_location: str
    filename: str
    
    mail_data: str
    categories: list[str]
    expected_response: list[dict]
    llm_responses: list[list[dict]]

@dataclass 
class GradeForSingleEvent:
    llm_generated_event: dict

    should_be_graded: bool = True
    event_name_grade: float = 0.0
    start_date_grade: float = 0.0
    end_date_grade: float = 0.0
    country_grade: float = 0.0
    city_grade: float = 0.0
    address_grade: float = 0.0
    room_grade: float = 0.0
    categories_grade: float = 0.0

@dataclass
class GradeForResponse:
    llm_response: list[dict]

    grades_for_each_event: list[GradeForSingleEvent]
    event_finding_grade: float = 0.0

@dataclass
class ManualGradingData:
    expected_response: list[dict]
    exemplars: list[GradeForResponse]

def read_response_file(loc: str) -> ResponseData:
    with open(f"{loc}", "r", encoding="UTF-8") as f:
        content = f.read().split(INPUT_OUTPUT_SEPARATOR)

        return ResponseData(
            file_location=loc,
            filename=os.path.basename(loc),
            
            mail_data=content[0],
            categories=json.loads(content[1]),
            expected_response=json.loads(content[2]),
            llm_responses=[json.loads(resp) for resp in content[3:]]
        )

def read_grading_file(loc: str) -> GradeForResponse:
    with open(f"{loc}", "r", encoding="UTF-8") as f:
        json_data = json.load(f)

        grading_data = ManualGradingData(
            json_data["expected_response"],
            []
        )

        for exemplar_json in json_data["exemplars"]:
            exemplar = GradeForResponse(
                exemplar_json["llm_response"],
                [],
                exemplar_json["event_finding_grade"]
            )

            for event_grade_json in exemplar_json["grades_for_each_event"]:
                exemplar.grades_for_each_event.append(
                    GradeForSingleEvent(**event_grade_json)
                )

            grading_data.exemplars.append(exemplar)

    return grading_data

def read_grading_file_with_metadata(loc: str) -> tuple[str, GradeForResponse]:
    return read_grading_file(loc), os.path.basename(loc)

def read_all_data(dir: str, reader_func: Callable[[str], T]) -> list[T]:
    metadatas = []
    for filename in os.listdir(dir):
        obj_loc = f"{dir}/{filename}"

        if(not os.path.isfile(obj_loc)):
            metadatas += read_all_data(obj_loc)
        elif(filename != "SYS_PROMPT.txt"):
            metadatas.append(
                reader_func(f"{dir}/{filename}")
            )

    return metadatas

def print_response(custom_text: str, events_response: list[dict]):
    print(f"---------------{custom_text} START-----------------")
    print(json.dumps(events_response, indent="\t"))
    print(f"---------------{custom_text} END-------------------")

def manually_grade(response_data: ResponseData) -> ManualGradingData:
    grading = ManualGradingData(
        expected_response=response_data.expected_response,
        exemplars=[]
    )

    for i, llm_response in enumerate(response_data.llm_responses):
        response_grade = GradeForResponse(
            llm_response,
            grades_for_each_event=[]
        )

        if(len(response_data.expected_response) == 0 and len(llm_response) != 0
           or len(response_data.expected_response) > 0 and len(llm_response) == 0
           ):
            print(f"Skipping exemplar {i+1} for {response_data.filename} because LLM generated events when none are supposed to be there (or vice versa)")
        
        elif(len(response_data.expected_response) == 0 and len(llm_response) == 0):
            print(f"Skipping correct exemplar {i+1} for {response_data.filename}, LLM generated correct answer")
            response_grade.event_finding_grade = 1.0
        
        else:            
            for i, event in enumerate(llm_response):
                print_response("EXPECTED RESULT", response_data.expected_response)
                print_response(f"GENERATED EVENT ({i+1}/{len(llm_response)})", event)

                event_grade = GradeForSingleEvent(event)
                while True:
                    try:
                        event_grade.should_be_graded = True if input("Should this event be graded (y/n)? ") == "y" else False
                        if(event_grade.should_be_graded == True):
                            event_grade.event_name_grade = float(input("Grade the accuracy of 'event_name' (0.0 -> 1.0): "))
                            event_grade.start_date_grade = float(input("Grade the accuracy of 'start_date' (0.0 -> 1.0): "))
                            event_grade.end_date_grade = float(input("Grade the accuracy of 'end_date' (0.0 -> 1.0): "))
                            event_grade.country_grade = float(input("Grade the accuracy of 'country' (0.0 -> 1.0): "))
                            event_grade.city_grade = float(input("Grade the accuracy of 'city' (0.0 -> 1.0): "))
                            event_grade.address_grade = float(input("Grade the accuracy of 'address' (0.0 -> 1.0): "))
                            event_grade.room_grade = float(input("Grade the accuracy of 'room' (0.0 -> 1.0): "))
                            event_grade.categories_grade = float(input("Grade the accuracy of 'tags' (0.0 -> 1.0): "))
                        break

                    except KeyboardInterrupt:
                        raise KeyboardInterrupt
                    except:
                        continue
                response_grade.grades_for_each_event.append(event_grade)

            response_grade.event_finding_grade = float(input("Grade the accuracy of LLM finding correct events (0.0 -> 1.0, correct ÷ total): "))

        grading.exemplars.append(response_grade)
    
    return grading

def add_manual_grading_for_everything(responses: list[ResponseData]):
    for i, response in enumerate(responses):
        grading = manually_grade(response)

        with open(f"{GRADED_RESPONSES_LOCATION}/{response.filename}", "w", encoding="UTF-8") as f:
            f.write(json.dumps(dataclasses.asdict(grading), indent="\t"))
            print(f"Saved grade to file {GRADED_RESPONSES_LOCATION}/{response.filename}")

        print(f"Progress: {i+1}/{len(responses)}")
        print("")
        print("")

def generate_average_grades(graded_emails: list[ManualGradingData]):
    grading_data = {
        # Each list has the average grade for all responses in an exemplar (for events that should be graded anyway)
        "no_events": {
            "event_finding_grade": []
        },
        "with_events": {
            "event_finding_grade": [],

            "event_name_grade": [],
            "start_date_grade": [],
            "end_date_grade": [],
            "country_grade": [],
            "city_grade": [],
            "address_grade": [],
            "room_grade": [],
            "categories_grade": [],
        }
    }

    for graded_email_llm_response in graded_emails:
        for graded_one_generated_response in graded_email_llm_response.exemplars:
            if(len(graded_email_llm_response.expected_response) == 0):
                grading_data["no_events"]["event_finding_grade"].append(graded_one_generated_response.event_finding_grade)
            else:
                grading_data["with_events"]["event_finding_grade"].append(graded_one_generated_response.event_finding_grade)

                grading_data["with_events"]["event_name_grade"].extend(
                    [item.event_name_grade for item in graded_one_generated_response.grades_for_each_event]
                )
                grading_data["with_events"]["start_date_grade"].extend(
                    [item.start_date_grade for item in graded_one_generated_response.grades_for_each_event]
                )
                grading_data["with_events"]["end_date_grade"].extend(
                    [item.end_date_grade for item in graded_one_generated_response.grades_for_each_event]
                )
                grading_data["with_events"]["country_grade"].extend(
                    [item.country_grade for item in graded_one_generated_response.grades_for_each_event]
                )
                grading_data["with_events"]["city_grade"].extend(
                    [item.city_grade for item in graded_one_generated_response.grades_for_each_event]
                )
                grading_data["with_events"]["address_grade"].extend(
                    [item.address_grade for item in graded_one_generated_response.grades_for_each_event]
                )
                grading_data["with_events"]["room_grade"].extend(
                    [item.room_grade for item in graded_one_generated_response.grades_for_each_event]
                )
                grading_data["with_events"]["categories_grade"].extend(
                    [item.categories_grade for item in graded_one_generated_response.grades_for_each_event]
                )

    # floats between 0.0 -> 1.0 representing 0% to 100%
    print("-----------NO EVENTS STATS-----------")
    print("event_finding_grade: ", statistics.mean(grading_data["no_events"]["event_finding_grade"]))
    print("----------WITH EVENTS STATS----------")
    print("event_finding_grade: ", statistics.mean(grading_data["with_events"]["event_finding_grade"]))
    print("event_name_grade: ", statistics.mean(grading_data["with_events"]["event_name_grade"]))
    print("start_date_grade: ", statistics.mean(grading_data["with_events"]["start_date_grade"]))
    print("end_date_grade: ", statistics.mean(grading_data["with_events"]["end_date_grade"]))
    print("country_grade: ", statistics.mean(grading_data["with_events"]["country_grade"]))
    print("city_grade: ", statistics.mean(grading_data["with_events"]["city_grade"]))
    print("address_grade: ", statistics.mean(grading_data["with_events"]["address_grade"]))
    print("room_grade: ", statistics.mean(grading_data["with_events"]["room_grade"]))
    print("categories_grade: ", statistics.mean(grading_data["with_events"]["categories_grade"]))

    all_correct_probability = statistics.mean(grading_data["with_events"]["event_finding_grade"]) \
    * statistics.mean(grading_data["with_events"]["event_name_grade"]) \
    * statistics.mean(grading_data["with_events"]["start_date_grade"]) \
    * statistics.mean(grading_data["with_events"]["end_date_grade"]) \
    * statistics.mean(grading_data["with_events"]["country_grade"]) \
    * statistics.mean(grading_data["with_events"]["city_grade"]) \
    * statistics.mean(grading_data["with_events"]["address_grade"]) \
    * statistics.mean(grading_data["with_events"]["room_grade"]) \
    * statistics.mean(grading_data["with_events"]["categories_grade"])
    print(f"GENERAL GRADE (P that all of the above are correct): {all_correct_probability}")

#generated_responses = read_all_data(RESPONSES_LOCATION, read_response_file)
#add_manual_grading_for_everything(generated_responses)

graded_email_responses = read_all_data(GRADED_RESPONSES_LOCATION, read_grading_file)
generate_average_grades(graded_email_responses)