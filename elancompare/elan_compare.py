import argparse
import contextlib
import os.path
from io import StringIO

import pandas
import pympi


def main():
    parser = argparse.ArgumentParser(
        "elan-compare",

        usage="e.g. elan-compare sandwiches_MY_complete sandwiches_SH_1.25.22 comparison.csv",

        description="For two directories containing ELAN .eaf files, compare the transcripts in those files "
                    "which have matching file names."
    )
    parser.add_argument("dir_a", help="The first directory containing .eaf files")
    parser.add_argument("dir_b", help="The second directory containing .eaf files")
    parser.add_argument("csv_out", help="Where to write the .csv with all the comparisons")
    args = parser.parse_args()
    compare(dir_a=args.dir_a, dir_b=args.dir_b, csv_out=args.csv_out)


def compare(dir_a, dir_b, csv_out):
    files_a = set(f for f in os.listdir(dir_a) if f.endswith(".eaf"))
    files_b = set(f for f in os.listdir(dir_b) if f.endswith(".eaf"))
    intersection = sorted(files_a.intersection(files_b))
    file_results = []
    for file in intersection:
        file_a = os.path.join(dir_a, file)
        file_b = os.path.join(dir_b, file)
        session_data_my = read_elan_file(file_a)
        session_data_sh = read_elan_file(file_b)
        combined = pandas.concat((session_data_my, session_data_sh), keys=[dir_a, dir_b], axis=1)
        combined = combined.reorder_levels((1, 0), axis=1)  # Make the linguistic type the first of the multi-column
        combined = combined[session_data_my.columns] # This orders the columns so the linguistic tiers are grouped
        file_results.append(combined)
    all_results = pandas.concat(file_results)
    all_results.columns = [f"{linguistic_type} ({dir_name})" for linguistic_type, dir_name in all_results.columns]
    if csv_out.endswith(".xlsx"):
        all_results.reset_index().to_excel(csv_out, engine="openpyxl", index=False)
    else:
        all_results.to_csv(csv_out)


def read_elan_file(filename):
    participant_id, file_extension = os.path.basename(filename).split(".")
    with contextlib.redirect_stdout(StringIO()):  # pympi gives warnings on any ELAN file not marked version 2.8/2.9.
        eaf = pympi.Elan.Eaf(filename)
    rows = []
    for tier_name in eaf.tiers:
        if "(INV)" in tier_name:
            speaker_label = "INV"
        else:
            speaker_label = "PAR"
        linguistic_type = eaf.tiers[tier_name][2]['LINGUISTIC_TYPE_REF']
        if len(eaf.tiers[tier_name][0]) > 0:
           tier_data = eaf.tiers[tier_name][0]
           for annotation_id in tier_data:
               timestamp_id_start, timestamp_id_end, transcript, _ = tier_data[annotation_id]
               if transcript.strip() == "":
                   continue
               row = {
                   "participant_id": participant_id,
                   "annotation_id": int(annotation_id.replace("a", "")),
                   "speaker_label": speaker_label,
                   "type": linguistic_type,
                   "transcript": transcript.strip()
               }
               rows.append(row)

        elif len(eaf.tiers[tier_name][1]) > 1:
            tier_data = eaf.tiers[tier_name][1]
            for annotation_id in tier_data:
                parent_annotation_id, transcript, _, _ = tier_data[annotation_id]
                if transcript.strip() == "":
                    continue
                row = {
                    "participant_id": participant_id,
                    "annotation_id": int(parent_annotation_id.replace("a", "")),
                    "speaker_label": speaker_label,
                    "type": linguistic_type,
                    "transcript": transcript.strip()
                }
                rows.append(row)

    df = pandas.DataFrame(rows)
    df = df.set_index(["participant_id", "annotation_id", "speaker_label"])
    df = pandas.pivot(df, columns="type").sort_index()
    df = df.droplevel(0, axis=1)  # Get rid of the "transcript" column name.
    return df


if __name__ == '__main__':
    main()