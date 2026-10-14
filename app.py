import google.generativeai as genai
from PIL import Image
from io import BytesIO
import streamlit as str
import pandas as pd
import sqlite3
import os

# API Yapılandırması ve AI Fonksiyonunu şu şekilde güncelleyin:
API_KEY = "BURAYA_GEMINI_API_ANAHTARINIZI_YAZIN"
genai.configure(api_key=API_KEY)

def analyze_hazard_with_ai(image, description_hint):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Sen profesyonel bir A Sınıfı İş Sağlığı ve Güvenliği (İSG) Uzmanısın. 
        Bu saha fotoğrafını ve ek bilgiyi ({description_hint}) inceleyerek şu bilgileri net başlıklar halinde ver:
        1. Tehlike Kaynağı:
        2. Tehlike Sebebi:
        3. Risk Tanımı:
        4. Risk Altındakiler:
        5. Alınması Gereken Önlemler:
        6. Önerilen Fine-Kinney Olasılık (P1), Frekans (F1) ve Şiddet (S1) değerleri (Sayısal).
        """
        response = model.generate_content([image, prompt])
        return response.text
    except Exception as e:
        return f"AI Analiz Hatası: {str(e)}"
