import streamlit as st
import google.generativeai as genai
import os
import json
import shutil
from datetime import datetime

API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    st.error("Waduh bro, API Key Gemini belum dikonfigurasi di Streamlit Secrets!")

HISTORY_DIR = "chat_histories"
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)

def save_chat_to_json(session_id, history_data):
    """Menyimpan history chat aktif dengan format nama: session_id_JudulCantik.json"""
    display_title = "Chat Baru"
    
    if history_data:
        user_messages = [msg for msg in history_data if msg["role"] == "user"]
        if user_messages:
            first_chat = user_messages[0]["content"]
            display_title = (first_chat[:25] + "...") if len(first_chat) > 25 else first_chat
            for char in ['/', '\\', '?', '%', '*', ':', '|', '"', '<', '>', '.', '_']:
                display_title = display_title.replace(char, '')
            display_title = display_title.strip()

    for f in os.listdir(HISTORY_DIR):
        if f.startswith(session_id) and f.endswith(".json"):
            try:
                os.remove(os.path.join(HISTORY_DIR, f))
            except:
                pass
            
    filename = f"{session_id}_{display_title}.json"
    filepath = os.path.join(HISTORY_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(history_data, f, indent=4, ensure_ascii=False)

def load_chat_from_json(session_id):
    """Memuat history chat dengan mencari file yang diawali session_id"""
    for f in os.listdir(HISTORY_DIR):
        if f.startswith(session_id) and f.endswith(".json"):
            filepath = os.path.join(HISTORY_DIR, f)
            with open(filepath, "r", encoding="utf-8") as file:
                return json.load(file)
    return []

st.set_page_config(page_title="HabitifyAI", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    .stChatMessage {
        background-color: #1F2937 !important;
        border-radius: 15px !important;
        padding: 15px !important;
        margin-bottom: 10px !important;
        border: 1px solid #374151 !important;
    }
    
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
    
    h1 {
        background: -webkit-linear-gradient(#00F0FF, #7000FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.sidebar.header("⚙️ Pengaturan Bot")
persona = st.sidebar.selectbox("Pilih Gaya Bicara Bot:", ["Sobat Santai", "GigaChad Coach", "Supportive Peer"])
mode = st.sidebar.radio("Pilih Mode Fokus Hari Ini:", ["Lifestyle & Habit", "Fitness & Jogging"])

st.sidebar.markdown("---")
st.sidebar.header("📜 Riwayat Percakapan")

if st.sidebar.button("➕ Mulai Chat Baru", use_container_width=True):
    new_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.current_session_id = new_id
    if "chat_session" in st.session_state:
        del st.session_state.chat_session
    save_chat_to_json(new_id, [])
    st.rerun()

saved_files = sorted([f for f in os.listdir(HISTORY_DIR) if f.endswith(".json")], reverse=True)
session_ids = [f[:15] for f in saved_files]

if "current_session_id" not in st.session_state:
    if session_ids:
        st.session_state.current_session_id = session_ids[0]
    else:
        st.session_state.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_chat_to_json(st.session_state.current_session_id, [])
        st.rerun()

if session_ids:
    display_mapping = {}
    for filename in saved_files:
        current_id = filename[:15]
        title_part = filename[16:].replace(".json", "") if len(filename) > 16 else "Chat Baru"
        display_mapping[current_id] = f"💬 {title_part}"

    if st.session_state.current_session_id not in session_ids:
        st.session_state.current_session_id = session_ids[0]

    selected_session_id = st.sidebar.selectbox(
        "Pilih sesi chat lama:",
        options=session_ids,
        format_func=lambda x: display_mapping.get(x, "💬 Chat Baru"),
        index=session_ids.index(st.session_state.current_session_id)
    )
    
    if selected_session_id != st.session_state.current_session_id:
        st.session_state.current_session_id = selected_session_id
        if "chat_session" in st.session_state:
            del st.session_state.chat_session
        st.rerun()
        
    st.sidebar.markdown(" ")
    if st.sidebar.button("🗑️ Bersihkan Semua Riwayat", use_container_width=True):
        shutil.rmtree(HISTORY_DIR)
        os.makedirs(HISTORY_DIR)
        if "chat_session" in st.session_state:
            del st.session_state.chat_session
        if "current_session_id" in st.session_state:
            del st.session_state.current_session_id
        st.rerun()
else:
    st.sidebar.write("*Belum ada riwayat chat.*")

if persona == "Sobat Santai":
    prompt_instruksi = "Anda adalah teman tongkrongan sebaya yang asik dan santai. Gunakan bahasa gaul anak muda Indonesia yang natural (lu, gua, bre, bro, wkwk). Tanggapi keluhan dengan santai dan solutif tanpa tekanan."
elif persona == "GigaChad Coach":
    prompt_instruksi = "Anda adalah pelatih olahraga dan gaya hidup yang sangat tegas, kompetitif, dan suka nge-roast jika pengguna malas, namun tujuannya memotivasi. Gunakan bahasa gaul (lu, gua, bre, bro)."
else:
    prompt_instruksi = "Anda adalah teman berbagi gaya hidup yang sangat suportif, penuh empati, ramah, dan selalu memuji pencapaian pengguna. Gunakan bahasa gaul (lu, gua, bre, bro, semangat)."

system_instruction = f"{prompt_instruksi} Saat ini Anda memandu pengguna fokus pada perkembangan: {mode}."

if API_KEY:
    model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_instruction)

raw_history = load_chat_from_json(st.session_state.current_session_id)

api_formatted_history = []
for msg in raw_history:
    api_role = "model" if msg["role"] == "assistant" else "user"
    api_formatted_history.append({"role": api_role, "parts": [msg["content"]]})

if API_KEY and "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=api_formatted_history)

st.title("⚡ HabitifyAI: Lifestyle & Fitness Companion")
st.caption(f"📅 ID Sesi Aktif: {st.session_state.current_session_id}")

for msg in raw_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Tulis progres lu hari ini, bro..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    raw_history.append({"role": "user", "content": user_input})
    
    # Bagian 7: Proses Streaming Respons AI (Paling Update!)
    with st.chat_message("assistant"):
        try:
            # Menggunakan send_message_stream milik Gemini API
            response_stream = st.session_state.chat_session.send_message_stream(user_input)
            
            # Generator sederhana untuk mem-passing potongan teks (chunks) dari Gemini ke Streamlit
            def stream_chunks():
                for chunk in response_stream:
                    yield chunk.text
            
            # Menampilkan teks secara mengalir (streaming) otomatis di layar
            bot_response = st.write_stream(stream_chunks)
            
        except Exception as e:
            bot_response = f"Gagal memproses pesan, bro. Error: {e}"
            st.markdown(bot_response)

    raw_history.append({"role": "assistant", "content": bot_response})
    save_chat_to_json(st.session_state.current_session_id, raw_history)
    
    if len(raw_history) <= 2:
        st.rerun()