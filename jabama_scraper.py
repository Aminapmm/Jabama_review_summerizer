
from bs4 import BeautifulSoup as bs
from requests import Session
import requests
import re
import random
from urllib.parse import urljoin
import pandas as pd
persian_months = ['فروردین','اردیبهشت','خرداد','تیر','مرداد','شهریور','مهر','آبان','آذر','دی','بهمن','اسفند']

def scrape_page(URL="") -> dict:
    if URL == "":
        return "enter a valid url"
    proxies = {'http':'http://185.172.214.112:80'}
    ses = requests.Session()
    ses.proxies.update(proxies)
    res = ses.get(url=URL)
    hotel = {}
    place= bs(res.content.decode('utf-8'),features='lxml')
    #info = list(map(lambda x:bs.get_text(x).strip(),place.find_all(class_=["product-card-header-name","pricing-main","rating-box-text rating-box-text__rate text-sm text-bold","rating-box-text text-sm text-light","product-card-info__item"])))


    """
    get the place id
    """
    apartment_id = re.search("\d{6,}",URL).group()
    params = {
        'reversePeriods': 'true',
        'withPanoramic': 'true',
    }

    response = requests.get(f'https://gw.jabama.com/api/v1/accommodations/{apartment_id}', params=params)

    
    hotel['rating']=place.find(class_="rating-box__score").text.strip("\n \n")
    hotel['title'] = place.find("title").text.strip("\n \n")
    hotel['city'] = place.find(class_="city-province").text.strip("\n \n")


    hotel['profile']=urljoin("https://www.jabama.com",place.find("a")['href'])
    hotel['place_id'] = response.json()['result']['item']['id']
    hotel['#comments'] = response.json()['result']['meta']['reviews']['reviewsCount']
    """
    Extract Comments
    """
    response = requests.get(f"https://gw.jabama.com/api/v2/reviews/place/{hotel['place_id']}", params={'size': str(hotel['#comments'])})

    df=pd.DataFrame.from_dict(response.json()['result']['reviews'])

    df=df.drop(columns=['image','reviewInfo','response'])
    df['comment']=df['comment'].str.replace("\n",".")
    df['subTitles']=df['subTitles'].apply(lambda x:x[0])

    """
    be Aware Below line will delete rows which belong to recent reviews
    """
    df1=df.loc[df['subTitles'].str.contains("|".join(persian_months))]
    df1[['month','year']] = df1['subTitles'].str.split(" ",expand=True)
    df1.drop(columns=['subTitles'],inplace=True)

    hotel['reviews'] = df1.to_dict()
    return hotel

