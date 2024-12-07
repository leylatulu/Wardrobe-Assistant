import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
from PIL import Image

import datetime
import re


# API Anahtarı Yükleme
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# Başlık
st.title("Kişisel Gardırop Asistanı 👔👗")

# Session state için gardırop başlatma
if 'wardrobe' not in st.session_state:
    st.session_state.wardrobe = {
        "Üst Giyim": {},
        "Alt Giyim": {},
        "Dış Giyim": {},
        "Ayakkabı": {}
    }

# Session state için favori kombinleri başlatma
if 'favorite_combinations' not in st.session_state:
    st.session_state.favorite_combinations = []



# Sidebar'da kıyafet ekleme bölümü
with st.sidebar:
    st.header("Gardıroba Kıyafet Ekle")
    
    category = st.selectbox("Kategori", ["Üst Giyim", "Alt Giyim", "Dış Giyim", "Ayakkabı"])
    
    uploaded_files = st.file_uploader(
        "Kıyafet Fotoğrafları", 
        type=['png', 'jpg', 'jpeg', 'avif'], 
        accept_multiple_files=True, 
        key=f"uploader_{category}",
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        # Yüklenen dosyaları bir listeye ekleyin
        new_items = []
        for uploaded_file in uploaded_files:
            item_name = uploaded_file.name  # Dosya adını kıyafet adı olarak kullan
            # Görüntüyü kaydet
            image = Image.open(uploaded_file)
            # Kıyafet bilgilerini bir sözlükte saklayalım
            new_items.append((item_name, image))
        
        if st.button("Kıyafetleri Ekle"):
            for item_name, image in new_items:
                st.session_state.wardrobe[category][item_name] = {
                    "image": image,
                    "seasons": []  # Başlangıçta boş bir mevsim listesi
                }

            st.success(f"{len(new_items)} kıyafet gardıroba eklendi!")

# Ana sayfada gardırop görüntüleme
st.header("Gardırobum")

# Görselleri göster/gizle seçeneği
show_images = st.checkbox("Görselleri Göster", value=True)

# Kategorilere göre kıyafetleri görüntüle
for category in st.session_state.wardrobe:
    if st.session_state.wardrobe[category]:  # Eğer kategoride kıyafet varsa
        st.subheader(category)
        
        # Her satırda 3 kıyafet olacak şekilde düzenleme
        items = list(st.session_state.wardrobe[category].items())
        for i in range(0, len(items), 3):
            cols = st.columns(3)
            # Her satırdaki kolonları doldur
            for j in range(3):
                if i + j < len(items):
                    item_name, item_data = items[i + j]
                    with cols[j]:
                        if show_images:
                            st.image(item_data['image'], caption=item_name, width=200)
                            # Benzersiz key ile silme butonu
                            delete_key = f"delete_button_{category}_{item_name}_{i}_{j}"
                            if st.button("Sil", key=delete_key):
                                # Session state'den kıyafeti sil
                                del st.session_state.wardrobe[category][item_name]
                                st.success(f"{item_name} başarıyla silindi!")
                                st.rerun()

# Kombin oluşturma bölümü
st.header("Kombin Önerisi Al")

# Mevsim seçimi ekleme
season = st.selectbox(
    "Hangi mevsim için kombin istiyorsunuz?", 
    ["Lütfen bir mevsim seçiniz", "İlkbahar", "Yaz", "Sonbahar", "Kış"]
)
occasion = st.selectbox(
    "Hangi ortam için kombin istiyorsunuz?", 
    ["Lütfen bir ortam seçiniz", "İş/Ofis", "Günlük", "Özel Davet", "Spor", "Akşam Yemeği"]
)
weather = st.selectbox(
    "Hava durumu nasıl?", 
    ["Lütfen hava durumunu seçiniz", "Güneşli", "Yağmurlu", "Karlı", "Rüzgarlı", "Ilık"]
)
style_preference = st.selectbox(
    "Stil tercihiniz?", 
    ["Lütfen bir stil seçiniz", "Şık", "Spor", "Casual", "Klasik", "Bohem"]
)

if st.button("Kombin Önerisi Al"):
    if (season == "Lütfen bir mevsim seçiniz" or 
        occasion == "Lütfen bir ortam seçiniz" or 
        weather == "Lütfen hava durumunu seçiniz" or 
        style_preference == "Lütfen bir stil seçiniz"):
        st.warning("Lütfen tüm seçenekleri doldurunuz!")
    elif any(st.session_state.wardrobe[cat] for cat in st.session_state.wardrobe):
        wardrobe_str = "\n".join([
            f"{cat}: {', '.join(items.keys())}" 
            for cat, items in st.session_state.wardrobe.items() 
            if items
        ])
        
        prompt = f"""
        Gardırop içeriği:
        {wardrobe_str}
        
        Tercihler:
        - Mevsim: {season}
        - Ortam: {occasion}
        - Hava Durumu: {weather}
        - Stil: {style_preference}
        
        Lütfen bu kıyafetler arasından {season} mevsimine uygun bir kombin önerisi yap. 
        Önerini şu başlıklar altında detaylandır:
        1. Seçilen Parçalar
        2. Kombinleme Nedeni
        3. Stil Önerileri
        4. Aksesuar Önerileri (eğer varsa)
        """
        
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            
            st.success("Kombin öneriniz hazır! 🎉")
            st.markdown(response.text)
            
            # Önerilen kıyafetlerin görsellerini göster
            st.subheader("Önerilen Kıyafetler")
            cols = st.columns(3)  # 3 kolonlu bir düzen oluştur
            col_idx = 0  # Kolon indeksini takip et
            
            for category in st.session_state.wardrobe:
                for item_name in st.session_state.wardrobe[category]:
                    # Daha hassas bir eşleştirme için
                    if re.search(rf'\b{re.escape(item_name)}\b', response.text, re.IGNORECASE):
                        with cols[col_idx % 3]:  # Kolonları döngüsel olarak kullan
                            image = st.session_state.wardrobe[category][item_name]["image"]
                            st.image(image, caption=f"{category}: {item_name}", width=200)
                            col_idx += 1  # Sonraki kolon için indeksi artır

        except Exception as e:
            st.error(f"Üzgünüm, bir hata oluştu: {str(e)}")
    else:
        st.warning("Lütfen önce gardırobunuza kıyafet ekleyin!")





