# -*- coding: utf-8 -*-

import time
import os
import re
import gzip
from base64 import b64decode
from turtle import circle
import pandas as pd
from datetime import datetime

from urllib.parse import urlparse, parse_qs

import scrapy
from scrapy.http import FormRequest

from ..items import (DistrictItem, AccountItem, RightItem)

from lxml import html

DEBUG = False


class BiharLandSpider(scrapy.Spider):
    #download_delay = 1
    name = 'bihar_land'
    allowed_domains = ['land.bihar.gov.in']
    start_urls = ['http://land.bihar.gov.in/Ror/RoR.aspx']

    def save_gzip_file(self, response, filename):
        fn = filename + '.gz'
        with gzip.open(fn, 'wb') as f:
            f.write(response.body)
        self.logger.info('Saved file {}'.format(fn) )
        return fn

    def parse(self, response):
        # Parse Districts from Image Map
        """
            How to pass argument to spider:-
            arg = getattr(self, 'arg', None)

            Command line:-
            scrapy crawl myspider -a arg=foo
        """
        if not os.path.exists('./html'):
            os.makedirs('./html')
        if not os.path.exists('./excel'):
            os.makedirs('./excel')

        page = response.meta.get('page', 0)
        cookiejar = response.meta.get('cookiejar', None)

        filter = getattr(self, 'filter', 'all')
        districts = getattr(self, 'districts', None)
        detail = getattr(self, 'detail', 'no')
        if districts:
            dist_list = [int(a.strip()) for a in districts.split(',')]
        else:
            dist_list = []

        self.logger.info('Arguments: filter={!s}, districts={!s}, detail={!s}'.format(filter, districts, detail))

        for i, area in enumerate(response.xpath("//area[re:test(@href, '.*ImageMap1.*')]")):
            title = area.attrib['title']
            if (dist_list == []) or (i in dist_list):
                self.logger.info("Parse District from Image Map: %d, %r, %s" % (i, area, title))
                href = area.attrib['href'].strip()
                m = re.match(".*?\((.*?)\,(.*?)\)", href)
                if m:
                    target = m.group(1).replace("'", "")
                    arg = m.group(2).replace("'", "")
                    yield FormRequest.from_response(response,
                        formdata={'__EVENTTARGET': target, '__EVENTARGUMENT': arg},
                        callback = self.parse_district,
                        dont_click = True,
                        dont_filter = True,
                        meta={'src': 'home', 'title': title, 'fork_from_cookiejar': cookiejar, 'cookiejar': str(page * 1000 + i + 1)})
            else:
                self.logger.info("Skip District from Image Map: %d, %r, %s" % (i, area, title))

    def parse_district(self, response):
        # Parse Zones from Image Map
        self.logger.info('Parse District URL %s (meta=%r)' % (response.url, response.meta))
        dist_name = response.xpath("//span[@id='ContentPlaceHolder1_distName']/text()").extract()
        self.logger.info('Parse District: %s' % dist_name)
        dfs = pd.read_html(response.body, attrs={'id': 'ContentPlaceHolder1_gvScreen'})
        fn = 'excel/ROR_{!s}_{!s}.xlsx'.format(dist_name[0], datetime.now().strftime('%Y%m%d'))
        self.logger.info('Save District to Excel: %s' % fn)
        dfs[0].to_excel(fn, index=False)
        item = DistrictItem()
        item['District'] = dist_name[0]
        item['Zone'] = response.xpath("//span[@id='ContentPlaceHolder1_lblCir']/text()").extract()[0].strip()
        item['Mau'] = response.xpath("//span[@id='ContentPlaceHolder1_lblMau']/text()").extract()[0].strip()
        item['Holder'] = response.xpath("//span[@id='ContentPlaceHolder1_lblHoldr']/text()").extract()[0].strip()
        item['Khata'] = response.xpath("//span[@id='ContentPlaceHolder1_lblKhata']/text()").extract()[0].strip()
        item['Khesra'] = response.xpath("//span[@id='ContentPlaceHolder1_lblKhesra']/text()").extract()[0].strip()
        item['Excel'] = fn
        #yield item
        for i, area in enumerate(response.xpath("//area[re:test(@href, 'ViewRor.aspx.*')]")):
            title = area.attrib['title']
            href = area.attrib['href'].strip()
            url = 'http://land.bihar.gov.in/Ror/' + href
            self.logger.info('Parse Zone from Image Map: %d, %s, %s' % (i, title, url))
            yield FormRequest(url,
                callback = self.parse_zone,
                dont_filter = True,
                meta={'item': item, 'cookiejar': response.meta['cookiejar']})
            if DEBUG:
                break

    def parse_account_items(self, response):
        # Parse Account Items
        tree = html.fromstring(response.body.decode('utf-8'))
        result = tree.xpath("//span[@id='ContentPlaceHolder1_LblSearchResult']/b/text()")
        l = len(result)
        dist = ''
        subdiv = ''
        z = ''
        mauja = ''
        if l > 1:
            dist = result[1]
        if l > 2:
            subdiv = result[2]
        if l > 3:
            z = result[3]
        if l > 4:
            mauja = result[4]
        rows = []
        for i, e in enumerate(tree.xpath("//table[@id='ContentPlaceHolder1_GridView1']/tr[position()>=2 and position()<=(last() - 1)]")):
            r = []
            for e2 in e.xpath('./td'):
                a = e2.xpath('./descendant-or-self::*/text()')
                r.append(''.join(a))
            r = [c.strip() for c in r[:-1]]
            url = 'http://land.bihar.gov.in/Ror/' + e.xpath(".//a[starts-with(@id, 'ContentPlaceHolder1_GridView1_hlDetails1_')]")[0].attrib['href'].replace(' ', '')
            r.append(url)
            # Account Holder No
            qs = parse_qs(urlparse(url).query)
            r.append(qs['LHID'][0])
            r.extend([dist, subdiv, z, mauja])
            rows.append(r)
        return rows

    def parse_zone_step3(self, response):
        # Step 3: Parse Account List and Pagination
        item = response.meta['item']
        page = response.meta['page']
        self.logger.info('Parse Zone Step 3 Page %d URL %s (item=%r)' % (page, response.url, item))
        dist_code = item['district_code']
        zone = item['Zone']
        sub_div_code = item['sub_div_code']
        circle_code = item['circle_code']
        index = response.meta['index']
        if DEBUG:
            fn = 'html/%s-%s-%s-%s-%d-%d.html' % (dist_code, zone, sub_div_code, circle_code, index, page)
            with open(fn, 'wb') as f:
                f.write(response.body)
        rows = self.parse_account_items(response)
        df = pd.DataFrame(rows, columns=AccountItem.fields_to_export)
        for i in df.to_dict(orient='records'):
            acc_item = AccountItem(i)
            yield acc_item
        # For all page:
        state = ''
        gen = ''
        for m in re.finditer(r'\|__VIEWSTATE\|(.*?)\|', response.body.decode('utf-8')):
            state = m.group(1)
        for m in re.finditer(r'\|__VIEWSTATEGENERATOR\|(.*?)\|', response.body.decode('utf-8')):
            gen = m.group(1)
        self.logger.debug('VIEWSTATEGENERATOR=%s, len(VIEWSTATE)=%d, URL=%s' % (gen, len(state), response.url))
        head = {'X-MicrosoftAjax': 'Delta=true', 'X-Requested-With': 'XMLHttpRequest'}
        try:
            lblmsg = response.xpath("//span[@id='ContentPlaceHolder1_LblMsg']/text()").extract()[0]
            n = int(lblmsg.split('-')[-1])
        except Exception as e:
            self.logger.error(e)
            n = 0
        self.logger.info("Parse Zone Step 3 Result Count=%d (dist_code=%s,zone=%s,sub_div_code=%s,circle_code=%s,index=%d,page=%d)" % (n, dist_code, zone, sub_div_code, circle_code, index, page))
        if DEBUG:
            page_count = 2
        else:
            page_count = n // 40 + 1
        page += 1
        if page <= page_count:
            form = FormRequest(response.url,
                    formdata={'__EVENTTARGET': 'ctl00$ContentPlaceHolder1$GridView1', '__EVENTARGUMENT': 'Page$%d' % page,
                    '__VIEWSTATEGENERATOR': gen, '__VIEWSTATE': state,
                    'ctl00$ContentPlaceHolder1$ScriptManager1': 'ctl00$ContentPlaceHolder1$UpdatePanel2|ctl00$ContentPlaceHolder1$GridView1',
                    'ctl00$ContentPlaceHolder1$DDLdistrict': item['district_code'],
                    'ctl00$ContentPlaceHolder1$DDLSubDiv': item['sub_div_code'],
                    'ctl00$ContentPlaceHolder1$DDLCircle': item['circle_code'],
                    'ctl00$ContentPlaceHolder1$SE': 'RadioButton5',
                    'ctl00$ContentPlaceHolder1$txtKhataNo': 'Disabled',
                    'ctl00$ContentPlaceHolder1$txtKhesraNo': 'Disabled',
                    'ctl00$ContentPlaceHolder1$txtName': 'Disabled',
                    '__ASYNCPOST': 'true',
                    '__SCROLLPOSITIONX': '0',
                    '__SCROLLPOSITIONY': '0',
                    '__LASTFOCUS': ''
                    },
                    callback = self.parse_zone_step3,
                    dont_filter = True,
                    headers=head,
                    meta={'item': response.meta['item'], 'page': page, 'index': index})
            yield form

    def parse_zone_step2(self, response):
        # Parse Zone Step 2 - Click Account Search Button
        item = response.meta['item']
        self.logger.info('Parse Zone Step 2 URL %s (item=%r, index=%d)' % (response.url, item, response.meta['index']))
        gen = response.xpath("//input[@id='__VIEWSTATEGENERATOR']/@value").extract()[0]
        state = response.xpath("//input[@id='__VIEWSTATE']/@value").extract()[0]
        head = {'X-MicrosoftAjax': 'Delta=true', 'X-Requested-With': 'XMLHttpRequest'}
        form = FormRequest.from_response(response,
                  formdata={'__EVENTTARGET': '', '__EVENTARGUMENT': '',
                  '__VIEWSTATEGENERATOR': gen, '__VIEWSTATE': state,
                  'ctl00$ContentPlaceHolder1$ScriptManager1': 'ctl00$ContentPlaceHolder1$ScriptManager1|ctl00$ContentPlaceHolder1$BtnSearch',
                  'ctl00$ContentPlaceHolder1$DDLdistrict': item['district_code'],
                  'ctl00$ContentPlaceHolder1$DDLSubDiv': item['sub_div_code'],
                  'ctl00$ContentPlaceHolder1$DDLCircle': item['circle_code'],
                  'ctl00$ContentPlaceHolder1$SE': 'RadioButton5',
                  'ctl00$ContentPlaceHolder1$txtKhataNo': 'Disabled',
                  'ctl00$ContentPlaceHolder1$txtKhesraNo': 'Disabled',
                  'ctl00$ContentPlaceHolder1$txtName': 'Disabled',
                  'ctl00$ContentPlaceHolder1$BtnSearch': 'खाता खोजें',
                  '__ASYNCPOST': 'true',
                  '__SCROLLPOSITIONX': '0',
                  '__SCROLLPOSITIONY': '0',
                  '__LASTFOCUS': ''
                  },
                  callback = self.parse_zone_step3,
                  dont_click = True,
                  dont_filter = True,
                  headers=head,
                  meta={'item': response.meta['item'], 'gen': gen, 'state': state, 'page': 1, 'index': response.meta['index']})
        yield form

    def parse_zone_step1(self, response):
        # Parse Zone Step 1 - Select Mauja from List
        item = response.meta['item']
        self.logger.info('Parse Zone Step 1 URL %s (item=%r)' % (response.url, item))
        dist_code = item['district_code']
        sub_div_code = item['sub_div_code']
        circle_code = item['circle_code']
        zone = item['Zone']
        gen = response.xpath("//input[@id='__VIEWSTATEGENERATOR']/@value").extract()[0]
        state = response.xpath("//input[@id='__VIEWSTATE']/@value").extract()[0]
        for tr in response.xpath("//table[@id='ContentPlaceHolder1_GridView2']/tr"):
            if 'onclick' in tr.attrib:
                m = re.match('.*?(Select\$\d+).*$', tr.attrib['onclick'])
                if m:
                    sel = m.group(1)
                    index = int(sel.split('$')[1])
                    self.logger.info('Selecting %s (dist_code=%s,zone=%s,sub_div_code=%s,circle_code=%s)' % (sel, dist_code, zone, sub_div_code, circle_code))
                    form = FormRequest.from_response(response,
                            formdata={'__EVENTTARGET': 'ctl00$ContentPlaceHolder1$GridView2', '__EVENTARGUMENT': sel,
                            '__VIEWSTATEGENERATOR': gen, '__VIEWSTATE': state,
                            'ctl00$ContentPlaceHolder1$ScriptManager1': 'ctl00$ContentPlaceHolder1$UpdatePanel1|ctl00$ContentPlaceHolder1$GridView2',
                            'ctl00$ContentPlaceHolder1$DDLdistrict': dist_code,
                            'ctl00$ContentPlaceHolder1$DDLSubDiv': sub_div_code,
                            'ctl00$ContentPlaceHolder1$DDLCircle': circle_code,
                            'ctl00$ContentPlaceHolder1$SE': 'RadioButton5',
                            'ctl00$ContentPlaceHolder1$txtKhataNo': 'Disabled',
                            'ctl00$ContentPlaceHolder1$txtKhesraNo': 'Disabled',
                            'ctl00$ContentPlaceHolder1$txtName': 'Disabled',
                            },
                            callback = self.parse_zone_step2,
                            dont_click = True,
                            dont_filter = True,
                            meta={'item': item, 'index': index})
                    yield form
                    if DEBUG:
                        break

    def parse_zone(self, response):
        # Parse Zone - Select "View all Mauja accounts by Khesra number"
        item = response.meta['item']
        self.logger.info('Parse Zone URL %s (item=%r)' % (response.url, item))
        qs = parse_qs(urlparse(response.url).query)
        dist_code =  qs['DistCode'][0]
        sub_div_code = qs['SubDivCode'][0]
        circle_code = qs['CircleCode'][0]
        # must be update on the copy of item
        new_item = item.copy()
        new_item['district_code'] = dist_code
        new_item['sub_div_code'] = sub_div_code
        new_item['circle_code'] = circle_code
        yield new_item
        self.logger.info('Parse Zone dist_code = %s, subdiv_code = %s, circle_code = %s' % (dist_code, sub_div_code, circle_code))
        gen = response.xpath("//input[@id='__VIEWSTATEGENERATOR']/@value").extract()[0]
        state = response.xpath("//input[@id='__VIEWSTATE']/@value").extract()[0]
        form = FormRequest.from_response(response,
                formdata={'__EVENTTARGET': 'ctl00$ContentPlaceHolder1$RadioButton5', '__EVENTARGUMENT': '',
                '__VIEWSTATEGENERATOR': gen, '__VIEWSTATE': state,
                'ctl00$ContentPlaceHolder1$ScriptManager1': 'ctl00$ContentPlaceHolder1$UpdatePanel1|ctl00$ContentPlaceHolder1$RadioButton5',
                'ctl00$ContentPlaceHolder1$DDLdistrict': dist_code,
                'ctl00$ContentPlaceHolder1$DDLSubDiv': sub_div_code,
                'ctl00$ContentPlaceHolder1$DDLCircle': circle_code,
                'ctl00$ContentPlaceHolder1$SE': 'RadioButton5',
                'ctl00$ContentPlaceHolder1$txtKhataNo': 'Disabled',
                'ctl00$ContentPlaceHolder1$txtKhesraNo': 'Disabled',
                'ctl00$ContentPlaceHolder1$txtName': 'Disabled',
                },
                callback = self.parse_zone_step1,
                dont_click = True,
                dont_filter = True,
                meta={'item': new_item})
        yield form
