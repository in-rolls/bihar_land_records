# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
import json
from collections import OrderedDict
import six


class OrderedItem(scrapy.Item):
    def __init__(self, *args, **kwargs):
        self._values = OrderedDict()
        if args or kwargs:
            for k, v in six.iteritems(dict(*args, **kwargs)):
                self[k] = v

    def __repr__(self):
        return json.dumps(OrderedDict(self),ensure_ascii = False)
        #ensure_ascii = False ,it make characters show in cjk appearance.


class DistrictItem(OrderedItem):
    fields_to_export = ['District', 'Zone', 'Mau', 'Holder', 'Khata', 'Khesra', 'Excel', 'district_code', 'sub_div_code', 'circle_code']
    District = scrapy.Field()
    Zone = scrapy.Field()
    Mau = scrapy.Field()
    Holder = scrapy.Field()
    Khata= scrapy.Field()
    Khesra = scrapy.Field()
    Excel = scrapy.Field()
    district_code = scrapy.Field()
    sub_div_code = scrapy.Field()
    circle_code = scrapy.Field()


class AccountItem(OrderedItem):
    fields_to_export = ['Order', 'Ryot_Holder_Name', 'Father_Husband_Name', 'Account_Number', 'Khresra_Number', 'Record_of_Rights', 'Account_Holder_No', 'District', 'Sub_Division', 'Zone', 'Mauja']
    Order = scrapy.Field()
    Ryot_Holder_Name = scrapy.Field()
    Father_Husband_Name = scrapy.Field()
    Account_Number = scrapy.Field()
    Khresra_Number = scrapy.Field()
    Record_of_Rights = scrapy.Field()
    Account_Holder_No = scrapy.Field()
    District = scrapy.Field()
    Sub_Division = scrapy.Field()
    Zone = scrapy.Field()
    Mauja = scrapy.Field()


class RightItem(OrderedItem):
    fields_to_export = ['District', 'Zone', 'Mauja', 'Account_Holder_No', 'Account_Number', 'Rayat_Name', 'Father_Husband_Name', 'Habitat', 'Caste', 'Revenue_Police_Station_No', 'Khesra Number']
    District = scrapy.Field()
    Zone = scrapy.Field()
    Mauja = scrapy.Field()
    Account_Holder_No = scrapy.Field()
    Account_Number = scrapy.Field()
    Rayat_Name = scrapy.Field()
    Father_Husband_Name = scrapy.Field()
    Habitat = scrapy.Field()
    Caste = scrapy.Field()
    Revenue_Police_Station_No = scrapy.Field()
    Khesra_Number = scrapy.Field()
