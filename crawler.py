# coding=utf-8
from pyquery import PyQuery as pq
from config import *
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from random import randint
import time
import re

from datetime import datetime
from bs4 import BeautifulSoup
import traceback
import logging



logger = logging.getLogger('__name__')
logger.setLevel(logging.INFO)
# create a file handler
handler = logging.FileHandler('justeat.log')
handler.setLevel(logging.INFO)
# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(handler)



def save_to_mysql(result):
    try:
        cursor = conn.cursor()
        keys = ','.join(str(e) for e in list(result.keys()))
        values=','.join(['% s']*len(result))
        sql='insert into just_eat ({keys}) values ({values}) ON DUPLICATE KEY UPDATE '.format(keys=keys,values=values)
        update = ','.join(["{key} = % s".format(key=key) for key in result])
        sql+=update
        cursor.execute(sql,tuple(result.values())*2)
        conn.commit()
    except Exception as e:
        print(e)
        print(sql)
        conn.rollback()
    finally:
        cursor.close()
def get_restaurants(url,html,insert_time):
    doc = pq(html)
    try:
        items = doc('.c-listing-item.c-card.c-card--rounded--large').items()
        i = 0
        for item in items:
            i += 1
            restaurants = {
                'url':url,
                'href': item.find('.c-listing-item-link.u-clearfix').attr('href'),
                'name': item.find('[data-test-id=restaurant_name]').text(),
                'category': item.find('[data-test-id=restaurant_cuisines]').text(),
                'star': item.find('[data-test-id=review_avg]').text(),
                'review': item.find('.c-listing-item-ratingText').text(),
                'state': item.find('[data-test-id=restaurant_stateOffline]').text(),
                'delivery_free': item.find('[data-test-id=restaurant_delivery_details]').text(),
                'delivery_time': item.find('[data-test-id=restaurant_delivery_time]').text(),
                'delivery_eta': item.find('[data-test-id=restaurant_eta]').text(),
                'restaurant_preorder': item.find('[data-test-id=restaurant-preorder]').text(),
                'distance': item.find('[data-test-id=restaurant_location]').text(),
                'promoted': item.find('[data-test-id=restaurant_promo_text]').text(),
                'lables':item.find('[data-test-id=restaurant_labels]').text(),
                'insert_time':insert_time
                }
            save_to_mysql(restaurants)
        print(str(insert_time)+' '+url+' '+str(i)+' restaurant')
    except Exception as e:
        print(e)

def get_restaurants_uber(url,html,insert_time):
    soup = BeautifulSoup(html, 'lxml')
    try:
        divs = soup.select('div#root div#wrapper > div:nth-child(2) > div > div > div')
        i = 0
        for div in divs:
            i += 1             
            third_party=''           
            if div.select_one('a > div > div > div:nth-child(3) > div > div:nth-child(1) > div > img'):
                if div.select_one('a > div > div > div:nth-child(3) > div > div:nth-child(1) > div > img').attrs['src']=='https://d3i4yxtzktqr9n.cloudfront.net/web-eats-v2/e70f60bb6c2f67ac555bfc98021f50ea.svg':
                    third_party='True'
            restaurants = {
                'url':url,
                'href': '' if div.select_one('a') is None else div.select_one('a')['href'],
                'name': '' if div.select_one('a > div > div > div:nth-child(1)') is None else div.select_one('a > div > div > div:nth-child(1)').get_text(),
                'category': '' if  div.select_one('a > div > div > div:nth-child(2)') is None else div.select_one('a > div > div > div:nth-child(2)').get_text(),
                'star': '' if div.select_one('a > div > div > div:nth-child(3) > div > div:nth-child(3) > div') is None else div.select_one('a > div > div > div:nth-child(3) > div > div:nth-child(3) > div').get_text(),
                'review': '' if div.select_one('a > div > div > div:nth-child(3) > div > div:nth-child(3) > div > span') is None else div.select_one('a > div > div > div:nth-child(3) > div > div:nth-child(3) > div > span').get_text(),
                'state': '' if div.select_one('a > div > figure > figcaption > div') is None else div.select_one('a > div > figure > figcaption > div').get_text(),
                'delivery_free': '',
                'delivery_time': '',
                'delivery_eta': '' if div.select_one('a > div > div > div:nth-child(3) > div > div:nth-child(1) > div') is None else div.select_one('a > div > div > div:nth-child(3) > div > div:nth-child(1) > div').get_text(),
                'restaurant_preorder': '',
                'distance': '',
                'promoted': '',
                'lables':'',
                'insert_time':insert_time,
                'third_party':third_party
                }
            save_to_mysql(restaurants)
        print(str(insert_time)+' '+url+' '+str(i)+' restaurant')
    except Exception as e:
        print(e)

def get_page(browser, wait):
    try:
        for i in range(1):
                ActionChains(browser).key_down(Keys.PAGE_DOWN).key_up(Keys.PAGE_DOWN).perform()
        html = browser.page_source
        return html
    except Exception:
        print(Exception)

def main():
    try:
        urls_justeat=['https://www.just-eat.co.uk/area/tn1-tonbridge','https://www.just-eat.co.uk/area/tn10-tonbridge']
        url_uber='https://www.ubereats.com/en-GB/feed/?pl=JTdCJTIyYWRkcmVzcyUyMiUzQSUyMlJveWFsJTIwVHVuYnJpZGdlJTIwV2VsbHMlMjIlMkMlMjJyZWZlcmVuY2UlMjIlM0ElMjJDaElKMmZnSkFaODQzMGNSWktkMjhUdDZVSE0lMjIlMkMlMjJyZWZlcmVuY2VUeXBlJTIyJTNBJTIyZ29vZ2xlX3BsYWNlcyUyMiUyQyUyMmxhdGl0dWRlJTIyJTNBNTEuMTMyMzc3JTJDJTIybG9uZ2l0dWRlJTIyJTNBMC4yNjM2OTUlN0Q%3D'        
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        browser = webdriver.Chrome(chrome_options=chrome_options,executable_path='/home/ubuntu/justeat/chromedriver')
        wait = WebDriverWait(browser, 10)
        while True:
            hour=int(datetime.now().strftime('%H'))
            print(datetime.now().strftime('%d/%m/%y %H:%M:%S')+'  '+str(hour))
            if (hour>7 and hour<23): 
                browser.get('https://www.google.com')
                insert_time=datetime.now()
                for cookie in cookies_justeat:
                    browser.add_cookie(cookie)
                for cookie in cookie_uber:
                    browser.add_cookie(cookie)
                for url in urls_justeat:
                    browser.get(url)
                    html = get_page(browser, wait)
                    get_restaurants(url,html,insert_time)
                    time.sleep(randint(5, 20)/10)
                #todo wait until a tag appear
                for cookie_uber_addon in cookie_uber_addons:
                    browser.delete_cookie('uev2.loc') 
                    browser.add_cookie(cookie_uber_addon)
                    browser.get(url_uber)
                    time.sleep(randint(30, 50)/10)
                    html = get_page(browser, wait)
                    get_restaurants_uber(url_uber,html,insert_time)
                    time.sleep(randint(5, 20)/10)
                # set every 20 minutes 
                time.sleep(600+randint(10, 100)/10)
            else:
                time.sleep(600+randint(10, 100)/10)            
    except Exception as e:
        print(Exception)
    finally:
        browser.close()
        conn.close()
if __name__=='__main__':
    main()