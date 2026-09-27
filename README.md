# Where Tourism Lives in Lebanon

An interactive Streamlit page built for **MSBA 325 – Data Visualization and Communication**
(American University of Beirut). It takes two visualizations from the earlier Plotly
assignment and turns them into a drill-down that goes from the whole country down to a
single town.

**Live app:** <!-- paste your Streamlit Community Cloud link here after deploying -->
`https://<your-app-name>.streamlit.app`

---

## What the page shows

The dataset is a 2023 municipal survey of **1,137 Lebanese towns**, recording how many
restaurants, cafes, hotels and guest houses each one has, plus a Tourism Index from 0 to 10.

Two insights the page is built around:

1. **Tourism is concentrated, not spread.** Mount Lebanon alone holds 2,107 of the
   country's 6,146 establishments (34%), and 43% of all towns score zero on the
   Tourism Index.
2. **Places to eat are common; places to stay are not.** Restaurants and cafes are 83%
   of all establishments and hotels only 6%. Just 35% of towns that have somewhere to eat
   also have somewhere to sleep — though that climbs to 81% in towns with 20+ eateries.

Two visualizations:

| Chart | What it answers |
|---|---|
| Stacked horizontal bar | What is the tourism offer **made of**, and who leads? Redraws itself at governorate, district or town level depending on how far the reader has drilled. |
| Bubble scatter (log–log) | Do towns that **feed** visitors also **host** them? One bubble per town; colour and size show lodging. |

## The two linked controls

| # | Control | Role |
|---|---|---|
| 1 | Governorate **multiselect** | Sets the scope and the comparison set. |
| 2 | District **selectbox** | **Its options are rebuilt from Control 1**, so only districts inside the chosen governorates are ever offered. |

They are deliberately *not* independent filters. Control 1 decides what Control 2 can
offer, and together they decide what a bar in the first chart means:

```
All Lebanon  ──►  bars are governorates
one governorate selected  ──►  bars are its districts
one district selected     ──►  bars are its towns
```

Because the district list is derived from the live governorate selection, it is impossible
to ask for a district that is not in view, so the page can never render an empty chart.
The written justification for each control is on the page itself, under
*"Why these two controls, and why this way"*.

## Run it locally

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
pip install -r requirements.txt
streamlit run app.py
```

The app then opens at `http://localhost:8501`.

## Deploying to Streamlit Community Cloud

1. Push this repository to GitHub (public).
2. Go to <https://share.streamlit.io> and sign in with GitHub.
3. **Create app → Deploy a public app from GitHub**, then pick this repository,
   branch `main`, and main file path `app.py`.
4. Press **Deploy**. The first build takes a couple of minutes while
   `requirements.txt` is installed.
5. Copy the resulting `*.streamlit.app` URL back into the **Live app** line above.

## Repository contents

```
.
├── app.py                              # the whole Streamlit page
├── requirements.txt                    # pinned dependencies for Streamlit Cloud
├── data/
│   └── Tourism_Lebanon_Dataset.csv     # the dataset, read from disk at startup
├── .streamlit/
│   └── config.toml                     # theme colours
└── README.md
```

## Data source

*Tourism – Lebanon 2023*, published by **Impact Open Data** and hosted as linked open
data by the **American University of Beirut** (CODEC).
Observation URIs: `http://linked.aub.edu.lb/CODEC/Lebanon/Dataset/Tourism-Lebanon-2023`
· Publisher portal: <https://impact.cib.gov.lb>

The survey records the **presence and count** of establishments, not their size, quality
or revenue, and **Beirut is not included** in the dataset.

## Author

Rayane — MSBA 325, Data Visualization and Communication.
