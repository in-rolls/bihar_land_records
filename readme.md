### Bihar Land Records

We scrape the [Bihar Land Records](http://land.bihar.gov.in/Ror/RoR.aspx). 

### Data and Data Dictionary

The data are hosted on Harvard Dataverse at: https://doi.org/10.7910/DVN/BI4KZS
It is only available to researchers with a valid academic affiliation and with an approved IRB application.

#### Data Dictionary

v1 name_of_ryot
v2 name_of_father
v3 residence
v4 jati
v5 thana
v5 district
v6 anchal
v7 village
v8 khatadari // account holder number
c1 khata 
c2 name_of_ryot2
c3 khasra // plot number
c4 khet_boundary
c5 land_type
c6 area_acre
c7 area_decimal
c8 area_hectare
c9 dhakal_swaroop
c10 lagaan
c11 terms
c12 gair_dakhildar
c13 orders
c14 jamabandi

### Steps

1. Iterate over all the districts
2. Within each district, you get an excel file. You can also iterate over the subdivisions.
3. Within each subdivision, there is a list of 'Maujas' (see the box with list in the [picture](bihar.png))
4. Click on the second bullet point (see the picture)
5. Click on search
6. Click on 'see' ---see the picture
7. download the html and link to it in a metadata CSV
8. parse the html

### Outputs

1. Metadata CSV that links geographic metadata to individual land record files
2. CSV with land record data (can be multiple rows per record)
