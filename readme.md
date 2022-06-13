### Bihar Land Records

We scrape the [Bihar Land Records](http://land.bihar.gov.in/Ror/RoR.aspx). 

### Steps

1. Iterate over all the districts
2. Within each district, you get an excel file. You can also iterate over the subdivisions.
3. Within each subdivision, there is a list of 'Maujas' (see the box with list in the [picture](bihar.png))
4. Click on the second bullet point (see the picture)
5. Click on search
6. Click on 'see' ---see the picture
7. download the html
8. parse the html