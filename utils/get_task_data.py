import pandas as pd
import os
from datetime import datetime
import subjectid_to_seqid as s2s

def get_summaries_data(summaries_path: str) -> pd.DataFrame:
    data = pd.DataFrame()
    for file in os.listdir(summaries_path):
        summary_path = os.path.join(summaries_path, file)
        summary = pd.read_csv(summary_path)
        data = pd.concat([data, summary])
    return data

def get_summaries_paths(glucklab_path: str) -> list:
    summaries_paths = []
    for dirpath, dirname, file in os.walk(glucklab_path):
        if dirpath.endswith("summaries") and "fmri" not in dirpath:
            summaries_paths.append(dirpath)
    return summaries_paths

def get_tasks_data(summaries_paths: str) -> pd.DataFrame:
    tasks_data = pd.DataFrame()
    for summaries_path in summaries_paths:
        summaries_data = get_summaries_data(summaries_path)
        tasks_data = pd.concat([tasks_data, summaries_data])
    return tasks_data

def rename_columns(tasks_data: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "subject": "subjectid",
        "experiment": "redcap_repeat_instrument",
        "date": "date",
        "train_accuracy": "choosetrainingaccavg",
        "train_errors": "choosetrainingnerr",
        "train_avg_rt": "choosetrainingrtavg",
        "probe_accuracy": "chooseprobeaccavg",
        "probe_errors": "chooseprobenerr",
        "probe_rt_avg": "chooseprobertavg",
        "acquisition": "facquisition",
        "acquisition_trials": "facquisition_trials",
        "retention": "fretention",
        "generalization": "fgen"
    }
    tasks_data = tasks_data.rename(columns=rename_map)
    tasks_data = tasks_data.drop(columns=[col for col in tasks_data.columns if col not in rename_map.values()])
    return tasks_data

def fix_instruments(tasks_data: pd.DataFrame) -> pd.DataFrame:
    tasks_data = tasks_data.replace("Choose_34", "choose_task")
    tasks_data = tasks_data.replace("Fish15", "fish_task")
    return tasks_data

def fix_dates(tasks_data: pd.DataFrame) -> pd.DataFrame:
    input_date_format = "%A, %B %d, %Y"
    tasks_data["date"] = tasks_data["date"].apply(lambda date: date.strip("\""))
    tasks_data["date"] = tasks_data["date"].apply(lambda date: datetime.strptime(date, input_date_format))
    return tasks_data

def add_task_specific_doadmin(tasks_data: pd.DataFrame) -> pd.DataFrame:
    choose_doadmin = []
    fish_doadmin = []
    for index, row in tasks_data.iterrows():
        if row["redcap_repeat_instrument"] == "choose_task":
            choose_doadmin.append(row["date"])
            fish_doadmin.append(None)
        elif row["redcap_repeat_instrument"] == "fish_task":
            choose_doadmin.append(None)
            fish_doadmin.append(row["date"])
        else:
            choose_doadmin.append(None)
            fish_doadmin.append(None)

    tasks_data["choose_doadmin"] = choose_doadmin
    tasks_data["fish_doadmin"] = fish_doadmin
    tasks_data = tasks_data.drop(columns="date")
    return tasks_data

def add_seqid_and_instance(tasks_data: pd.DataFrame) -> pd.DataFrame:
    tasks_data["seqid"] = tasks_data["subjectid"].apply(s2s.get_seqid)
    tasks_data["redcap_repeat_instance"] = tasks_data["subjectid"].apply(s2s.get_instance_number)
    tasks_data = tasks_data[list(tasks_data.columns[-2:]) + list(tasks_data.columns[:-2])]
    tasks_data = tasks_data.drop(columns="subjectid")
    return tasks_data


def main():
    glucklab_path = input("Enter the path to the GluckLab folder: ")
    summaries_paths = get_summaries_paths(glucklab_path)
    tasks_data = get_tasks_data(summaries_paths)
    tasks_data = rename_columns(tasks_data)
    tasks_data = fix_instruments(tasks_data)
    tasks_data = fix_dates(tasks_data)
    tasks_data = add_seqid_and_instance(tasks_data)
    tasks_data = add_task_specific_doadmin(tasks_data)
    tasks_data["chooseprobenerr"] = tasks_data["chooseprobenerr"].astype(str).str.replace(r"\.0", "", regex=True)
    tasks_data["chooseprobenerr"] = tasks_data["chooseprobenerr"].str.replace("nan", "")
    tasks_data["choosetrainingnerr"] = tasks_data["choosetrainingnerr"].astype(str).str.replace(r"\.0", "", regex=True)
    tasks_data["choosetrainingnerr"] = tasks_data["choosetrainingnerr"].str.replace("nan", "")
    tasks_data["facquisition_trials"] = tasks_data["facquisition_trials"].astype(str).str.replace(r"\.0", "", regex=True)
    tasks_data["facquisition_trials"] = tasks_data["facquisition_trials"].str.replace("nan", "")
    tasks_data.to_csv("generalization_data.csv", index=False)
    

if __name__ == "__main__":
    main()