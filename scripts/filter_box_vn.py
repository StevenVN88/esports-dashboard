import csv

BOX_IDS = {
    "566396933440625","566400087557233","566531620930673","566466726659185",
    "566930448909425","566471222953073","2921142818243697","760613341299825",
    "2920672854869105",
    "15303162085049457","15303205907137649","15303250064770161","15303275901682801",
    "15303219194692721","15303266170897521","15303296571212913","15303322810778737",
    "15308233569010801",
    "15303182620361841","15303235233711217","15303263754978417","15303289591891057",
    "15303250735858801","15303284223181937","15303309187679345","15303332206019697",
    "15308267660313713"
}

with open(r"D:\EsportsAI\data\match_history_vn.csv", encoding="utf-8") as fin, \
     open(r"D:\EsportsAI\data\box_mh_vn.csv", "w", newline="", encoding="utf-8") as fout:
    reader = csv.reader(fin)
    writer = csv.writer(fout)
    header = next(reader)
    writer.writerow(header)
    for row in reader:
        if row[2] in BOX_IDS:
            writer.writerow(row)

print("Done - saved to box_mh_vn.csv")
