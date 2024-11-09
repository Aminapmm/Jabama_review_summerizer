import streamlit as st
from generate_graph import yearly_reservation,generate_wordcloud
from reviews_summary import *
from st_aggrid import AgGrid,GridOptionsBuilder,GridUpdateMode,DataReturnMode
#from st_aggrid.shared import DataReturnMode
from jabama_scraper import scrape_page
import pandas as pd
import re
import os
import json

grid_options = {
    'autoSizeStrategy':{
        'type':'fitGridWidth',
    },
    'columnDefs':[{'field':'comment','headerName':"نظرات",'width':200,'enableRangeSelection':True,'checkboxSelection':True,'rowSelection':"multiple"},
                  {'field':"month",'headerName':"ماه",'width':50,'enableRowGroup':True,'enableRangeSelction':True,'rowSelection':"multiple"},
                  {'field':"year",'headerName':"سال",'width':50,'enableRowGroup':True,'rowSelection':"multiple"}]
                  ,'rowGroupPanelShow':'always',
                  'rowSelection':"multiple",
                  'groupSelectsChildren':True              
}

def home():
    place_url = st.text_input(label=":آدرس صفحه اقامتگاه را وارد کنید", key="place_url",value="")
    
    place_id = ""

    if place_url !="":
        place_id = re.search("\d{6,}",place_url).group()
        st.session_state['place_id']=place_id

    if place_id !="":
        if not os.path.exists(f"{place_id}.json"):
            hotel = scrape_page(place_url) #hotel is an dict which contains information we need.
            with open(f'{place_id}.json','w') as f:
                json.dump(hotel,f)

        with open(f'{place_id}.json','r') as f:
            hotel = json.load(f)
        table(hotel)
    
    

    
def table(hotel:dict):
    
    df = pd.DataFrame.from_dict(hotel['reviews'])
    #Remove Nan comments
    df = df.loc[df['comment'].notnull()]

    st.subheader(f"**{hotel['title']}**",divider=True)

    tab1,tab2,tab3 = st.tabs(["Chart","Data","Reviews Summary"])

    summary = ""
    reviews = ""
    selected_reviews = df
    with tab1:
        col1,col2 = st.columns(2,gap='medium')
        with col1:
            st.header("آمار سالانه اقامتگاه",divider=True)
            yearly_reservation(df)
        with col2:
            st.header("ابر کلمات",divider=True)
            generate_wordcloud(df)    

    with tab2:
        ag = AgGrid(df,grid_options,data_return_mode = DataReturnMode.FILTERED_AND_SORTED,update_mode = GridUpdateMode.SELECTION_CHANGED)
        selected_reviews = ag.selected_data

        if st.button(label="اعمال تغییرات"):
            reviews = " ".join(df['comment'].to_list())

    
    with tab3:

        selected_reviews_grid = AgGrid(selected_reviews,{'autoSizeStrategy':{'type':'fitGridWidth'},'columnDefs':[{'field':'comment','headerName':"نظرات",'width':500}],'alwaysShowHorizontalScroll' : True})
        reviews = " ".join(selected_reviews['comment'].to_list())
            
        if st.button("خلاصه کن"):
            summary = get_review_summary(reviews)
                
        st.header("در این قسمت می‌توانید خلاصه‌نظرات را مطالعه کنید")
        message = st.chat_message('ai')
        #message.write("here is your summary")
        message.write(summary)

    
home()