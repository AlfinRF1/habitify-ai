import streamlit as st
import google.generativeai as genai
import os
import json
from datetime import datetime

# 1. AMBIL API KEY
API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    st.error("Waduh bro, API Key Gemini belum dikonfigurasi di Streamlit Secrets!")

# 2. FUNGSI UNTUK MANAJEMEN FILE RIWAYAT (JSON)
HISTORY_DIR = "chat_histories"
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

def save_chat_to_json(session_id, history_data):
    """Menyimpan history chat aktif ke file JSON"""
    filepath = os.path.join(HISTORY_DIR, f"{session_id}.json")
    with open(filepath, "w") as f:
        json.dump(history_data, f, indent=4)

def load_chat_from_json(session_id):
    """Memuat history chat dari file JSON"""
    filepath = os.path.join(HISTORY_DIR, f"{session_id}.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return []

# 3. KONFIGURASI UI & SIDEBAR STREAMLIT
st.set_page_config(page_title="HabitifyAI", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    /* 1. Mengubah background dan border box chat */
    .stChatMessage {
        background-color: #1F2937 !important;
        border-radius: 15px !important;
        padding: 15px !important;
        margin-bottom: 10px !important;
        border: 1px solid #374151 !important;
    }
    
    /* 2. Custom desain untuk tombol sidebar */
    .stButton>button {
        background: linear-gradient(135deg, #00F0FF 0%, #7000FF 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover {
        transform: scale(1.02) !important;
        box-shadow: 0px 0px 12px #00F0FF !important;
    }
    
    /* 3. Desain judul utama */
    h1 {
        background: -webkit-linear-gradient(#00F0FF, #7000FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- KONTROL SIDEBAR ---
st.sidebar.header("⚙️ Pengaturan Bot")
persona = st.sidebar.selectbox("Pilih Gaya Bicara Bot:", ["Sobat Santai", "GigaChad Coach", "Supportive Peer"])
mode = st.sidebar.radio("Pilih Mode Fokus Hari Ini:", ["Lifestyle & Habit", "Fitness & Jogging"])

st.sidebar.markdown("---")
st.sidebar.header("📜 Riwayat Percakapan")

# Fitur untuk membuat Sesi Chat Baru
if st.sidebar.button("➕ Mulai Chat Baru", use_container_width=True):
    # 1. Bikin ID sesi baru berdasarkan waktu sekarang
    new_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.current_session_id = new_id
    
    # 2. Hapus paksa semua cache memory chat lama dari Streamlit
    if "chat_session" in st.session_state:
        del st.session_state.chat_session
        
    # 3. Trik Sakti: Paksa bikin file JSON kosong baru buat ID baru ini
    # Supaya pas script ke-reload, kodingan bawah ngebaca data kosongan
    filepath = os.path.join(HISTORY_DIR, f"{new_id}.json")
    with open(filepath, "w") as f:
        json.dump([], f) # Isinya cuma list kosong []
        
    # 4. Rerun halaman
    st.rerun()

# Menampilkan daftar file riwayat yang ada di server
saved_files = sorted(os.listdir(HISTORY_DIR), reverse=True)
session_options = [f.replace(".json", "") for f in saved_files if f.endswith(".json")]

# Inisialisasi ID sesi aktif saat pertama kali buka web
if "current_session_id" not in st.session_state:
    if session_options:
        st.session_state.current_session_id = session_options[0]
    else:
        st.session_state.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

# Widget Selector untuk memilih riwayat chat lama
if session_options:
    selected_session = st.sidebar.selectbox(
        "Pilih sesi chat lama:",
        options=session_options,
        index=session_options.index(st.session_state.current_session_id) if st.session_state.current_session_id in session_options else 0
    )
    # Jika user memilih sesi yang berbeda di sidebar, muat datanya
    if selected_session != st.session_state.current_session_id:
        st.session_state.current_session_id = selected_session
        st.rerun()
else:
    st.sidebar.write("*Belum ada riwayat chat.*")

# 4. RACIK PROMPT SYSTEM & INIT GEMINI
if persona == "Sobat Santai":
    prompt_instruksi = "Anda adalah teman tongkrongan sebaya yang asik dan santai. Gunakan bahasa gaul anak muda Indonesia yang natural (lu, gua, bre, bro, wkwk). Tanggapi keluhan dengan santai dan solutif tanpa tekanan."
elif persona == "GigaChad Coach":
    prompt_instruksi = "Anda adalah pelatih olahraga dan gaya hidup yang sangat tegas, kompetitif, dan suka nge-roast jika pengguna malas, namun tujuannya memotivasi. Gunakan bahasa gaul (lu, gua, bre, bro)."
else:
    prompt_instruksi = "Anda adalah teman berbagi gaya hidup yang sangat suportif, penuh empati, ramah, dan selalu memuji pencapaian pengguna. Gunakan bahasa gaul (lu, gua, bre, bro, semangat)."

system_instruction = f"{prompt_instruksi} Saat ini Anda memandu pengguna fokus pada: {mode}."

if API_KEY:
    model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_instruction)

# 5. MEMUAT MEMORI KE LAYAR UTAMA
# Muat data chat dari file JSON berdasarkan ID sesi yang aktif
raw_history = load_chat_from_json(st.session_state.current_session_id)

# Sinkronisasi dengan API Gemini agar Gemini ingat konteks lama
api_formatted_history = []
for msg in raw_history:
    api_role = "model" if msg["role"] == "assistant" else "user"
    api_formatted_history.append({"role": api_role, "parts": [msg["content"]]})

if API_KEY:
    chat_session = model.start_chat(history=api_formatted_history)

# Tampilkan seluruh riwayat percakapan sesi ini ke layar utama
st.title("⚡ HabitifyAI: Productivity & Fitness Companion")
st.caption(f"📅 ID Sesi Aktif: {st.session_state.current_session_id}")

for msg in raw_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 6. PROSES CHAT BARU
if user_input := st.chat_input("Tulis progres lu hari ini, bro..."):
    # 1. Tampilkan input user
    with st.chat_message("user"):
        st.markdown(user_input)
    raw_history.append({"role": "user", "content": user_input})
    
    # 2. Ambil respon dari Gemini
    with st.status("HabitifyAI lagi mikir...", expanded=False) as status:
        try:
            response = chat_session.send_message(user_input)
            bot_response = response.text
            status.update(label="Selesai menganalisis!", state="complete", expanded=False)
        except Exception as e:
            bot_response = f"Gagal memproses pesan, bro. Error: {e}"
            status.update(label="Gagal memproses.", state="error", expanded=False)

    # 3. Tampilkan respon bot
    with st.chat_message("assistant"):
        st.markdown(bot_response)
    raw_history.append({"role": "assistant", "content": bot_response})
    
    # 4. SIMPAN OTOMATIS KE FILE JSON
    save_chat_to_json(st.session_state.current_session_id, raw_history)