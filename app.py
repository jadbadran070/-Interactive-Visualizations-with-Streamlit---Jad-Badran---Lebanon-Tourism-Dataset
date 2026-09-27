"""
MSBA 325 - Streamlit Activity
Where Tourism Lives in Lebanon: an interactive drill-down

Dataset : Tourism - Lebanon 2023 (AUB Linked Open Data / CODEC,
          publisher: Impact Open Data)
Author  : Rayane

The page keeps two related visualizations from the Plotly assignment and
connects them to two LINKED controls:

  Control 1 (sidebar)  : governorate multiselect  -> sets the scope
  Control 2 (sidebar)  : district selectbox       -> its OPTIONS are rebuilt
                         from whatever Control 1 currently holds, so the user
                         drills down (country -> governorate -> district ->
                         town) instead of filtering two things independently.

Run locally:  streamlit run app.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------
# Page setup and styling
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Where Tourism Lives in Lebanon",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

CEDAR, DEEP, RED, INK = "#1F6F4A", "#123F2B", "#C8102E", "#1B2631"
SEA, SAND, GREY, PANEL = "#2A7F9E", "#E9C46A", "#AEB6BF", "#F3F6F4"
TYPE_COLORS = {
    "Restaurants": CEDAR,
    "Cafes": SEA,
    "Hotels": RED,
    "Guest houses": SAND,
}

st.markdown(
    f"""
    <style>
      .block-container {{padding-top: 2.2rem; padding-bottom: 3rem;}}
      h1, h2, h3 {{color: {INK};}}
      .hero {{
        background: linear-gradient(120deg, {DEEP} 0%, {CEDAR} 100%);
        color: #ffffff; padding: 1.6rem 1.9rem; border-radius: 14px;
        margin-bottom: 1.3rem;
      }}
      .hero h1 {{color: #ffffff; margin: 0 0 .35rem 0; font-size: 2.1rem;}}
      .hero p {{margin: 0; color: #E5EFEA; font-size: 1.02rem; max-width: 60rem;}}
      .insight {{
        background: {PANEL}; border-radius: 12px; padding: 1rem 1.15rem;
        height: 100%;
      }}
      .insight b {{color: {CEDAR};}}
      .scope-note {{
        background: #FBEFF1; border-radius: 10px; padding: .7rem 1rem;
        font-size: .93rem; color: {INK};
      }}
      div[data-testid="stMetricValue"] {{color: {CEDAR}; font-size: 1.9rem;}}
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# Data loading and cleaning (cached so the widgets stay instant)
# --------------------------------------------------------------------------
DATA_PATH = Path(__file__).parent / "data" / "Tourism_Lebanon_Dataset.csv"

COUNT_COLS = ["Restaurants", "Cafes", "Hotels", "Guest houses"]
ALL_DISTRICTS = "All districts in the selection"

# Each area in the source file is mapped to one of Lebanon's governorates.
# Keserwan and Byblos are kept under Mount Lebanon; Beirut is not in the data.
GOVERNORATE_OF = {
    "Akkar": "Akkar",
    "Mount Lebanon": "Mount Lebanon", "Matn": "Mount Lebanon",
    "Byblos": "Mount Lebanon", "Aley": "Mount Lebanon",
    "Keserwan": "Mount Lebanon", "Baabda": "Mount Lebanon",
    "Baalbek-Hermel": "Baalbek-Hermel", "Hermel": "Baalbek-Hermel",
    "South": "South", "Tyre": "South", "Sidon": "South",
    "North": "North", "Miniyeh-Danniyeh": "North", "Zgharta": "North",
    "Batroun": "North", "Bsharri": "North", "Tripoli": "North",
    "Nabatieh": "Nabatieh", "Bint Jbeil": "Nabatieh",
    "Marjeyoun": "Nabatieh", "Hasbaya": "Nabatieh",
    "Beqaa": "Beqaa", "Zahle": "Beqaa", "Western Beqaa": "Beqaa",
}


def _fix_mojibake(text: str) -> str:
    """Repair UTF-8 text that was decoded as Latin-1 (e.g. 'ZahlÃ©' -> 'Zahle')."""
    try:
        return text.encode("latin1").decode("utf8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["Town"] = df["Town"].str.strip()

    # refArea is a DBpedia URL that mixes district-level and governorate-level areas
    area = (
        df["refArea"].str.split("/").str[-1].apply(_fix_mojibake)
        .str.replace("_Governorate", "", regex=False)
        .str.replace("_District", "", regex=False)
        .str.replace(",_Lebanon", "", regex=False)
        .str.replace("_", " ", regex=False)
        .str.replace("–", "-", regex=False)   # en dash in Miniyeh-Danniyeh
        .str.replace("é", "e", regex=False)   # Zahle
    )
    df["Area"] = area
    df["Governorate"] = df["Area"].map(GOVERNORATE_OF)

    # Rows tagged only at governorate level get their own bucket, so a district
    # drill-down never silently hides towns. Akkar governorate is one district.
    df["District"] = np.where(
        df["Area"] != df["Governorate"],
        df["Area"],
        np.where(df["Area"] == "Akkar", "Akkar", df["Area"] + " (district not specified)"),
    )

    df = df.rename(
        columns={
            "Total number of restaurants": "Restaurants",
            "Total number of cafes": "Cafes",
            "Total number of hotels": "Hotels",
            "Total number of guest houses": "Guest houses",
            "Existence of touristic attractions prone to be exploited and developed - exists":
                "Untapped attraction",
            "Existence of initiatives and projects in the past five years to "
            "improve the tourism sector - exists": "Recent initiative",
        }
    )

    df["Dining"] = df["Restaurants"] + df["Cafes"]
    df["Lodging"] = df["Hotels"] + df["Guest houses"]
    df["Total establishments"] = df[COUNT_COLS].sum(axis=1)
    df["Has lodging"] = np.where(
        df["Lodging"] > 0, "Has hotel or guest house", "No lodging"
    )
    return df[
        ["Town", "Governorate", "District", "Tourism Index", "Untapped attraction",
         "Recent initiative", "Dining", "Lodging", "Has lodging",
         "Total establishments"] + COUNT_COLS
    ]


df = load_data()
GOVERNORATES = sorted(df["Governorate"].unique())


# --------------------------------------------------------------------------
# Header and page context
# --------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
      <h1>Where Tourism Lives in Lebanon</h1>
      <p>Lebanon's tourism sector is usually described country-wide, which hides how
      unevenly it is spread. This page uses a 2023 municipal survey of
      <b>1,137 towns</b> to show where restaurants, cafes, hotels and guest houses
      actually are &mdash; and lets you drill from the whole country down to a single
      town.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("About the data (source, coverage, and how it was prepared)"):
    st.markdown(
        """
**Source.** *Tourism &ndash; Lebanon 2023*, published by **Impact Open Data** and hosted as
linked open data by the **American University of Beirut** (CODEC). Each row is one town.

**What each row holds.** Counts of restaurants, cafes, hotels and guest houses; yes/no
flags for untapped tourist attractions and for tourism projects in the last five years;
and a **Tourism Index** from 0 (no activity recorded) to 10.

**Preparation.**
- The area of each town is stored inside a DBpedia URL, so the name is extracted from
  the link and broken accents are repaired.
- The source mixes 25 districts and governorates in one column. These are mapped to
  Lebanon's **7 governorates**; Keserwan and Byblos sit under Mount Lebanon.
  **Beirut is not in the dataset.**
- Towns the source tagged only at governorate level are kept in a visible
  *"(district not specified)"* bucket rather than dropped.

**A caveat worth stating.** The survey records **presence and counts, not quality, size
or revenue.** One large hotel and one guesthouse both count as one establishment.
        """
    )


# --------------------------------------------------------------------------
# THE TWO LINKED CONTROLS
#   The district options below are rebuilt from the governorate selection, which
#   is what makes the two controls a drill-down rather than two separate filters.
# --------------------------------------------------------------------------
st.sidebar.markdown("### Explore the map of tourism")
st.sidebar.caption(
    "Pick your regions first. The district list underneath rebuilds itself from "
    "that choice, so you can zoom in step by step."
)


def _reset_scope() -> None:
    st.session_state["govs"] = GOVERNORATES
    st.session_state["district"] = ALL_DISTRICTS


if "govs" not in st.session_state:
    st.session_state["govs"] = GOVERNORATES

# ---- Control 1: which governorates are in scope -------------------------
selected_govs = st.sidebar.multiselect(
    "**1. Governorates**",
    options=GOVERNORATES,
    key="govs",
    help="Choose one or more regions to compare. Clearing this empties the page.",
)

if not selected_govs:
    # The reset button has to be drawn here too, otherwise clearing every region
    # leaves the reader with no one-click way back.
    st.sidebar.button("Reset to all of Lebanon", on_click=_reset_scope,
                      width="stretch", key="reset_empty")
    st.sidebar.warning("Select at least one governorate.")
    st.warning("No governorate is selected, so there is nothing to show. "
               "Pick a region in the sidebar, or press **Reset to all of Lebanon**.")
    st.stop()

# ---- Control 2: district options depend on Control 1 --------------------
district_options = [ALL_DISTRICTS] + sorted(
    df.loc[df["Governorate"].isin(selected_govs), "District"].unique()
)
# If the governorate selection changed, a previously chosen district may no
# longer exist. Reset it before the widget is drawn so the app never errors.
if st.session_state.get("district") not in district_options:
    st.session_state["district"] = ALL_DISTRICTS

selected_district = st.sidebar.selectbox(
    "**2. District** (options come from your choice above)",
    options=district_options,
    key="district",
    help="Zoom into one district. The list only ever offers districts that exist "
         "inside the governorates you selected.",
)

st.sidebar.button("Reset to all of Lebanon", on_click=_reset_scope,
                  width="stretch")

# ---- Apply the scope ----------------------------------------------------
scope = df[df["Governorate"].isin(selected_govs)]
if selected_district != ALL_DISTRICTS:
    scope = scope[scope["District"] == selected_district]

# The drill-down level for the composition chart follows the two controls.
if selected_district != ALL_DISTRICTS:
    level, level_label = "Town", f"towns in {selected_district}"
elif len(selected_govs) == 1:
    level, level_label = "District", f"districts of {selected_govs[0]}"
else:
    level, level_label = "Governorate", "governorates"

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"**In scope:** {len(scope):,} towns  \n"
    f"**Breakdown level:** {level.lower()}"
)
st.sidebar.caption(
    "Source: Tourism - Lebanon 2023, Impact Open Data / AUB linked open data."
)


# --------------------------------------------------------------------------
# Headline numbers for the current scope
# --------------------------------------------------------------------------
st.subheader("The picture for your selection")

total_est = int(scope["Total establishments"].sum())
share_of_country = total_est / int(df["Total establishments"].sum()) * 100
zero_share = (scope["Tourism Index"] == 0).mean() * 100
dining_towns = scope[scope["Dining"] > 0]
lodging_share = (
    (dining_towns["Lodging"] > 0).mean() * 100 if len(dining_towns) else 0.0
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Towns in scope", f"{len(scope):,}")
k2.metric("Tourism establishments", f"{total_est:,}",
          help="Restaurants + cafes + hotels + guest houses.")
k3.metric("Share of Lebanon's total", f"{share_of_country:.0f}%")
k4.metric("Towns with no tourism", f"{zero_share:.0f}%",
          help="Towns whose Tourism Index is 0.")

national_tail = (
    "" if len(scope) == len(df) else " Across the whole country that figure is 35%."
)
st.markdown(
    f"""<div class="scope-note">Of the {len(dining_towns):,} towns here that have at
    least one restaurant or cafe, <b>{lodging_share:.0f}%</b> also offer a hotel or a
    guest house.{national_tail}</div>""",
    unsafe_allow_html=True,
)
st.write("")


# --------------------------------------------------------------------------
# Two insights the page is built to highlight
# --------------------------------------------------------------------------
st.subheader("Two things the data makes clear")
c1, c2 = st.columns(2)
c1.markdown(
    """<div class="insight"><b>1. Tourism is concentrated, not spread.</b><br>
    Mount Lebanon alone holds 2,107 of the country's 6,146 establishments (34%),
    and 43% of all Lebanese towns score a flat zero on the Tourism Index.
    Half the country's dining sits in just five districts.
    <i>Select one governorate at a time to watch the concentration repeat itself
    inside each region.</i></div>""",
    unsafe_allow_html=True,
)
c2.markdown(
    """<div class="insight"><b>2. Places to eat are common; places to stay are not.</b><br>
    Restaurants and cafes make up 83% of all establishments, hotels just 6%.
    Only 35% of towns that have somewhere to eat also have somewhere to sleep &mdash;
    but that rises to 81% in towns with 20 or more eateries.
    <i>The scatter plot below shows exactly which towns are missing their
    lodging.</i></div>""",
    unsafe_allow_html=True,
)
st.write("")


# --------------------------------------------------------------------------
# VISUALIZATION 1 - composition bar chart, redrawn at the drill-down level
# --------------------------------------------------------------------------
st.subheader(f"1. What the tourism offer is made of, by {level.lower()}")

grouped = (
    scope.groupby(level, as_index=False)[COUNT_COLS + ["Total establishments"]]
    .sum()
    .sort_values("Total establishments", ascending=False)
)
grouped = grouped[grouped["Total establishments"] > 0]

TOP_N = 15
truncated = len(grouped) > TOP_N
plot_df = grouped.head(TOP_N).sort_values("Total establishments")

if plot_df.empty:
    st.info("No establishments are recorded anywhere in this selection.")
else:
    long_df = plot_df.melt(
        id_vars=[level, "Total establishments"],
        value_vars=COUNT_COLS,
        var_name="Type",
        value_name="Count",
    )
    fig1 = px.bar(
        long_df, x="Count", y=level, color="Type", orientation="h",
        color_discrete_map=TYPE_COLORS,
        category_orders={"Type": COUNT_COLS},
        custom_data=["Type"],
    )
    fig1.update_traces(
        hovertemplate="<b>%{y}</b><br>%{customdata[0]}: %{x}<extra></extra>"
    )
    # Total at the end of each bar, so the reader gets the sum and the mix at once
    fig1.add_trace(
        go.Scatter(
            x=plot_df["Total establishments"], y=plot_df[level], mode="text",
            text=["  " + f"{v:,}" for v in plot_df["Total establishments"]],
            textposition="middle right", textfont=dict(size=13, color=INK),
            showlegend=False, hoverinfo="skip",
        )
    )
    fig1.update_layout(
        barmode="stack", template="plotly_white",
        height=max(330, 42 * len(plot_df) + 150),
        margin=dict(l=10, r=30, t=30, b=10),
        xaxis_title="Number of establishments", yaxis_title="",
        xaxis=dict(range=[0, plot_df["Total establishments"].max() * 1.12],
                   gridcolor="#EAECEE"),
        legend=dict(orientation="h", y=-0.18, x=0, title_text=""),
        font=dict(family="Arial", size=13, color=INK),
    )
    st.plotly_chart(fig1, width="stretch")

    leader = grouped.iloc[0]
    lead_share = leader["Total establishments"] / grouped["Total establishments"].sum() * 100
    caption = (
        f"Showing {level_label}. **{leader[level]}** leads with "
        f"{int(leader['Total establishments']):,} establishments, "
        f"{lead_share:.0f}% of everything in this selection."
    )
    if truncated:
        caption += f" Only the top {TOP_N} of {len(grouped)} are drawn."
    st.caption(caption)


# --------------------------------------------------------------------------
# VISUALIZATION 2 - dining vs lodging, one bubble per town in scope
# --------------------------------------------------------------------------
st.subheader("2. Do towns that feed visitors also host them?")

sc = scope[scope["Dining"] > 0].copy()
if sc.empty:
    st.info("No town in this selection has a restaurant or a cafe.")
else:
    rng = np.random.default_rng(325)
    sc["Bubble"] = np.sqrt(sc["Lodging"]) + 1           # tames the 60-guesthouse outlier
    # +1 lets zeros sit on a log axis; a small jitter separates identical towns
    sc["x"] = (sc["Restaurants"] + 1) * rng.uniform(0.94, 1.06, len(sc))
    sc["y"] = (sc["Cafes"] + 1) * rng.uniform(0.94, 1.06, len(sc))
    sc = sc.sort_values("Lodging")

    fig2 = px.scatter(
        sc, x="x", y="y", size="Bubble", color="Has lodging",
        color_discrete_map={"No lodging": GREY, "Has hotel or guest house": RED},
        category_orders={"Has lodging": ["Has hotel or guest house", "No lodging"]},
        size_max=30, opacity=0.78, log_x=True, log_y=True,
        hover_name="Town",
        custom_data=["District", "Restaurants", "Cafes", "Hotels",
                     "Guest houses", "Tourism Index"],
    )
    fig2.update_traces(
        marker=dict(line=dict(color="white", width=0.8)),
        hovertemplate=(
            "<b>%{hovertext}</b><br>%{customdata[0]}<br><br>"
            "Restaurants: %{customdata[1]}<br>Cafes: %{customdata[2]}<br>"
            "Hotels: %{customdata[3]}<br>Guest houses: %{customdata[4]}<br>"
            "Tourism Index: %{customdata[5]}/10<extra></extra>"
        ),
    )
    # When the user has drilled in far enough, name the towns on the chart itself
    if len(sc) <= 40:
        top = sc.nlargest(min(6, len(sc)), "Total establishments")
        for i, (_, r) in enumerate(top.iterrows()):
            # alternate the label above/below so neighbouring labels do not collide
            ay = -28 if i % 2 == 0 else 30
            fig2.add_annotation(
                x=np.log10(r["x"]), y=np.log10(r["y"]), text=r["Town"],
                showarrow=True, arrowhead=0, arrowcolor="#7F8C8D",
                ax=0, ay=ay, font=dict(size=12, color=INK),
                bgcolor="rgba(255,255,255,0.8)",
            )

    ticks = [1, 2, 3, 6, 11, 21, 51, 101]
    fig2.update_xaxes(title="Restaurants in town (log scale)", tickvals=ticks,
                      ticktext=[t - 1 for t in ticks], gridcolor="#EAECEE")
    fig2.update_yaxes(title="Cafes in town (log scale)", tickvals=ticks,
                      ticktext=[t - 1 for t in ticks], gridcolor="#EAECEE")
    fig2.update_layout(
        template="plotly_white", height=520,
        margin=dict(l=10, r=20, t=40, b=10),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right",
                    yanchor="bottom", title_text=""),
        font=dict(family="Arial", size=13, color=INK),
    )
    st.plotly_chart(fig2, width="stretch")

    gap = sc[sc["Lodging"] == 0].nlargest(3, "Dining")[["Town", "Dining"]]
    if len(gap):
        names = ", ".join(f"**{t}** ({int(d)} eateries)" for t, d in gap.to_numpy())
        st.caption(
            f"Each bubble is one town; bubble size is the number of hotels and guest "
            f"houses. Biggest lodging gaps in this selection: {names}."
        )


# --------------------------------------------------------------------------
# Design justifications (required by the brief)
# --------------------------------------------------------------------------
st.markdown("---")
st.subheader("Why these two controls, and why this way")

with st.expander("Control 1 - Governorate multiselect", expanded=False):
    st.markdown(
        """
**The user question it answers.** *"How does my region compare with the others, and
what happens if I put only the regions I care about side by side?"* A planner in the
North does not want Mount Lebanon's 2,107 establishments flattening every other bar;
a reader comparing the two southern governorates wants only those two on screen.

**Why a multiselect and not something else.** Three alternatives were considered:

- A **single-choice dropdown** would answer "what about my region?" but destroys
  comparison, which is the whole point of the first chart.
- **Seven checkboxes** hold the same information but cost seven clicks to clear and
  push the second control far down the sidebar.
- **Keeping all seven always visible** was the Plotly version of this chart, and it is
  exactly the clutter this page is trying to fix.

The multiselect gives free comparison of any subset in one compact widget, and it
defaults to all seven so the reader still gets the **overview first**.

**The course concept behind it.** This is the first move of Shneiderman's mantra,
*overview first, zoom and filter, details on demand*. It is also a deliberate
**reduce-clutter / data-ink** decision: every governorate the reader removes is ink
spent on a comparison they did not ask for. Because removing a region rescales the
axis, it also protects **accurate encoding** &mdash; small regions stay readable instead of
being crushed against the left edge by a single dominant bar.
        """
    )

with st.expander("Control 2 - District drill-down (linked to Control 1)", expanded=False):
    st.markdown(
        """
**The user question it answers.** *"Fine &mdash; but inside the region I picked, where
exactly is the activity, and which individual towns are driving it?"* A governorate
total hides that Baabda district alone out-dines four entire governorates, and that
inside Baabda a handful of towns hold most of it.

**Why a dependent selectbox and not something else.** The important design decision is
not the widget's shape but that **its options are rebuilt from Control 1**. Districts
that do not exist inside the chosen governorates are never offered, so an empty chart
is impossible by construction. Alternatives considered:

- A **flat list of all 25 districts** independent of Control 1 lets the user pick
  Batroun while viewing the South and get a blank page. Two filters, no relationship.
- A **text search box** would demand the user already know the district names, which
  is exactly the knowledge the page is meant to supply.
- A **second multiselect** would allow arbitrary district combinations, but that
  re-creates the clutter problem one level down and makes "which town?" unanswerable.

Single choice is the right constraint here, because the third level of the drill-down
(towns) is only legible for one district at a time.

**The course concept behind it.** This is **zoom-and-filter into details-on-demand**,
and it is the reason the first chart silently changes what a bar means &mdash;
governorate, then district, then town &mdash; instead of adding a third chart to the page.
Keeping the governorate selection visible in the sidebar while the district view is on
screen preserves **focus plus context**: the reader never loses track of where the
zoomed view sits in the whole. Restricting the options is also **error prevention**:
the interface will not let the reader build a question the data cannot answer.
        """
    )

st.markdown("---")
with st.expander("See the filtered data table"):
    st.dataframe(
        scope.sort_values("Total establishments", ascending=False)
        .loc[:, ["Town", "District", "Governorate"] + COUNT_COLS +
             ["Total establishments", "Tourism Index"]]
        .reset_index(drop=True),
        width="stretch", height=380,
    )

st.caption(
    "Data: Tourism - Lebanon 2023, Impact Open Data, published as linked open data by "
    "the American University of Beirut (CODEC). Built with Streamlit and Plotly for "
    "MSBA 325 by Rayane."
)
