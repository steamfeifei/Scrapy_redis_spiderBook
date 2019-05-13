# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


class BookPipeline(object):
    def open_spider(self, spider):
        # self.txt_channel = open('txt_save', 'a+', encoding='utf-8')
        self.txt_channel = open('txt_save1', 'a+', encoding='utf-8')

    def process_item(self, item, spider):
        self.txt_channel.write(str(item) + '\n')
        self.txt_channel.flush()
        return item

    def close_spider(self, spider):
        self.txt_channel.close()