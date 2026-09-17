##----------------- read existing Governor proclamation CSV.----------------------------##

## python update_disaster_data.py 

import pandas as pd
import os
import subprocess


print("\nUpdating SBA data...")

subprocess.run(
    ["python", "run_update.py"],
    cwd=r"..\SBA_Disaster_Tracker",
    check=True
)

print("SBA update complete.")

##------------------make the script read the old registry on future runs--------------------##



registry_file = "output/event_id_registry.csv"

if os.path.exists(registry_file):

    old_registry = pd.read_csv(
        registry_file,
        dtype={"source_id": str}
    )

    print("\nExisting event ID registry loaded.")
    print("Registry rows:", len(old_registry))

else:

    old_registry = pd.DataFrame(
        columns=[
            "source_id",
            "event_id",
            "source"
        ]
    )

    print("\nNo existing registry found.")



    ##--------------make three simple lookup tables from it--------------------##

gov_old_ids = (
    old_registry[
        old_registry["source"] == "Governor"
    ]
    .set_index("source_id")["event_id"]
    .to_dict()
)

print("Governor registry sample:", list(gov_old_ids.items())[:5])

if gov_old_ids:
    first_gov_key = next(iter(gov_old_ids))

    if not first_gov_key.startswith("http"):
        print("OLD Governor registry format detected.")
        gov_old_ids = {}

sba_old_ids = (
    old_registry[
        old_registry["source"] == "SBA"
    ]
    .set_index("source_id")["event_id"]
    .to_dict()
)

fema_old_ids = (
    old_registry[
        old_registry["source"] == "FEMA"
    ]
    .set_index("source_id")["event_id"]
    .to_dict()
)





##----------------------------make new IDs start after the highest old ID------------------------##

if len(old_registry) > 0:

    old_numbers = (
        old_registry["event_id"]
        .str.replace("EID_", "", regex=False)
        .astype(int)
    )

    next_event_number = old_numbers.max() + 1

else:

    next_event_number = 1


print("\nNext new event number:", next_event_number)





###----------------------- Update Governor proclamation data-------------------------##

print("\nUpdating Governor proclamation data...")

subprocess.run(
    ["python", "scraper.py"],
    cwd=r"..\texas_proclamation_tracker",
    check=True
)

print("Governor proclamation update complete.")


##----------- Read Governor proclamation data-----------------------------------##

proclamation = pd.read_csv(
    r"..\texas_proclamation_tracker\data\disaster_proclamations.csv"
)


print("Governor data loaded")
print(proclamation.head())
print("Rows:", len(proclamation))

 


 ##-----------------------------Read SBA data -----------------------------------##


sba = pd.read_csv(r"..\SBA_Disaster_Tracker\Data\SBA_disaster_Final.csv",dtype={"county_fips": str})

print("\nSBA data loaded")
print(sba.head())
print("Rows:", len(sba))



#### Keep only Texas county records ###



sba_tx = sba[sba["state"] == "TX"].copy()

print("\nTexas SBA data loaded")
print(sba_tx.head())
print("Texas rows:", len(sba_tx))




###---------------- add FEMA-------------------------###

import requests

# FEMA Texas data
fema_url = "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries?$filter=state%20eq%20%27TX%27&$orderby=incidentBeginDate%20desc&$top=1000"

response = requests.get(fema_url)

print("\nFEMA API status:", response.status_code)



##-----------------------------FEMA response into a dataframe.-----------------------------------##

fema_json = response.json()

fema = pd.DataFrame(
    fema_json["DisasterDeclarationsSummaries"]
)

print("\nFEMA data loaded")
print(fema.head())
print("Rows:", len(fema))




##-----------------------------clean the FEMA county name so it matches the format-----------------------------------##


fema["county_name"] = (
    fema["designatedArea"]
    .str.replace(" (County)", "", regex=False)
)

print("\nFEMA county names cleaned")
print(fema[["designatedArea", "county_name"]].head())




##-------convert the date columns WHICH need for matching into proper datetime valueS----------##


proclamation["publication_date"] = pd.to_datetime(
    proclamation["publication_date"],
    format="mixed",
    dayfirst=True
)

sba_tx["incident_start_date"] = pd.to_datetime(
    sba_tx["incident_start_date"],
     
)

fema["incidentBeginDate"] = pd.to_datetime(
    fema["incidentBeginDate"]
).dt.tz_localize(None)

print("\nDate columns converted")
print(proclamation["publication_date"].dtype)
print(sba_tx["incident_start_date"].dtype)
print(fema["incidentBeginDate"].dtype)




##----------------------------Create smaller tables for matching-----------------------------------##


gov_simple = proclamation[
    ["disaster_id", "publication_date", "disaster_type", "county", "title"]
].copy()

sba_simple = sba_tx[
    ["disaster_number", "incident_start_date", "disaster_description", "county_name"]
].copy()

fema_simple = fema[
    ["disasterNumber", "incidentBeginDate", "incidentType", "county_name"]
].copy()

print("\nMatching tables created")
print("Governor:", gov_simple.shape)
print("SBA:", sba_simple.shape)
print("FEMA:", fema_simple.shape)




##-----create one simple disaster-type matcher to reduce them into simple categories----------------------------##



def simple_type(text):
    text = str(text).lower()

    if "drought" in text:
        return "Drought"

    elif "fire" in text or "wildfire" in text:
        return "Fire"

    elif (
        "flood" in text
        or "storm" in text
        or "tornado" in text
        or "hurricane" in text
        or "wind" in text
    ):
        return "Storm/Flood"

    else:
        return "Other"




gov_simple["match_type"] = gov_simple["disaster_type"].apply(simple_type)

sba_simple["match_type"] = sba_simple["disaster_description"].apply(simple_type)

fema_simple["match_type"] = fema_simple["incidentType"].apply(simple_type)


# TO TEST##

print("\nDisaster types standardized")

print("Governor:")
print(gov_simple["match_type"].value_counts())

print("\nSBA:")
print(sba_simple["match_type"].value_counts())

print("\nFEMA:")
print(fema_simple["match_type"].value_counts())





##---------------------------- Clean county names for matching----------------------------------##


def clean_county(name):
    name = str(name).lower().strip()
    name = name.replace("(county)", "")
    name = name.replace("county", "")
    return name.strip()


gov_simple["match_county"] = gov_simple["county"].apply(clean_county)

sba_simple["match_county"] = sba_simple["county_name"].apply(clean_county)

fema_simple["match_county"] = fema_simple["county_name"].apply(clean_county)


## to test##

print("\nCounty names standardized")

print("\nGovernor:")
print(gov_simple[["county", "match_county"]].head())

print("\nSBA:")
print(sba_simple[["county_name", "match_county"]].head())

print("\nFEMA:")
print(fema_simple[["county_name", "match_county"]].head())





##--------------------------Create event-level SBA records---------------------------------##
## SBA has many county rows for the same disaster..
# need to create one row per disaster event for matching with Governor and FEMA data##

sba_events = (
    sba_simple
    .groupby(
        ["disaster_number", "incident_start_date", "match_type"]
    )
    .agg(
        counties=("match_county", lambda x: set(x))
    )
    .reset_index()
)

print("\nSBA event table created")
print(sba_events.head())
print("Unique SBA events:", len(sba_events))




##-------------------------create the FEMA event table--------------------------------##

fema_events = (
    fema_simple
    .groupby(
        ["disasterNumber", "incidentBeginDate", "match_type"]
    )
    .agg(
        counties=("match_county", lambda x: set(x))
    )
    .reset_index()
)

print("\nFEMA event table created")
print(fema_events.head())
print("Unique FEMA events:", len(fema_events))


##-------------------------create the Governor event table--------------------------------##


gov_events = (
    gov_simple
    .groupby(
        ["disaster_id", "publication_date", "match_type"]
    )
    .agg(
        counties=("match_county", lambda x: set(x))
    )
    .reset_index()
)

print("\nGovernor event table created")
print(gov_events.head())
print("Unique Governor events:", len(gov_events))



##-----------------------to confirm the count:-----------------------------##

print("Unique Governor events:", len(gov_events))
print("Unique SBA events:", len(sba_events))
print("Unique FEMA events:", len(fema_events))



##--------------------------------------------------------------------------------------##
##-----------------------match Governor events to SBA events----------------------------##
##--------------------------------------------------------------------------------------##


gov_sba_matches = []

for _, gov_row in gov_events.iterrows():

    for _, sba_row in sba_events.iterrows():

        if gov_row["match_type"] != sba_row["match_type"]:
            continue

        county_overlap = len(
            gov_row["counties"] & sba_row["counties"]
        )

        date_difference = (
            gov_row["publication_date"]
            - sba_row["incident_start_date"]
        ).days

        if county_overlap > 0 and 0 <= date_difference <= 30:

            gov_sba_matches.append({
                "governor_disaster_id": gov_row["disaster_id"],
                "sba_number": sba_row["disaster_number"],
                "match_type": gov_row["match_type"],
                "county_overlap": county_overlap,
                "date_difference": date_difference
            })


gov_sba_matches = pd.DataFrame(gov_sba_matches)

print("\nGovernor-SBA candidate matches")
print(gov_sba_matches)
print("Candidate matches:", len(gov_sba_matches))


## only 3 matches found, show them ##

print("\nGovernor-SBA matches:")
print(
    gov_sba_matches[
        [
            "governor_disaster_id",
            "sba_number",
            "match_type",
            "county_overlap",
            "date_difference"
        ]
    ]
)





##----------------give each one a simple confidence level based on county overlap and date difference.---------------------##

def match_confidence(row):

    if row["county_overlap"] >= 3 and row["date_difference"] <= 14:
        return "high"

    elif row["county_overlap"] >= 2 and row["date_difference"] <= 30:
        return "medium"

    else:
        return "low"



gov_sba_matches["match_confidence"] = gov_sba_matches.apply(
    match_confidence,
    axis=1
)

print("\nGovernor-SBA matches with confidence:")
print(
    gov_sba_matches[
        [
            "governor_disaster_id",
            "sba_number",
            "county_overlap",
            "date_difference",
            "match_confidence"
        ]
    ]
)


##------------------------create the approved Governor–SBA matches---------------------------##

approved_gov_sba = gov_sba_matches[
    gov_sba_matches["match_confidence"].isin(
        ["high", "medium"]
    )
].copy()

print("\nApproved Governor-SBA matches:")
print(approved_gov_sba)

print("Approved matches:", len(approved_gov_sba))




##---------------------------------------------------------------------##
##------------Governor +FEMA matching----------------------------------##
##---------------------------------------------------------------------##


gov_fema_matches = []

for _, gov_row in gov_events.iterrows():

    for _, fema_row in fema_events.iterrows():

        if gov_row["match_type"] != fema_row["match_type"]:
            continue

        county_overlap = len(
            gov_row["counties"] & fema_row["counties"]
        )

        date_difference = (
            gov_row["publication_date"]
            - fema_row["incidentBeginDate"]
        ).days

        if county_overlap > 0 and 0 <= date_difference <= 30:

            gov_fema_matches.append({
                "governor_disaster_id": gov_row["disaster_id"],
                "fema_number": fema_row["disasterNumber"],
                "match_type": gov_row["match_type"],
                "county_overlap": county_overlap,
                "date_difference": date_difference
            })


gov_fema_matches = pd.DataFrame(gov_fema_matches)

print("\nGovernor-FEMA candidate matches:")
print(gov_fema_matches)

print("Candidate FEMA matches:", len(gov_fema_matches))


## 38 matches found ##
## -----------give those FEMA candidates the same confidence levels-----##
##----------------------------------------------------------------------##

gov_fema_matches["match_confidence"] = gov_fema_matches.apply(
    match_confidence,
    axis=1
)

print("\nGovernor-FEMA matches with confidence:")
print(
    gov_fema_matches[
        [
            "governor_disaster_id",
            "fema_number",
            "county_overlap",
            "date_difference",
            "match_confidence"
        ]
    ]
)

print("\nConfidence counts:")
print(gov_fema_matches["match_confidence"].value_counts())



##------------------------choose the best FEMA candidate--------------------------##

best_gov_fema = (
    gov_fema_matches
    .sort_values(
        by=[
            "governor_disaster_id",
            "county_overlap",
            "date_difference"
        ],
        ascending=[True, False, True]
    )
    .drop_duplicates(
        subset="governor_disaster_id",
        keep="first"
    )
    .copy()
)

print("\nBest FEMA match for each Governor event:")
print(best_gov_fema)

print("Best FEMA matches:", len(best_gov_fema))


##------------------------to approve the strong FEMA matches---------------------------##

approved_gov_fema = best_gov_fema[
    best_gov_fema["match_confidence"].isin(
        ["high", "medium"]
    )
].copy()

print("\nApproved Governor-FEMA matches:")
print(approved_gov_fema)

print("Approved FEMA matches:", len(approved_gov_fema))


## Check whether the same Governor event matched both SBA and FEMA

gov_sba_ids = set(
    approved_gov_sba["governor_disaster_id"]
)

gov_fema_ids = set(
    approved_gov_fema["governor_disaster_id"]
)

both_sources = gov_sba_ids & gov_fema_ids




##################temporarily stop event_number = using the old bad registry 



##--------create the connection table- to produce-- three datasets their shared event_id-----##


connections = []

for _, row in approved_gov_sba.iterrows():
    connections.append({
        "governor_id": row["governor_disaster_id"],
        "sba_number": row["sba_number"],
        "fema_number": None
    })

for _, row in approved_gov_fema.iterrows():
    connections.append({
        "governor_id": row["governor_disaster_id"],
        "sba_number": None,
        "fema_number": row["fema_number"]
    })

connections = pd.DataFrame(connections)


connections["fema_number"] = connections["fema_number"].astype("Int64") #-fix the FEMA numbers instead of decimals-

print("\nConnection table:")
print(connections)


##---------------------To create the shared event_id.--------------------------##
##-----------------------------------------------------------------------------##

# Create a key for each connected disaster
connections["link_key"] = connections.apply(        #Some proclamations has FEMA disaster--created a new ID--
                                                    #need to share the same event_id
    lambda row:
        f"SBA_{row['sba_number']}"
        if pd.notna(row["sba_number"])
        else f"FEMA_{row['fema_number']}",
    axis=1
)

# Give the same event_id to rows connected to the same disaster
unique_keys = connections["link_key"].unique()

gov_source_lookup = (
    proclamation
    .drop_duplicates("disaster_id")
    .set_index("disaster_id")["source_url"]
    .to_dict()
)




event_lookup = {}

for key in unique_keys:

    rows = connections[
        connections["link_key"] == key
    ]

    existing_ids = []

    for _, row in rows.iterrows():

        # Check SBA registry
        if pd.notna(row["sba_number"]):

            sba_id = str(row["sba_number"])

            if sba_id in sba_old_ids:
                existing_ids.append(
                    sba_old_ids[sba_id]
                )

        # Check FEMA registry
        if pd.notna(row["fema_number"]):

            fema_id = str(
                int(row["fema_number"])
            )

            if fema_id in fema_old_ids:
                existing_ids.append(
                    fema_old_ids[fema_id]
                )

        # Check Governor registry
        gov_id = int(row["governor_id"])

        gov_source_url = gov_source_lookup.get(gov_id)

        if gov_source_url in gov_old_ids:
            existing_ids.append(
                gov_old_ids[gov_source_url]
            )

    # Reuse an existing ID if this event is already known
    if len(existing_ids) > 0:

        event_lookup[key] = existing_ids[0]

    # Otherwise give this new matched event a brand-new ID
    else:

        event_lookup[key] = (
            f"EID_{next_event_number:04d}"
        )

        next_event_number += 1

connections["event_id"] = connections["link_key"].map(event_lookup)

print(
    connections[
        ["governor_id", "sba_number", "fema_number", "event_id"]
    ]
)

print("\nConnections with Event IDs:")
print(connections)


##---------------------put the new event_id back into the Governor proclamation dataset--------------------------##

# Create a map from Governor disaster_id to matched event_id
gov_map = (
    connections
    .drop_duplicates("governor_id")
    .set_index("governor_id")["event_id"]
)

# First assign event_id from the approved matches
proclamation["event_id"] = (
    proclamation["disaster_id"]
    .map(gov_map)
)

# Reuse old Governor event IDs only when
# there is no approved matched event_id
proclamation["event_id"] = (
    proclamation["event_id"]
    .fillna(
        proclamation["source_url"].map(gov_old_ids)
    )
)


print("\nGovernor data with event_id:")
print(
    proclamation[
        ["disaster_id", "event_id"]
    ].head(20)
)

print(
    "Governor rows with event_id:",
    proclamation["event_id"].notna().sum()
)

##---------------------add event_id to the SBA Texas data------------------------##

sba_map = (
    connections
    .dropna(subset=["sba_number"])
    .drop_duplicates("sba_number")
    .set_index("sba_number")["event_id"]
)

sba_tx["event_id"] = sba_tx["disaster_number"].map(sba_map)

### Reuse SBA event IDs from previous runs
sba_tx["event_id"] = (
    sba_tx["event_id"]
    .map(sba_old_ids)
    .fillna(sba_tx["event_id"])
)





print(
    "SBA rows with event_id:",
    sba_tx["event_id"].notna().sum()
)


##--------------------add event_id to FEMA----------------------##

fema_map = (
    connections
    .dropna(subset=["fema_number"])
    .drop_duplicates("fema_number")
    .set_index("fema_number")["event_id"]
)

fema["event_id"] = fema["disasterNumber"].map(fema_map)

###  Reuse`` FEMA event IDs from previous runs
old_fema_map = {
    int(source_id): event_id
    for source_id, event_id in fema_old_ids.items()
}


fema["event_id"] = (
    fema["event_id"]
    .fillna(
        fema["disasterNumber"].map(old_fema_map)
    )
)



##--------------------verify that nothing is missing after registry reuse.------------------------##


print("\nAfter registry reuse:")

print(
    "Governor missing:",
    proclamation["event_id"].isna().sum()
)

print(
    "SBA missing:",
    sba_tx["event_id"].isna().sum()
)

print(
    "FEMA missing:",
    fema["event_id"].isna().sum()
)

print(
    "FEMA rows with event_id:",
    fema["event_id"].notna().sum()
)




##----------------------assign IDs to unmatched Governor events------------------------##

event_number = next_event_number

for disaster_id in proclamation.loc[
    proclamation["event_id"].isna(),
    "disaster_id"
].unique():

    new_event_id = f"EID_{event_number:04d}"

    proclamation.loc[
        proclamation["disaster_id"] == disaster_id,
        "event_id"
    ] = new_event_id

    event_number += 1

print(
    "Governor missing event IDs:",
    proclamation["event_id"].isna().sum()
)

##-------------------assign IDs to unmatched SBA events------------------------##

for disaster_number in sba_tx.loc[
    sba_tx["event_id"].isna(),
    "disaster_number"
].unique():

    new_event_id = f"EID_{event_number:04d}"

    sba_tx.loc[
        sba_tx["disaster_number"] == disaster_number,
        "event_id"
    ] = new_event_id

    event_number += 1

print(
    "SBA missing event IDs:",
    sba_tx["event_id"].isna().sum()
)


##-------------------assign IDs to unmatched FEMA events-----------------------##

for disaster_number in fema.loc[
    fema["event_id"].isna(),
    "disasterNumber"
].unique():

    new_event_id = f"EID_{event_number:04d}"

    fema.loc[
        fema["disasterNumber"] == disaster_number,
        "event_id"
    ] = new_event_id

    event_number += 1


print(
    "FEMA missing event IDs:",
    fema["event_id"].isna().sum()
)



##---------------------verify all three together------------------------##




##last collision check across all three sources together

all_event_ids = pd.concat([
    proclamation[["event_id"]].drop_duplicates(),
    sba_tx[["event_id"]].drop_duplicates(),
    fema[["event_id"]].drop_duplicates()
])



###---------------------save the updated datasets------------------------##
import os

os.makedirs("output", exist_ok=True)


##--------------------final validation-----------------------##

print("\nFINAL VALIDATION")

print("Governor missing:", proclamation["event_id"].isna().sum())
print("SBA missing:", sba_tx["event_id"].isna().sum())
print("FEMA missing:", fema["event_id"].isna().sum())




##---------------------export the JSON files------------------------##

proclamation.to_json(
    "output/governor_disasters.json",
    orient="records",
    indent=4,
    date_format="iso"
)

sba_tx.to_json(
    "output/sba_disasters.json",
    orient="records",
    indent=4,
    date_format="iso"
)

fema.to_json(
    "output/fema_disasters.json",
    orient="records",
    indent=4,
    date_format="iso"
)

connections.to_json(
    "output/event_connections.json",
    orient="records",
    indent=4
)

print("\nJSON files saved.")


##---------------------export the CSV files------------------------##

proclamation.to_csv(
    "output/governor_disasters.csv",
    index=False
)

sba_tx.to_csv(
    "output/sba_disasters.csv",
    index=False
)

fema.to_csv(
    "output/fema_disasters.csv",
    index=False
)

connections.to_csv(
    "output/event_connections.csv",
    index=False
)

print("\nCSV files saved.")


##---------------------create the registry------------------------##
#that remembers which source disaster already owns which event_id,
#  so that future updates can be matched to the same event_id




gov_registry = (
    proclamation[["source_url", "event_id"]]
    .drop_duplicates()
    .rename(columns={"source_url": "source_id"})
)

gov_registry["source"] = "Governor"


sba_registry = (
    sba_tx[["disaster_number", "event_id"]]
    .drop_duplicates()
    .rename(columns={"disaster_number": "source_id"})
)

sba_registry["source"] = "SBA"


fema_registry = (
    fema[["disasterNumber", "event_id"]]
    .drop_duplicates()
    .rename(columns={"disasterNumber": "source_id"})
)

fema_registry["source"] = "FEMA"


event_registry = pd.concat(
    [gov_registry, sba_registry, fema_registry],
    ignore_index=True
)

event_registry["source_id"] = event_registry["source_id"].astype(str)

event_registry.to_csv(
    "output/event_id_registry.csv",
    index=False
)

print("\nRegistry rebuilt.")
print("Registry rows:", len(event_registry))
print("Unique event IDs:", event_registry["event_id"].nunique())






### Create detailed table for reviewing matched disaster records

matched_event_ids = connections["event_id"].unique()

print("\nMatched event IDs:")
print(matched_event_ids)

print("Total matched event IDs:", len(matched_event_ids))





