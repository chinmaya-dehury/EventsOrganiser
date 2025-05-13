from datetime import datetime, timedelta, date, time
from dateutil import parser
from dataclasses import dataclass

CONTAINER_LOGS_FILE = "./container_logs_50/merged.log"
TEST_LOGS_FILE = "performance_test_50.log" #"performance_test.log"

@dataclass
class SentEmailData:
    mail_id: str
    sent_date: datetime | None = None
    parse_started_date: datetime | None = None
    parse_ended_date: datetime | None = None

# Returns sorted performance data based on the send date
def get_parsing_performance_data() -> list[SentEmailData]:
    data: dict[str, SentEmailData] = {}

    with open(TEST_LOGS_FILE, "r", encoding="UTF-8") as f:
        for line in f:
            if("; http" not in line):
                continue

            parts = line.split(" ")
            sent_date = " ".join(parts[1:5])

            mail_id = parts[5].replace(";", "").strip()
            sent_date = parser.parse(sent_date)

            data[mail_id] = SentEmailData(
                mail_id, sent_date
            )

    # read in parse start data and end data
    with open(CONTAINER_LOGS_FILE, "r", encoding="UTF-8") as f:
        for line in f:
            parts = line.split(" ")
            mail_id = parts[-1].strip() # might not be mail id but it doesn't matter for the following check
            if(mail_id not in data):
                continue

            if("New e-mail" in line):
                data[mail_id].parse_started_date = parser.parse(" ".join(parts[1:5]))
            elif("E-mail parsing finished" in line):
                data[mail_id].parse_ended_date = parser.parse(" ".join(parts[1:5]))

    # data validation, print out issues

    filtered_data = []
    for mail_id, mail_parsing_info in data.items():
        if(mail_parsing_info.parse_started_date > mail_parsing_info.parse_ended_date):
            print(f"Mail ID {mail_id} has parsing start date set to after the end date, filtering it")
            continue

        if(mail_parsing_info.parse_started_date == None):
            print(f"Mail ID {mail_id} has no parsing start date, filtering it")
            continue

        if(mail_parsing_info.parse_ended_date == None):
            print(f"Mail ID {mail_id} has no parsing end date, filtering it")
            continue

        filtered_data.append(mail_parsing_info)

    return sorted(filtered_data, key=lambda val: val.sent_date)

def get_entire_parsing_duration(parsing_performance_data: list[SentEmailData]):
    return parsing_performance_data[-1].parse_ended_date - parsing_performance_data[0].sent_date

def generate_waiting_time_before_email_processed_graph(
        parsing_performance_data: list[SentEmailData],
        time_between_averages: str = "1min"
        ):
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.ticker as tkr
    import matplotlib.dates as md

    def y_formatter(seconds: float, pos):
        timedelta_ = pd.Timedelta(seconds, "ns")

        hours = timedelta_.total_seconds() // 3600
        minutes = (timedelta_.total_seconds() % 3600) // 60
        return f"{int(hours):02}:{int(minutes):02}"
    y_fmt = tkr.FuncFormatter(y_formatter)

    parsing_performance_data = sorted(parsing_performance_data, key=lambda val: val.sent_date)
    waiting_started = [data.sent_date for data in parsing_performance_data]
    email_mq_idle_duration = [
        (data.parse_started_date - waiting_started[i]) for i, data in enumerate(parsing_performance_data)
    ]

    processing_started_in_day_timedelta = datetime.combine(date.min, waiting_started[0].time()) - datetime.min

    df = pd.DataFrame({
        "Processing start time": waiting_started,
        "Processing duration": email_mq_idle_duration
    })
    df["Processing start time"] = pd.to_datetime(
        df["Processing start time"].apply(lambda x: x - processing_started_in_day_timedelta) # normalize X-axis to start with 00:00:00
    )

    df.set_index(pd.DatetimeIndex(df["Processing start time"]), inplace=True)
    #df = df.resample(time_between_averages).mean() # avoid PC crashing....

    drawn_plot = df.plot(
        y="Processing duration", 
        xlabel="Aeg alates testi käivitamisest (tundides)", 
        ylabel="Ühe e-kirja ooteaeg järjekorras (tundides)",
        title="Testprogrammi saadetud e-kirjade ooteajad töötlusjärjekorras"
    )
    drawn_plot.xaxis.set_major_formatter(md.DateFormatter("%H:%M"))
    drawn_plot.yaxis.set_major_formatter(y_fmt)
    drawn_plot.yaxis.set_major_locator(tkr.MultipleLocator(3600 * 2 * 1_000_000_000)) # sets y axis size... retarded but works

    drawn_plot.get_legend().remove()
    plt.show()

def generate_parse_time_histogram(
        parsing_performance_data: list[SentEmailData],
        grouping_interval_seconds: float = 30.0,
        max_interval: float = 270
        ):
    import matplotlib.pyplot as plt
    from matplotlib.axis import Axis
    import matplotlib.ticker as tkr

    parsing_times_sec: list[float] = []
    for performance_data in parsing_performance_data:
        parsing_times_sec.append((performance_data.parse_ended_date - performance_data.parse_started_date).total_seconds())
    
    print("Average parsing time (sec): ", sum(parsing_times_sec) / len(parsing_times_sec))

    min_parse_time = min(parsing_times_sec)
    max_parse_time = max(parsing_times_sec)
    intervals: list[tuple[int, int]] = []
    y_values: list[float] = [0]

    # find min range that has some data
    for i in range(1000):
        if(i*grouping_interval_seconds <= min_parse_time < (i+1)*grouping_interval_seconds):
            intervals.append((i*grouping_interval_seconds, (i+1)*grouping_interval_seconds))
            break

    if(not (intervals[0][0] <= max_parse_time < intervals[0][1])):
        for i in range(i+1, 1000):
            intervals.append((i*grouping_interval_seconds, (i+1)*grouping_interval_seconds))

            if((i*grouping_interval_seconds <= max_parse_time < (i+1)*grouping_interval_seconds)
               or (i*grouping_interval_seconds <= max_interval < (i+1)*grouping_interval_seconds)
               ):
                break

    y_values *= len(intervals)
    for parsing_time in parsing_times_sec:
        interval_idx = int(parsing_time / grouping_interval_seconds)
        if(interval_idx >= len(y_values) and max_interval > 0.0):
            interval_idx = len(y_values)-1

        y_values[interval_idx] += 1

    x_values = [
        f"[{int(interval_start)}, {int(interval_end)})" for interval_start, interval_end in intervals
    ]
    if(max_interval > 0.0):
        first_interval = int(x_values[-1].split(", ")[0].replace("[", ""))
        x_values[-1] = f"[{first_interval}, ∞)"


    fig, ax = plt.subplots()
    ax.bar(
        x_values,
        y_values,
    )
    Axis.set_major_locator(ax.yaxis, tkr.MultipleLocator(50))

    plt.xlabel("Töötlemisaja vahemik (sekundites)")
    plt.ylabel("E-kirjade arv")
    plt.title("E-kirjade jaotus töötlemisaja põhjal")

    plt.show()

data = get_parsing_performance_data()

#print(get_entire_parsing_duration(data))
generate_waiting_time_before_email_processed_graph(data)
#generate_parse_time_histogram(data)