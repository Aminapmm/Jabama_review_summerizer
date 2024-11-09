import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from bidi.algorithm import get_display
import arabic_reshaper
import numpy as np
from wordcloud import WordCloud
from PIL import Image
from st_aggrid import AgGrid,GridOptionsBuilder


persian_months = ['فروردین','اردیبهشت','خرداد','تیر','مرداد','شهریور','مهر','آبان','آذر','دی','بهمن','اسفند']

def yearly_reservation(df:pd.DataFrame):
    monthly_passengers = df.groupby(by=['year','month']).agg(count=("year","count"))
    sort_key = {m:i for i,m in enumerate(persian_months,1)}
    monthly_passengers['month_number'] = [sort_key[m[1]] for m in monthly_passengers.index]
    monthly_passengers = monthly_passengers.sort_values(['year','month_number'],ascending=[True,False])
    fig,ax = plt.subplots()
    ax.set_title(get_display(arabic_reshaper.reshape("نمودار پراکندگی مسافران در ماه های مختلف سال")))
    years = monthly_passengers.index.levels[0]
    colors = np.random.rand(len(years),3)
    offset = 0

    for i,year in enumerate(years):
        x = monthly_passengers.loc[year]
        y = np.arange(len(x))
        rect = ax.barh(y+offset,x['count'],color=colors[i],label = year)
        ax.bar_label(rect, padding =3)
        offset += len(y)
        
    tick_labels = monthly_passengers.index.get_level_values(1).to_series().apply(lambda x:get_display(arabic_reshaper.reshape(x)))
    ax.set_yticks(np.arange(len(tick_labels)),tick_labels)
    ax.tick_params(labelsize='8', labelrotation=0, pad=2,length=3)
    ax.legend()

    st.pyplot(fig,use_container_width=True)

def generate_wordcloud(df:pd.DataFrame):
    
    farsi_text = get_display(arabic_reshaper.reshape("".join(df['comment'])))
    #TODO: set the dataframe here with filtering&selection rows
    abr = WordCloud(max_words = 100,font_path="C:/Users/Amin/Downloads/Yekan.ttf")
    frequencies = abr.process_text(farsi_text)
    data = abr.generate_from_frequencies(frequencies)
    c = st.container(border=True)
    img = Image.fromarray(data.to_array())
    base_width = 500
    wpercent = (base_width / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((base_width, hsize), Image.Resampling.LANCZOS)
    st.image(np.array(img),width=450)
