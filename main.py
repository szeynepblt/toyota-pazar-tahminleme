#Importing the dependencies
import joblib
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import confusion_matrix
from sklearn.neighbors import KNeighborsClassifier
import lightgbm as lgb
import pickle
import time
import datetime as dt
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import pymongo
import urllib.parse
import random as rnd
from io import BytesIO
from pyxlsb import open_workbook as open_xlsb
import xlsxwriter


#---------STREAMLIT------------
st.header('Toyota Pazar Tahminleme Sistemi') #Başlık

pazar=st.radio('Pazar Seçiniz:',('Binek Araçları Pazarı','Hafif Ticari Araç Pazarı'))

tekli_coklu=st.sidebar.radio("Seçiniz",("Tekli Tahmin","Çoklu Tahmin"))

if tekli_coklu=="Tekli Tahmin":
    st.sidebar.subheader('Ekonomik Değişkenler') #Değişken seçimi başlığı

    faiz=st.sidebar.text_input('Taşıt Kredi Faizi') #Taşıt Kredi Faizi input
    calisma_gunu=st.sidebar.text_input('Çalışma Günü') #Ay içerisindeki çalışma günü input
    guven_endeksi=st.sidebar.text_input('Tüketici Güven Endeksi') #Tüketici Güven Endeksi input
    enflasyon=st.sidebar.text_input('Aylık Enflasyon') #Aylık Enflasyon
    tufe=st.sidebar.text_input('TÜFE') #TÜFE Endeksi
    ay=st.sidebar.text_input('Ay') #Ay
    yil=st.sidebar.text_input('Yıl') #Ay

    sezonsallik = [-8336.58446876, -5422.31128824, 333.7142071, -622.93622349,
                   798.52677185, -104.26254763, -1205.4341307, -718.23560128,
                   560.4286144, -1291.69148364, 1177.36488891, 14831.42126146]

    ay_dict={'1':'Ocak','2':'Şubat','3':'Mart','4':'Nisan',
             '5':'Mayıs','6':'Haziran','7':'Temmuz','8':'Ağustos',
             '9':'Eylül','10':'Ekim','11':'Kasım','12':'Aralık'}

    pc_model=joblib.load('pc_model.pkl') #PC Modeli
    pc_scaler=joblib.load('pc_scaler.pkl') #PC Scaler

    lcv_model=joblib.load('lcv_model.pkl') #LCV Modeli
    lcv_scaler=joblib.load('lcv_scaler.pkl') #LCV Scaler

    market_data=pd.read_excel('marketdata.xlsx')
    market_data=market_data[['Tarih','PC_Market','LCV_Market']]
    market_data.dropna(inplace=True)
    market_data=market_data.set_index('Tarih')
    print(market_data)
    if pazar=='Binek Araçları Pazarı':
        st.line_chart(market_data['PC_Market'])
    elif pazar=='Hafif Ticari Araç Pazarı':
        st.line_chart(market_data['LCV_Market'])

    if st.sidebar.button('Tahmin Et'):
        try:
            sezonsallik_endeksi = sezonsallik[int(ay)-1]
            pc_prediction=pc_model.predict(pc_scaler.transform([[faiz,calisma_gunu,guven_endeksi,enflasyon,tufe,ay]]))[0]
            lcv_prediction = lcv_model.predict(
                lcv_scaler.transform([[faiz, sezonsallik_endeksi, calisma_gunu, guven_endeksi, enflasyon, tufe, ay]]))[0]
            st.subheader(f'{yil} {ay_dict[ay]} Binek Araçları Pazarı Tahmini: {int(pc_prediction):,}')
            st.subheader(f'{yil} {ay_dict[ay]} Hafif Ticari Araç Pazarı Tahmini: {int(lcv_prediction):,}')
            st.subheader(f'{yil} {ay_dict[ay]} Toplam Pazar: {(int(pc_prediction)+int(lcv_prediction)):,}')
        except:
            st.warning('Lütfen tüm alanları hatasız bir şekilde doldurunuz.')
else:
    sablon=pd.read_excel('sablon.xlsx')

    #Download Fonksiyonu
    def to_excel(df):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        format1 = workbook.add_format({'num_format': '0.00'})
        worksheet.set_column('A:A', None, format1)
        writer.save()
        processed_data = output.getvalue()

        return processed_data

    sezonsallik = [-8336.58446876, -5422.31128824, 333.7142071, -622.93622349,
                   798.52677185, -104.26254763, -1205.4341307, -718.23560128,
                   560.4286144, -1291.69148364, 1177.36488891, 14831.42126146]

    pc_model = joblib.load('pc_model.pkl')  # PC Modeli
    pc_scaler = joblib.load('pc_scaler.pkl')  # PC Scaler

    lcv_model = joblib.load('lcv_model.pkl')  # LCV Modeli
    lcv_scaler = joblib.load('lcv_scaler.pkl')  # LCV Scaler

    df_xlsx = to_excel(sablon)
    st.sidebar.download_button(label='📥 Şablonu İndir',
                       data=df_xlsx,
                       file_name='Şablon.xlsx')

    try:
        coklu_dosya=pd.read_excel(st.sidebar.file_uploader("Dosya Yükleme"))

        pc_ciktilar = []
        lcv_ciktilar = []
        for i in range(0, len(coklu_dosya)):
            sezonsallik_endeksi = sezonsallik[int(coklu_dosya.iloc[0]["Ay"]) - 1]
            x_pc = coklu_dosya.iloc[i].to_list()
            x_pc.append(coklu_dosya.iloc[i][1])
            x_pc = x_pc[2:]
            x_lcv = x_pc.copy()
            x_lcv.insert(1, sezonsallik_endeksi)
            pc_ciktilar.append(pc_model.predict(pc_scaler.transform([np.array(x_pc)]))[0])
            lcv_ciktilar.append(lcv_model.predict(lcv_scaler.transform([np.array(x_lcv)]))[0])
        coklu_dosya["Binek Araçları Pazarı"] = pc_ciktilar
        coklu_dosya["Hafif Ticari Araç Pazarı"] = lcv_ciktilar
        coklu_dosya["Toplam Pazar"] = coklu_dosya["Binek Araçları Pazarı"] + coklu_dosya["Hafif Ticari Araç Pazarı"]
        cols = ['Yıl', 'Ay', 'Toplam Pazar', 'Binek Araçları Pazarı', 'Hafif Ticari Araç Pazarı',
                'Taşıt Kredi Faizi', 'Çalışma Günü',
                'Tüketici Güven Endeksi', 'Aylık Enflasyon', 'TÜFE']
        coklu_dosya = coklu_dosya[cols]
        coklu_dosya = to_excel(coklu_dosya)
        st.sidebar.download_button(label='📥 Tahmini İndir',
                                   data=coklu_dosya,
                                   file_name='Tahmin.xlsx')
    except:
        pass

    market_data = pd.read_excel('marketdata.xlsx')
    market_data = market_data[['Tarih', 'PC_Market', 'LCV_Market']]
    market_data.dropna(inplace=True)
    market_data = market_data.set_index('Tarih')
    print(market_data)
    if pazar == 'Binek Araçları Pazarı':
        st.line_chart(market_data['PC_Market'])
    elif pazar == 'Hafif Ticari Araç Pazarı':
        st.line_chart(market_data['LCV_Market'])