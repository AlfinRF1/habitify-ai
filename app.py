import streamlit as st
import google.generativeai as genai
import os

# os.environ.get akan membaca key "GEMINI_API_KEY" yang kita set di dashboard Streamlit Cloud nanti
API_KEY = os.environ.get("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    st.error("Waduh bro, API Key Gemini belum dikonfigurasi di Streamlit Secrets!")

# 2. KONFIGURASI UI STREAMLIT
st.set_page_config(page_title="HabitifyAI", page_icon="⚡", layout="wide")
st.title("⚡ HabitifyAI: Productivity & Fitness Companion")
st.write("Teman AI interaktif buat pantau progres produktivitas dan olahraga mu!")


# 3. SIDEBAR PARAMETER
st.sidebar.header("⚙️ Pengaturan Bot")
persona = st.sidebar.selectbox("Pilih Gaya Bicara Bot:", ["GigaChad Coach", "Supportive Peer"])
mode = st.sidebar.radio("Pilih Mode Fokus Hari Ini:", ["Productivity & Lifestyle", "Fitness & Jogging"])

# Set instruksi karakter berdasarkan pilihan
if persona == "GigaChad Coach":
    prompt_instruksi = (
        "Anda adalah pelatih olahraga dan produktivitas yang sangat tegas, kompetitif, "
        "dan agak suka menyindir (nge-roast) jika pengguna malas, namun tujuannya memotivasi. "
        "Gunakan bahasa santai, gaul Indonesia (seperti lu, gua, bre, bro, mantap, parah)."
    )
else:
    prompt_instruksi = (
        "Anda adalah teman belajar dan olahraga yang sangat suportif, penuh empati, ramah, "
        "dan selalu memberikan pujian positif atas pencapaian sekecil apa pun. "
        "Gunakan bahasa santai, gaul Indonesia (seperti lu, gua, bre, bro, semangat, keren)."
    )

system_instruction = f"{prompt_instruksi} Saat ini Anda sedang dalam mode mendampingi pengguna untuk fokus pada: {mode}."

# Inisialisasi model jika API Key aman
if API_KEY:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_instruction
    )

# 4. MEMORI CHAT (SESSION STATE)
if "chat_session" not in st.session_state and API_KEY:
    st.session_state.chat_session = model.start_chat(history=[])

# Tampilkan history chat jika sudah ada
if "chat_session" in st.session_state:
    for message in st.session_state.chat_session.history:
        role = "assistant" if message.role == "model" else "user"
        with st.chat_message(role):
            st.markdown(message.parts[0].text)

# 5. INPUT & RESPONS CHAT
if user_input := st.chat_input("Tulis progres lu hari ini, bre..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    
    with st.status("HabitifyAI lagi mikir...", expanded=False) as status:
        try:
            response = st.session_state.chat_session.send_message(user_input)
            bot_response = response.text
            status.update(label="Selesai menganalisis!", state="complete", expanded=False)
        except Exception as e:
            bot_response = f"Gagal memproses pesan, bre. Pastikan API Key bener. Error: {e}"
            status.update(label="Gagal memproses.", state="error", expanded=False)

    with st.chat_message("assistant"):
        st.markdown(bot_response)