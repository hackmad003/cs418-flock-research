# Exploratory Data Analysis

Name: Alexandra Golley

## 1. Dataset Profiles

### ALPR Camera Dataset

The ALPR camera dataset contains 101,085 records and 4 columns. Each record represents an ALPR camera/location and includes an ID, latitude, longitude, and an indicator for whether the camera is identified as a Flock camera.

The dataset contains 75,614 Flock cameras and 25,471 non-Flock cameras. There are no missing values, duplicate rows, duplicate IDs, or invalid latitude/longitude values.

The latitude and longitude ranges show that the dataset covers a broad geographic area rather than only Chicago. The analysis uses a Chicago geographic subset when comparing camera locations with Chicago crime data.

### Chicago Crime 2017

The 2017 Chicago crime dataset contains 269,349 records and 22 columns. The dataset contains crime information including date, crime type, arrest status, geographic information, and location.

There are missing values in several fields. The largest issue is missing geographic information, with 4,413 records missing latitude and longitude. There are also 1,375 missing location description values, 1 missing district, 1 missing ward, and 15 missing community area values.

There are no duplicate rows or duplicate IDs. The Date column was originally stored as a string and was converted to a datetime format for time-based analysis.

### Chicago Crime 2026

The 2026 Chicago crime dataset contains 167,474 records and 22 columns. The data covers January 1, 2026 through September 20, 2026, so it represents year-to-date crime rather than a complete year.

There are 758 missing Location Description values, 1 missing Community Area value, and 304 records missing latitude, longitude, and other geographic location information. There are no duplicate rows or duplicate IDs, and no invalid geographic coordinates were found.

The Date column was converted from a string to datetime format for analysis.

## 2. Anomalies

| Dataset         | Anomaly                        |  Rows Affected | Action                                   |
| --------------- | ------------------------------ | -------------: | ---------------------------------------- |
| ALPR            | Missing values                 |              0 | None needed                              |
| ALPR            | Duplicate rows                 |              0 | None needed                              |
| ALPR            | Duplicate IDs                  |              0 | None needed                              |
| ALPR            | Invalid coordinates            |              0 | None needed                              |
| Crime 2017      | Missing geographic coordinates |          4,413 | Retained; excluded from geographic plots |
| Crime 2017      | Missing Location Description   |          1,375 | Retained and flagged                     |
| Crime 2017      | Missing District               |              1 | Retained and flagged                     |
| Crime 2017      | Missing Ward                   |              1 | Retained and flagged                     |
| Crime 2017      | Missing Community Area         |             15 | Retained and flagged                     |
| Crime 2026      | Missing geographic coordinates |            304 | Retained; excluded from geographic plots |
| Crime 2026      | Missing Location Description   |            758 | Retained and flagged                     |
| Crime 2026      | Missing Community Area         |              1 | Retained and flagged                     |
| Crime 2017/2026 | Date stored as string          |    All records | Converted to datetime                    |
| Crime 2026      | Partial year                   | Entire dataset | Treated as 2026 YTD                      |

No rows were dropped from the original datasets because the missing values were limited to specific fields. Records with missing coordinates were excluded only when creating geographic visualizations that require latitude and longitude.

## 3. Distributions

### ALPR Camera Distribution

The ALPR dataset contains substantially more Flock cameras than non-Flock cameras. About 74.8% of records are identified as Flock cameras, while 25.2% are non-Flock cameras.

The latitude and longitude distributions show that the ALPR dataset covers a broad geographic area and is not limited to Chicago. This is why a Chicago geographic subset was used for the relationship analysis.

### Crime Type Distribution

The most common crime types in both 2017 and 2026 are concentrated among a small number of categories. In 2017, theft and battery were the most common reported crimes. In 2026, theft and battery were the most common, followed by criminal damage, assault, and motor vehicle theft.

This uneven distribution suggests that crime type should be considered when examining relationships between Flock cameras and reported crime.

### Monthly Crime Distribution

Reported crime counts vary throughout the year. In 2017, July had the highest monthly crime count, while February was among the lowest.

In 2026, crime counts generally increased from January through July, with July having the highest count among the complete months. September has a lower count because the dataset only includes incidents through September 20.

### Geographic Crime Distribution

The latitude and longitude distributions for 2026 show that reported crimes are concentrated within the geographic range of Chicago. There are no invalid coordinates, although 304 records have missing geographic information.

## 4. Relationships

### Relationship 1: Flock Cameras and Reported Crime Locations

The first relationship plot compares the geographic locations of reported crimes with Flock camera locations in Chicago in 2026.

The spatial distribution shows some overlap between reported crime and Flock camera locations. Several cameras appear in areas with higher concentrations of reported crime, but many cameras are also located outside the densest crime groups.

### So What?

This suggests that Flock camera placement is not determined solely by reported crime density. However, this plot is descriptive and does not measure the strength of the relationship statistically.

### What Next?

A useful next step is to compare the number of Flock cameras with the number of reported crimes across smaller geographic areas within Chicago.

### Relationship 2: Crime Type and Arrest Rate

The second relationship plot compares arrest rates across the ten most common crime types in Chicago in 2026.

Arrest rates vary substantially across crime types. Narcotics has an arrest rate of aroud 94.9%, while theft has an arrest rate of 9.0%. Other common crimes, including criminal damage, motor vehicle theft, burglary, and deceptive practice, have even lower arrest rates.

### So What?

The likelihood of an arrest varies considerably depending on the type of crime reported. This shows that crime outcomes are not consistent across crime categories. However, this relationship does not show whether Flock cameras contributed to arrests or crime outcomes.

### What Next?

A useful next step would be to examine whether the relationship between Flock cameras and reported crime differs for specific crime types, such as theft, battery, or motor vehicle theft.

### Relationship 3: Flock Cameras and Reported Crime by Geographic Area

The third relationship plot compares the number of Flock cameras with the number of reported crimes within geographic areas of Chicago.

The scatter plot suggests a weak and inconsistent relationship between the number of Flock cameras and reported crime. Areas with few or no Flock cameras show a wide range of reported crime levels, including some of the highest crime counts. As the number of cameras increases, there is no clear upward or downward trend in reported crime.

### So What?

This suggests that the number of Flock cameras in a geographic area is not strongly associated with the number of reported crimes. This is important because simply having more Flock cameras in an area does not necessarily correspond to having more reported crime.

### What Next?

A useful next step would be to examine whether this relationship changes for specific types of crime. This could show whether Flock cameras are more commonly located in areas with certain types of reported crime rather than overall crime.

## 5. Overall Findings

The exploratory analysis shows some geographic overlap between Flock cameras and reported crime in Chicago, but the number of Flock cameras in an area does not show a strong or consistent relationship with the number of reported crimes.

Crime types also have different arrest rates. Narcotics has a much higher arrest rate than the other common crime categories, while crimes such as theft, burglary, and motor vehicle theft have relatively low arrest rates.

The analysis identified missing geographic information in the crime datasets. These records were retained in the original datasets but excluded from geographic plots when latitude or longitude was missing.

The 2026 crime dataset only covers January through September 20, 2026, so it should be treated as year-to-date data rather than a complete year.

Overall, the findings suggest that Flock camera placement should be examined more closely by crime type and geographic area rather than assuming that more cameras correspond to more reported crime.
