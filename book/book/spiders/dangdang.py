# -*- coding: utf-8 -*-
import scrapy
from copy import deepcopy
import re
import json
import urllib
from scrapy import Selector
import logging
logger = logging.getLogger(__name__)


from scrapy_redis.spiders import RedisSpider    # distributed

class DangdangSpider(RedisSpider):   # distributed
    name = 'dangdang'
    # allowed_domains = ['book.dangdang.com', 'dangdang.com']
    # start_urls = ['http://book.dangdang.com/']       # distributed
    redis_key = 'dangdang'  # 原来spider文件中的start_urls没有了   # distributed

    # __init__方法必须按规定写，使用时只需要修改super()里的类名参数即可
    def __init__(self, *args, **kwargs):
        # 修改这里的类名为当前类名
        super(DangdangSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        print('Start spider....')
        item = {}

        level_ones = response.xpath("//div[@class='level_one ']")    # 一级分类集合
        print('一级目录集合：', level_ones)

        for one in level_ones:
            item['level_one_name'] = [content.strip() for content in one.xpath("./dl//text()").extract() if len(content.strip())>0]
            print('一级目录名称： ', item['level_one_name'])

            level_twos = one.xpath('.//dl[@class="inner_dl"]/dt')   # 二级分类集合

            for two in level_twos:
                item['level_two_name'] = [content.strip() for content in two.xpath('.//text()').extract() if len(content.strip())>0]
                print('二级目录名称： ', item['level_two_name'])

                level_three = two.xpath('../dd/a')

                for three in level_three:
                    print(type(three), type(level_three), type(two))
                    item['level_three_name'] = [content.strip() for content in three.xpath('./text()').extract() if len(content.strip())>0]
                    print('三级目录名称： ', item['level_three_name'])

                    item['level_three_urls'] = three.xpath('./@href').extract_first()
                    print('三级url: ', item['level_three_urls'])

                    yield scrapy.Request(
                        item['level_three_urls'],
                        callback=self.parse_book_show,
                        meta=deepcopy(item)
                    )

    def parse_book_show(self, response):
        item = response.meta


        current_book_list = response.xpath('.//ul[@class="bigimg"]/li')
        if not current_book_list:
            current_book_list = response.xpath('.//*[@id="d3150"]/ul/li')
        print('response_url: ', response.url, '--->current_book_list: ', current_book_list)

        for book_li in current_book_list:
            # item['title'] = book_li.xpath('./p[@class="name"]/a/text()').extract_first()
            # item['detail'] = book_li.xpath('./p[@class="detail"]/text()').extract_first()
            # item['price'] = book_li.xpath('./p[@class="price"]/span[@class="search_now_price"]/text()').extract_first()
            # item['price'] = re.findall(r'¥(.*)', item['price'])[0]
            # item['author'] = book_li.xpath('./p[@class="search_book_author"]/span[1]/a/text()').extract_first()
            # print('item[title] ', item)

            item['detail_url'] = book_li.xpath('.//a/@href').extract_first()
            print('detail_url: ', item['detail_url'])

            yield scrapy.Request(
                item['detail_url'],
                callback=self.parse_book_detail,
                meta=deepcopy(item)
            )

    def parse_book_detail(self, response):
        item = response.meta

        item['b_name'] = [content.strip() for content in response.xpath('.//div[@class="name_info"]/h1/text()').extract() if len(content.strip()) > 1]
        item['b_detail'] = [content.strip() for content in response.xpath('.//div[@class="name_info"]/h2/span[1]/text()').extract() if len(content.strip()) > 1]
        item['b_author'] = ''.join([content.strip() for content in response.xpath('.//div[@class="messbox_info"]/span[@id="author"]/a/text()').extract() if len(content.strip()) > 1])
        item['b_press'] = [content.strip() for content in response.xpath('.//div[@class="messbox_info"]/span[@id="出版社"]/a/text()').extract() if len(content.strip()) > 1]
        item['b_price'] = [content.strip() for content in response.xpath('.//div[@class="show_info"]//p[@id="dd-price"]/text()').extract() if len(content.strip()) > 1]
        item['b_comment'] = [content.strip() for content in response.xpath('.//div[@id="comment_list"]//a/text()').extract() if len(content.strip()) > 1]

        item['comment_nums'] = response.xpath('//*[@id="comment_num_tab"]/span[1]/text()').extract()

        prodSpuInfo = re.findall('prodSpuInfo = (.*?})', response.text)
        prodSpuInfo = json.loads(prodSpuInfo[0])
        print('prodSpuInfo: ', prodSpuInfo)

        # 短评url
        item['b_comment_short_url'] = 'http://product.dangdang.com/index.php?r=comment%2Flist&productId={0}&categoryPath={1}&mainProductId={2}&mediumId={4}&pageIndex=1&sortType=1&filterType=1&isSystem=1&tagId=0&tagFilterCount=0&template={3}'
        item['b_comment_short_url'] = item['b_comment_short_url'].format(prodSpuInfo.get('productId'), prodSpuInfo.get('categoryPath'), prodSpuInfo.get('mainProductId'), prodSpuInfo.get('template'), prodSpuInfo.get('mediumId'), )
        item['b_comment_short_strs'] = []     # 短评


        # 长评url
        item['b_comment_long_url'] = 'http://product.dangdang.com/index.php?r=comment%2Flist&productId={0}&categoryPath={1}&mainProductId={2}&mediumId={4}&pageIndex=1&sortType=1&filterType=1&isSystem=1&tagId=0&tagFilterCount=0&template={3}&long_or_short=long'
        item['b_comment_long_url'] = item['b_comment_long_url'].format(prodSpuInfo.get('productId'), prodSpuInfo.get('categoryPath'), prodSpuInfo.get('mainProductId'), prodSpuInfo.get('template'), prodSpuInfo.get('mediumId'), )
        item['b_comment_long_strs'] = []    # 长评

        # 长评请求
        yield scrapy.Request(
            item['b_comment_long_url'],
            callback=self.parse_book_long_comment,
            meta=item
        )

        from scrapy import Selector
        print('b_name: ', item['b_name'])
        print('b_detail: ', item['b_detail'])
        print('b_author: ', item['b_author'])
        print('b_press: ', item['b_press'])
        print('b_price: ', item['b_price'])
        print('comment_nums: ', item['comment_nums'])
        print('b_comment: ', item['b_comment'])
        print('b_comment_short_url: ', item['b_comment_short_url'])
        print('b_comment_long_url: ', item['b_comment_long_url'])




    # 短评
    def parse_book_short_comment(self,  response):
        item = response.meta
        comment_json_dict = json.loads(response.text)
        print('response.text: ', response.text)
        # print('comment_json_dict: ', comment_json_dict)

        # 处理返回的评论列表html
        comment_return_html = comment_json_dict.get('data').get('list').get('html')
        comment_body = Selector(text=comment_return_html).xpath('.//div[@class="describe_detail"]//a/text()').extract()
        item['b_comment_short_strs'].extend(comment_body)

        print('response.url: ',  response.url)
        # print('comment_body: ', comment_body)
        # print('len(comment_body): ', len(comment_body))

        page_short_counts = int(comment_json_dict.get('data').get('list').get('summary').get('pageCount'))
        page_short_index= int(comment_json_dict.get('data').get('list').get('summary').get('pageIndex'))


        print('==>:', re.sub('pageIndex=(\d+)', 'pageIndex=' + str(page_short_index + 1), item['b_comment_short_url']))
        print('page_short_counts: ', page_short_counts, 'page_short_index: ', page_short_index)
        if page_short_index < page_short_counts and page_short_index > 0:
            yield scrapy.Request(
                # item['b_comment_url'].replace()
                re.sub('pageIndex=(\d+)', 'pageIndex=' + str(page_short_index + 1), item['b_comment_short_url']),
                callback=self.parse_book_short_comment,
                meta=item
            )
        else:
            print('item[detail_url]: ', item['detail_url'])
            print('page_short_index: ', page_short_index, 'page_short_counts: ', page_short_counts)
            print('item[b_comment_short_strs]: ', item['b_comment_short_strs'])
            print('len(item[b_comment_short_strs]): ', len(item['b_comment_short_strs']))

            print('=========Spider End One ===============')
            print('item: ', item)
            logger.info(item)  # 输出到日志
            yield item

    # 长评
    def parse_book_long_comment(self,  response):
        item = response.meta
        comment_json_dict = json.loads(response.text)
        # print('comment_json_dict: ', comment_json_dict)

        # 处理返回的评论列表html   ==========> ??????????????看看内容分部
        comment_return_html = comment_json_dict.get('data').get('longlist').get('html')
        response_selector = Selector(text=comment_return_html)

        comment_counts = len(response_selector.xpath('.//div[@class="comment_items clearfix long_c"]'))
        print('comment_counts: ', comment_counts)
        for i in range(comment_counts):
            print('Text: comment_body: ', response_selector.xpath('.//div[@class="comment_items clearfix long_c"][{0}]//a/text()|.//div[@class="describe_detail"][{0}]//a/text()'.format(str(i + 1))))
            comment_body = ''.join([content.strip() for content in response_selector.xpath('.//div[@class="comment_items clearfix long_c"][{0}]//a/text()|.//div[@class="describe_detail"][{0}]//a/text()'.format(str(i + 1))).extract() if len(content.strip()) > 0])
            print('Text: comment_body1: ', comment_body)
            item['b_comment_long_strs'].append(comment_body)

        print('response.url: ',  response.url)

        page_long_counts = int(comment_json_dict.get('data').get('longlist').get('summary').get('pageCount'))
        page_long_index= int(comment_json_dict.get('data').get('longlist').get('summary').get('pageIndex'))


        print('page_long_counts: ', page_long_counts, 'page_long_index: ', page_long_index)
        print('item[b_comment_long_url]==>:', re.sub('pageIndex=(\d+)', 'pageIndex=' + str(page_long_index + 1), item['b_comment_long_url']))

        if page_long_index < page_long_counts and page_long_index > 0:
            yield scrapy.Request(
                re.sub('pageIndex=(\d+)', 'pageIndex=' + str(page_long_index + 1), item['b_comment_long_url']),
                callback=self.parse_book_long_comment,
                meta=item
            )
        else:
            print('item[detail_url]: ', item['detail_url'])
            print('page_long_index: ', page_long_index, 'page_long_counts: ', page_long_counts)
            print('item[b_comment_long_strs]: ', item['b_comment_long_strs'])
            print('len(item[b_comment_long_strs]): ', len(item['b_comment_long_strs']))

            # 短评请求
            yield scrapy.Request(
                item['b_comment_short_url'],
                callback=self.parse_book_short_comment,
                meta=item
            )

