import scrapy
from geopy.geocoders import Nominatim
import re

rating_parts_types = {
    'Питание': 'rating__food',
    'Обслуживание': 'rating__service',
    'Цена/качество': 'rating__price_quality',
    'Атмосфера': 'rating__atmosphere'
}

SPbDistricts = [
    'адмиратлейский',
    'василеостровский',
    'выборгский',
    'калининский',
    'кировский',
    'колпинский',
    'красногвардейский',
    'красносельский',
    'кронштадский',
    'курортный',
    'московский',
    'невский',
    'петроградский',
    'петродворцовый',
    'приморский',
    'пушкинский',
    'фрунзенский',
    'центральный'
]

geoloc = Nominatim(user_agent='TripAdv')


class TripAdvisorRestaurantsSpider(scrapy.Spider):
    name = 'TripAdvisor_restaurants'
    allowed_domains = ['tripadvisor.ru']
    start_urls = ['http://tripadvisor.ru/Restaurants-g298507-St_Petersburg_Northwestern_District.html/']
    custom_settings = {
        'FEED_URI': 'tripadvisor_restaurants.json',
        'FEED_EXPORT_ENCODING': 'utf-8',
        'FEED_FORMAT': 'json'
    }

    def parse(self, response):
        current_pagination_hrefs = map(
            lambda x: x.get(),
            response.xpath('//div[@class="_1llCuDZj"][not(@data-test="SL_list_item")]'
                           '//ancestor::a[@class="_15_ydu6b"]/@href'))

        for href in current_pagination_hrefs:
            url = response.urljoin(href)

            yield scrapy.Request(url, callback=self.parse_restaurant)

        next_page = response.xpath(
            '//div[@class="unified pagination js_pageLinks"]/a[contains(@class, "next")]/@href')
        if next_page:
            yield scrapy.Request(response.urljoin(next_page.get()), callback=self.parse)

    def parse_restaurant(self, response):
        restaurant = {}
        restaurant['name'] = response.xpath('//h1[@data-test-target="top-info-header"]/text()').get()
        address = response.xpath('//a[@class="_15QfMZ2L"][@href="#MAPVIEW"]/text()')
        if address:
            restaurant['address'] = address.get()
        else:
            address = response.xpath(
                '//div[@class="_2vbD36Hr _36TL14Jn"][span[contains(@class, "map-pin-fill")]]'
                '//span[@class="_2saB_OSe"]/text()')
            if address:
                restaurant['address'] = address.get()
            else:
                restaurant['address'] = None

        if not (restaurant['address'] is None):
            addr = restaurant['address'].split(',')[0].lower()
            addr_splited = restaurant['address'].split(',')
            if len(addr_splited) > 1:
                bld = get_building(addr_splited[1])
            else:
                bld = get_building(addr_splited[0])
            
            addr = addr.replace('пр.', ' ') \
                        .replace('ул.', ' ') \
                        .replace('наб.', ' ') \
                        .replace('пр-кт', ' ') \
                        .replace('пр-т', ' ') \
                        .replace('проспект', ' ') \
                        .replace('просп.', ' ') \
                        .replace('просп ', ' ') \
                        .replace(' просп', ' ') \
                        .replace('ш.', ' ') \
                        .replace('.', ' ') \
                        .replace('бул.', ' ') \
                        .replace('бульвар', ' ') \
                        .replace('переулок', ' ') \
                        .replace('пер.', ' ') \
                        .replace(' пер ', ' ') \
                        .replace('васильевского острова', ' ') \
                        .replace('в.о.', ' ') \
                        .replace('пл.', ' ') \
                        .replace('площадь', ' ') \
                        .replace('канал', ' ') \
                        .replace(' кан ', ' ') \
                        .replace('кан.', ' ') \
                        .replace('.', ' ') \
                        .replace('-', ' ') + ' спб '

            loc = geoloc.geocode(addr, timeout=15)
            if loc:
                loc1 = str(loc).lower()
                district = re.search(', (.*?) район', loc1)
                if district is None:
                    district = re.search(', (.*?) district', loc1)
                if not (district is None):
                    district = district.group(1).split(' ')[-1]
                    restaurant['district'] = district
                else:
                    restaurant['district'] = None

                loc2 = geoloc.geocode(addr + ' ' + str(bld), timeout=15)
                if loc2:
                    lat, lon = loc2.latitude, loc2.longitude
                else:
                    lat, lon = loc.latitude, loc.longitude
                restaurant['coords'] = {
                    'coords__lat': lat,
                    'coords__lon': lon
                }
            else:
                restaurant['district'] = None
                restaurant['coords'] = None
        else:
            restaurant['district'] = None
            restaurant['coords'] = None

        rating__parts = {
            rating_parts_types[t.get()]: int(rate.get().split('_')[-1]) / 10
            for t, rate in zip(
                response.xpath(
                    '//div[@class="jT_QMHn2"]/span[@class="_2vS3p6SS"]/text()'),
                response.xpath(
                    '//div[@class="jT_QMHn2"]/span[@class="_377onWB-"]/span/@class')
            )
        }
        restaurant['rating'] = {}
        rating__mean = response.xpath('//span[@class="r2Cf69qf"]/text()').get()
        if rating__mean:
            restaurant['rating']['rating__mean'] = float(rating__mean.replace(',', '.'))
        else:
            restaurant['rating']['rating__mean'] = None
        restaurant['rating']['rating__food'] = rating__parts['rating__food'] \
            if 'rating__food' in rating__parts.keys() \
            else None
        restaurant['rating']['rating__service'] = rating__parts['rating__service'] \
            if 'rating__service' in rating__parts.keys() \
            else None
        restaurant['rating']['rating__price_quality'] = rating__parts['rating__price_quality'] \
            if 'rating__price_quality' in rating__parts.keys() \
            else None
        restaurant['rating']['rating__atmosphere'] = rating__parts['rating__atmosphere'] \
            if 'rating__atmosphere' in rating__parts \
            else None

        check_group = response.xpath('//a[@class="_2mn01bsa"][contains(text(), "$")]/text()').get()
        if check_group == '$':
            restaurant['check_group'] = 'Вкусно и недорого'
        elif check_group == '$$ - $$$':
            restaurant['check_group'] = 'По умеренной цене'
        elif check_group == '$$$$':
            restaurant['check_group'] = 'Рестораны высокой кухни'
        else:
            restaurant['check_group'] = 'Вкусно и недорого'

        kitchen_types = response.xpath(
            '//div[@class="_3UjHBXYa"]/div[div[@class="_14zKtJkz"]/text()="ТИП КУХНИ"]/div[@class="_1XLfiSsv"]/text()')
        if kitchen_types:
            restaurant['kitchen_types'] = kitchen_types.get().split(', ')
        else:
            restaurant['kitchen_types'] = None

        _comments = []
        comment = {}
        for r, c in zip(
                response.xpath('//div[@id="REVIEWS"]//span[contains(@class, "ui_bubble_rating")]/@class'),
                response.xpath('//div[@id="REVIEWS"]//p[@class="partial_entry"]/text()[not(ancestor::div[@class="mgrRspnInline"])]')):
            comment['comment__rating'] = int(r.get().split('_')[-1]) / 10
            comment['comment__body'] = c.get()

            _comments.append(comment)

        comments__count = response.xpath('//span[@class="reviews_header_count"]/text()').get()

        n_reviews_pages = response.xpath('//div[@id="REVIEWS"]//div[@class="pageNumbers"]/a/text()')
        if n_reviews_pages:
            n_reviews_pages = int(n_reviews_pages[-1].get())
            for i in range(1, n_reviews_pages):
                review_page_url = response.url.replace('Reviews-', 'Reviews-or'+str(i*10)+'-')
                yield scrapy.Request(review_page_url, callback=self.parse_comments, cb_kwargs={'_comments': _comments})

        if comments__count:
            restaurant['comments'] = {
                'comments__count': int(comments__count.replace('(', '') 
                                                        .replace(')', '')
                                                        .replace(' ', '')
                                                        .replace('\xa0', '')),
                'comments': _comments
            }
        if not comments__count or restaurant['comments']['comments'] == []:
            restaurant['comments'] = None

        yield restaurant

    def parse_comments(self, response2, _comments):
        comment = {}
        for r, c in zip(
                response2.xpath('//div[@id="REVIEWS"]//span[contains(@class, "ui_bubble_rating")]/@class'),
                response2.xpath('//div[@id="REVIEWS"]//p[@class="partial_entry"]/text()[not(ancestor::div[@class="mgrRspnInline"])]')):
            comment['comment__rating'] = int(r.get().split('_')[-1]) / 10
            comment['comment__body'] = c.get()

            _comments.append(comment)


def get_building(s):
    bld = 0
    for si in s:
        if si.isdigit():
            bld = bld*10 + int(si)
        elif bld != 0:
            break

    return bld if bld != 0 else ''
