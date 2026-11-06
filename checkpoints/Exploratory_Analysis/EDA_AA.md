# EDA Summary (Ahmad)

Notebook: `notebooks/eda_aa2.ipynb`

For this EDA I focused on **Chicago only**. My main dataset is the OSM ALPR cameras, and I used the Chicago ward shapes and ward income data to compare cameras across the 50 wards.

---

## Step 1: Dataset Profiles

| Dataset | Role | Rows x Columns | One row = |
|---|---|---|---|
| OSM ALPR cameras | primary | 8,047 x 11 | one ALPR camera in Illinois |
| EFF Atlas of Surveillance | primary | 15,135 x 13 (28 in the raw file) | one agency using one technology |
| Chicago wards | secondary | 50 x 2 | one ward (number + shape) |
| Chicago ward income | secondary | 50 x 10 | one ward's household income |
| Chicago city boundary | secondary | 1 x 1 | the city outline |

**What stands out:**
- **OSM:** There are no duplicate rows and no missing `lat` / `lon`. However, `operator` is missing for 7,064 cameras, and `manufacturer` is missing for 643. Flock Safety makes 5,772 of the 8,047 cameras in Illinois.
- **Atlas:** The loader keeps 13 of the 28 columns. Chicago PD and Houston PD use 10 of the 12 technologies, the most of any agency. In Illinois, Flock Safety shows up in 221 of the 258 ALPR rows.
- **Ward income:** The 5 income brackets add up to the total households for every ward. Ward 20 has the lowest median income ($43,792) and ward 42 has the highest ($170,763).
- **Wards / city:** The 50 wards add up to about the same area as the city boundary (231.42 vs. 231.37 sq miles).

**Datasets I didn't use:**
- **Census by ZIP:** Since I'm only looking at Chicago, the ward income data fits better.
- **Eyes On Flock:** I don't trust it, since the numbers are self-reported by agencies.

---

## Step 2: Anomalies

| Dataset | Anomaly | Rows affected | What I did |
|---|---|---|---|
| OSM | Axis spelled two ways ("Axis communications" with a lowercase c) | 500 | Fixed, merged into one name |
| OSM | `manufacturer` missing | 643 (355 in Chicago) | Flagged, labeled as "Unknown" |
| OSM | `operator` missing | 7,064 | Left it, not used in my plots |
| OSM | `timestamp` is the last edit, not when the camera was added | all edited cameras | Only used never-edited cameras (`version == 1`, 1,047 in Chicago) in R4 |
| OSM | Big mapping spike in 2026 Q3, mostly Axis cameras in ward 41 (O'Hare) | 529 Axis, 311 in ward 41 | Flagged in the R4 note |
| Atlas | Exact duplicate rows (Burleson PD, Orlando PD) | 2 | Flagged |
| Atlas | Missing values written as "" instead of blank | 7,203 in Vendor | Fixed by the loader (turned into nulls) |
| Atlas | "FRT" is the same as "Face Recognition" | 6 | Fixed by the loader |
| Atlas | Dates that couldn't be read | 4,863 missing after loading vs. 1,898 empty in the raw file | Turned into nulls by the loader |
| Atlas | `vendor` sometimes lists more than one company | 19 different strings with "Flock" | Left it |
| Wards | Invalid ward shapes | 6 (wards 11, 12, 27, 28, 40, 50) | Fixed with `make_valid()` |
| Wards / income | `ward` is text in one file and a number in the other | 50 | Fixed, changed to text before joining |

---

## Step 3: Distributions

- **D1, Cameras by manufacturer in Chicago (bar chart):** Out of 1,327 cameras in Chicago, Axis has the most (529), then Unknown (355), Motorola (281), and Flock only has 93. So, in Chicago most cameras are not Flock.
- **D2, Cameras per ward (histogram):** Skewed to the right. Most wards have only a few cameras (the median is 13), but one ward has over 300, which is a big outlier.

---

## Step 4 and 5: Relationships, So What? and What Next?

### 4.1 map and R1: Map of ALPR cameras in Chicago
- **So what?** Axis cameras are mostly downtown and at O'Hare, Motorola cameras are spread out on the South and West Sides, and Flock cameras are scattered around the neighborhoods. Some areas have almost no cameras, but that could just mean nobody mapped them yet.
- **What next?** Color the map by `operator` to see who runs each group of cameras.

### R2: Camera density vs. income by ward (uses the ward join)
- **So what?** The two wards with the most cameras per square mile (42 and 2) are also two of the richest. However, ward 34 has a lot of cameras with a middle income, and most wards have less than 15 cameras per square mile no matter their income. So, richer wards might have a few more cameras, but this doesn't prove income causes it.
- **What next?** Take out the downtown wards to see if the pattern still holds, and join crime data by ward.

### R4: New cameras mapped in Chicago per quarter
- **So what?** New cameras get mapped slowly over time, then there's a huge jump in 2026 Q3. That jump is mostly Axis cameras in ward 41 (O'Hare) mapped on Sept 18, 19, and 20, so this plot shows when cameras were added to OSM, not when they were installed. Flock stays low the whole time.
- **What next?** Take out the 2026 Q3 jump, and make the same plot for all of Illinois to compare.

---

## Step 6: Revised Research Questions

1. **(revised)** How many new ALPR cameras are being mapped in Chicago each quarter, and is Flock growing faster than the other manufacturers?
   - **What changed and why:** I narrowed it to Chicago and split Flock vs. other cameras, since R4 showed a big jump that came from other cameras.
2. **(revised)** Do richer Chicago wards have more ALPR cameras per square mile than poorer wards?
   - **What changed and why:** I switched from ZIP codes to Chicago wards, since the ward data fits Chicago better.
3. **(unchanged)** Do ALPR-using agencies also use other surveillance technologies (like face recognition and drones) more than non-ALPR agencies?
   - **Why:** I explored the Atlas data but haven't plotted it yet.
4. **(revised)** Which Chicago wards have the most ALPR cameras per square mile, and which manufacturers are in them?
   - **What changed and why:** I compared wards inside Chicago instead of different cities, and looked at all ALPR cameras instead of only Flock, since most of Chicago's cameras are not Flock.
