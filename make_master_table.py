import pandas as pd

# Read the files already created by the main script
gov = pd.read_csv("output/governor_disasters.csv")
sba = pd.read_csv("output/sba_disasters.csv")
fema = pd.read_csv("output/fema_disasters.csv")
connections = pd.read_csv("output/event_connections.csv")

print("Governor:", gov.shape)
print("SBA:", sba.shape)
print("FEMA:", fema.shape)
print("Connections:", connections.shape)

# See the matched connections only
print("\nMatched connections:")
print(connections)

print("\nUnique matched event IDs:")
print(connections["event_id"].unique())

# Get Governor records for matched events
matched_gov = gov[
    gov["event_id"].isin(connections["event_id"])
].copy()

print("\nMatched Governor rows:", len(matched_gov))
print("\nGovernor columns:")
print(matched_gov.columns.tolist())


# Get SBA records for matched events
matched_sba = sba[
    sba["event_id"].isin(connections["event_id"])
].copy()

print("\nMatched SBA rows:", len(matched_sba))
print("\nSBA columns:")
print(matched_sba.columns.tolist())

# Get FEMA records for matched events
matched_fema = fema[
    fema["event_id"].isin(connections["event_id"])
].copy()

print("\nMatched FEMA rows:", len(matched_fema))
print("\nFEMA columns:")
print(matched_fema.columns.tolist())





# --------------------------------------------------
# BUILD CLEAN MATCH REVIEW TABLE
# One row for each actual connection
# --------------------------------------------------

def combine_values(series):
    values = (
        series
        .dropna()
        .astype(str)
        .drop_duplicates()
        .tolist()
    )

    return "; ".join(values)

print("\nCHECK GOV 24:")
print(
    gov[gov["disaster_id"] == 24][
        ["disaster_id", "county", "title", "event_id"]
    ]
)

print("\nCHECK GOV 77:")
print(
    gov[gov["disaster_id"] == 77][
        ["disaster_id", "county", "title", "event_id"]
    ]
)


review_rows = []


for _, connection in connections.iterrows():

    event_id = connection["event_id"]
    gov_id = connection["governor_id"]

    # Governor records belonging to this connection
    g = gov[
        (gov["event_id"] == event_id) &
        (gov["disaster_id"] == gov_id)
    ]

    row = {
        "event_id": event_id,

        # Governor details
        "gov_disaster_id": gov_id,
        "gov_publication_date": combine_values(
            g["publication_date"]
        ),
        "gov_disaster_type": combine_values(
            g["disaster_type"]
        ),
        "gov_action": combine_values(
            g["action"]
        ),
        "gov_counties": combine_values(
            g["county"]
        ),
        "gov_title": combine_values(
            g["title"]
        ),
        "gov_source_url": combine_values(
            g["source_url"]
        )
    }


    # --------------------------------------------------
    # Governor - SBA
    # --------------------------------------------------

    if pd.notna(connection["sba_number"]):

        row["matched_sources"] = "Governor-SBA"

        sba_number = connection["sba_number"]

        s = sba[
            (sba["event_id"] == event_id) &
            (sba["disaster_number"] == sba_number)
        ]

        row.update({
            "sba_disaster_number": sba_number,
            "sba_state": combine_values(s["state"]),
            "sba_description": combine_values(
                s["disaster_description"]
            ),
            "sba_incident_start_date": combine_values(
                s["incident_start_date"]
            ),
            "sba_incident_end_date": combine_values(
                s["incident_end_date"]
            ),
            "sba_declaration_date": combine_values(
                s["declaration_date"]
            ),
            "sba_declaration_type": combine_values(
                s["declaration_type"]
            ),
            "sba_status": combine_values(
                s["status"]
            ),
            "sba_physical_deadline_date": combine_values(
                s["physical_deadline_date"]
            ),
            "sba_eidl_deadline_date": combine_values(
                s["eidl_deadline_date"]
            ),
            "sba_fema_number": combine_values(
                s["fema_number"]
            ),
            "sba_county_type": combine_values(
                s["county_type"]
            ),
            "sba_counties": combine_values(
                s["county_name"]
            ),
            "sba_county_fips": combine_values(
                s["county_fips"]
            ),
            "sba_latitude": combine_values(
                s["latitude"]
            ),
            "sba_longitude": combine_values(
                s["longitude"]
            ),

            # No FEMA match
            "fema_disaster_number": None,
            "fema_declaration_type": None,
            "fema_declaration_date": None,
            "fema_incident_type": None,
            "fema_declaration_title": None,
            "fema_incident_begin_date": None,
            "fema_incident_end_date": None,
            "fema_designated_areas": None,
            "fema_state_fips": None,
            "fema_county_fips": None
        })


    # --------------------------------------------------
    # Governor - FEMA
    # --------------------------------------------------

    elif pd.notna(connection["fema_number"]):

        row["matched_sources"] = "Governor-FEMA"

        fema_number = int(connection["fema_number"])

        f = fema[
            (fema["event_id"] == event_id) &
            (fema["disasterNumber"] == fema_number)
        ]

        row.update({
            # No SBA match
            "sba_disaster_number": None,
            "sba_state": None,
            "sba_description": None,
            "sba_incident_start_date": None,
            "sba_incident_end_date": None,
            "sba_declaration_date": None,
            "sba_declaration_type": None,
            "sba_status": None,
            "sba_physical_deadline_date": None,
            "sba_eidl_deadline_date": None,
            "sba_fema_number": None,
            "sba_county_type": None,
            "sba_counties": None,
            "sba_county_fips": None,
            "sba_latitude": None,
            "sba_longitude": None,

            # FEMA details
            "fema_disaster_number": fema_number,
            "fema_declaration_type": combine_values(
                f["declarationType"]
            ),
            "fema_declaration_date": combine_values(
                f["declarationDate"]
            ),
            "fema_incident_type": combine_values(
                f["incidentType"]
            ),
            "fema_declaration_title": combine_values(
                f["declarationTitle"]
            ),
            "fema_incident_begin_date": combine_values(
                f["incidentBeginDate"]
            ),
            "fema_incident_end_date": combine_values(
                f["incidentEndDate"]
            ),
            "fema_designated_areas": combine_values(
                f["designatedArea"]
            ),
            "fema_state_fips": combine_values(
                f["fipsStateCode"]
            ),
            "fema_county_fips": combine_values(
                f["fipsCountyCode"]
            )
        })


    review_rows.append(row)


# --------------------------------------------------
# Save final review table
# --------------------------------------------------

master = pd.DataFrame(review_rows)

master.to_csv(
    "output/master_disaster_details.csv",
    index=False
)

print("\nMaster review table created.")
print("Rows:", len(master))
print("Unique event IDs:", master["event_id"].nunique())

print("\nMatch types:")
print(master["matched_sources"].value_counts())

print("\nSaved:")
print("output/master_disaster_details.csv")