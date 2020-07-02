import scrapy


rating_parts_types = {
    'Питание': 'rating__food',
    'Обслуживание': 'rating__service',
    'Цена/качество': 'rating__price_quality',
    'Атмосфера': 'rating__atmosphere'
}


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

        district = response.xpath('//span[@class="_2saB_OSe _1OBMr94N"]/div')
        if district != []:
            restaurant['district'] = district[0].xpath('text()').get()
        else:
            restaurant['district'] = None

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
            restaurant['check_group'] = None

        kitchen_types = response.xpath(
            '//div[@class="_3UjHBXYa"]/div[div[@class="_14zKtJkz"]/text()="ТИП КУХНИ"]/div[@class="_1XLfiSsv"]/text()')
        if kitchen_types:
            restaurant['kitchen_types'] = kitchen_types.get().split(', ')
        else:
            restaurant['kitchen_types'] = None

        yield restaurant
