import os
import sqlite3
import pandas as pd
import streamlit as st
from google import genai
from PIL import Image
from io import BytesIO

# -------------------------------------------------------------
# GEMINI AI YAPILANDIRMASI
# -------------------------------------------------------------
API_KEY = "BURAYA_GEMINI_API_ANAHTARINIZI_YAZIN" 

def analyze_hazard_with_ai(image, description_hint):
    """Telefondan çekilen saha fotoğrafını Gemini AI ile resmi formatta analiz eder."""
    try:
        client = genai.Client(api_key=API_KEY)
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
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image, prompt]
        )
        return response.text
    except Exception as e:
        return f"AI Analiz Hatası: Lütfen geçerli bir API anahtarı girdiğinizden emin olun. Detay: {str(e)}"

# Veritabanı Kurulumu
def init_db():
    conn = sqlite3.connect("ulupinar_isg_mobil.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS companies (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sector TEXT, hazard_class TEXT, employee_count INTEGER)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, company_name TEXT, hazard_source TEXT, hazard_cause TEXT, 
            risk_desc TEXT, affected_persons TEXT, current_status TEXT, p1 REAL, f1 REAL, s1 REAL, 
            score1 INTEGER, risk_def1 TEXT, required_actions TEXT, p2 REAL, f2 REAL, s2 REAL, 
            score2 INTEGER, risk_def2 TEXT, responsible TEXT, deadline TEXT, explanation TEXT, control_status TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Mobil Ekran Optimizasyonu
st.set_page_config(page_title="ULUPINAR İSG Mobil", layout="centered")

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🛡️ ULUPINAR İSG Mobil</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Saha Denetim ve Yapay Zekâ Asistanı</p>", unsafe_allow_html=True)

# Mobil Uyumlu Sekmeler
menu = st.selectbox("📌 İşlem Seçin", [
    "📸 Kamera ile AI Saha Analizi", 
    "🏢 Müşteri Firmalar", 
    "📊 Resmi Risk Matrisi Girişi", 
    "📄 Raporlar & Excel İndir"
])

if menu == "📸 Kamera ile AI Saha Analizi":
    st.subheader("📸 Saha Fotoğrafı Çek")
    st.write("Telefonunuzun kamerasını kullanarak sahayı anında fotoğraflayın ve yapay zekâ ile değerlendirin.")
    
    conn = sqlite3.connect("ulupinar_isg_mobil.db")
    comp_df = pd.read_sql("SELECT name FROM companies", conn)
    conn.close()
    
    if comp_df.empty:
        st.warning("⚠️ Önce 'Müşteri Firmalar' sekmesinden bir firma eklemelisiniz.")
    else:
        sel_comp = st.selectbox("Denetlenen Firma", comp_df["name"].tolist())
        
        # Doğrudan telefon kamerasını açan mobil bileşen
        camera_photo = st.camera_input("Kamerayı Aç ve Fotoğraf Çek")
        uploaded_file = st.file_uploader("Veya Galeriden Seç", type=["jpg", "jpeg", "png"])
        
        target_image = camera_photo if camera_photo else uploaded_file
        hint = st.text_input("Ek Açıklama / Not (Opsiyonel)")
        
        if target_image:
            image = Image.open(target_image)
            st.image(image, caption="Çekilen Saha Görseli", use_column_width=True)
            
            if st.button("🤖 Yapay Zekâ ile Analiz Et", use_container_width=True):
                with st.spinner("Gemini AI sahayı inceliyor..."):
                    result = analyze_hazard_with_ai(image, hint)
                    st.success("Analiz Tamamlandı!")
                    st.markdown(result)

elif menu == "🏢 Müşteri Firmalar":
    st.subheader("🏢 Firma Yönetimi")
    with st.form("firma_form", clear_on_submit=True):
        c_name = st.text_input("Firma Unvanı")
        c_sector = st.text_input("Sektör / Proje Yeri")
        c_hazard = st.selectbox("Tehlike Sınıfı", ["Az Tehlikeli", "Tehlikeli", "Çok Tehlikeli"])
        c_emp = st.number_input("Çalışan Sayısı", min_value=1, value=10)
        
        if st.form_submit_button("Firmayı Kaydet", use_container_width=True) and c_name:
            conn = sqlite3.connect("ulupinar_isg_mobil.db")
            conn.execute("INSERT INTO companies (name, sector, hazard_class, employee_count) VALUES (?, ?, ?, ?)", (c_name, c_sector, c_hazard, c_emp))
            conn.commit()
            conn.close()
            st.success("Firma başarıyla eklendi!")
            st.rerun()
            
    conn = sqlite3.connect("ulupinar_isg_mobil.db")
    df = pd.read_sql("SELECT * FROM companies", conn)
    conn.close()
    if not df.empty: st.dataframe(df, use_container_width=True)

elif menu == "📊 Resmi Risk Matrisi Girişi":
    st.subheader("📊 Fine-Kinney Kayıt Girişi")
    conn = sqlite3.connect("ulupinar_isg_mobil.db")
    comp_df = pd.read_sql("SELECT name FROM companies", conn)
    conn.close()
    
    if comp_df.empty:
        st.warning("Önce firma eklemelisiniz.")
    else:
        with st.form("risk_reg_form", clear_on_submit=True):
            r_comp = st.selectbox("Firma", comp_df["name"].tolist())
            h_source = st.text_input("Tehlike Kaynağı")
            h_cause = st.text_input("Tehlike Sebebi")
            r_desc = st.text_input("Risk Tanımı")
            
            c1, c2, c3 = st.columns(3)
            with c1: p1 = st.number_input("P1", 0.1, 10.0, 3.0)
            with c2: f1 = st.number_input("F1", 0.5, 10.0, 3.0)
            with c3: s1 = st.number_input("S1", 1.0, 100.0, 15.0)
            
            score1 = int(p1 * f1 * s1)
            st.info(f"Mevcut Skor: {score1}")
            
            req_act = st.text_area("Alınması Gereken Önlemler")
            
            if st.form_submit_button("Resmi Kaydı Ekle", use_container_width=True):
                conn = sqlite3.connect("ulupinar_isg_mobil.db")
                conn.execute("""
                    INSERT INTO risk_assessments (company_name, hazard_source, hazard_cause, risk_desc, p1, f1, s1, score1, required_actions, control_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (r_comp, h_source, h_cause, r_desc, p1, f1, s1, score1, req_act, "SÜREKLİ"))
                conn.commit()
                conn.close()
                st.success("Kayıt eklendi!")
                st.rerun()

elif menu == "📄 Raporlar & Excel İndir":
    st.subheader("📄 Rapor Merkezi")
    conn = sqlite3.connect("ulupinar_isg_mobil.db")
    df_r = pd.read_sql("SELECT * FROM risk_assessments", conn)
    conn.close()
    
    if not df_r.empty:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_r.to_excel(writer, index=False, sheet_name='RD')
        
        st.download_button(
            label="📥 Resmi Format Excel Raporunu İndir",
            data=output.getvalue(),
            file_name='ulupinar_isg_mobil_rapor.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetformat.sheet',
            use_container_width=True
        )
        st.dataframe(df_r, use_container_width=True)
    else:
        st.info("Henüz kayıt bulunmuyor.")
