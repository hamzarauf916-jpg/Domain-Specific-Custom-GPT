import os
import uuid
import base64
from pathlib import Path

from langchain_openai import ChatOpenAI, OpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import streamlit as st

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=True)

st.set_page_config(page_title="Streamlit Chatbot", page_icon=":robot_face:")

# ------------------------------------------------------------------
# Login page graphics (replaced: split-card design with illustration
# panel on the left and "Apna AI" branded form on the right)
# ------------------------------------------------------------------
LOGIN_PANEL_PATH = Path(__file__).parent / "assets" / "login_panel.jpg"
LOGO_BADGE_PATH = Path(__file__).parent / "assets" / "apna_ai_badge.png"

# small bot avatar icon used on the chat page header / sidebar
BOT_ICON_PATH = Path(__file__).parent / "assets" / "bot_avatar_icon.png"

# ------------------------------------------------------------------
# Chat page graphics (new: ambient app background, sidebar texture,
# WhatsApp-style doodle wallpaper behind the conversation, and a
# hero illustration for the empty/new-chat state)
# ------------------------------------------------------------------
APP_BG_PATH = Path(__file__).parent / "assets" / "backgrounds" / "app-bg.jpg"
SIDEBAR_TEXTURE_PATH = Path(__file__).parent / "assets" / "backgrounds" / "sidebar-texture.jpg"
CHAT_DOODLE_PATH = Path(__file__).parent / "assets" / "backgrounds" / "chat-doodle.jpg"
EMPTY_HERO_PATH = Path(__file__).parent / "assets" / "illustrations" / "empty-hero.jpg"


def get_image_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ------------------------------------------------------------------
# Session state setup (added: page routing, api key, chat history)
# ------------------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "login"
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "conversations" not in st.session_state:
    st.session_state.conversations = {}     # conv_id -> {"title": ..., "messages": [...]}
if "conv_order" not in st.session_state:
    st.session_state.conv_order = []
if "current_conv" not in st.session_state:
    st.session_state.current_conv = None
if "domain" not in st.session_state:
    st.session_state.domain = ""


def new_conversation():
    conv_id = str(uuid.uuid4())
    st.session_state.conversations[conv_id] = {"title": "New chat", "messages": []}
    st.session_state.conv_order.append(conv_id)
    st.session_state.current_conv = conv_id
    return conv_id


def ensure_conversation():
    if not st.session_state.current_conv or st.session_state.current_conv not in st.session_state.conversations:
        new_conversation()


def generate_chat_title(api_key, user_message, ai_message):
    """Ask the model for a short title that summarizes what this
    conversation is about (like ChatGPT/Claude do), falling back to a
    trimmed version of the user's first message if that call fails."""
    fallback = (user_message[:28] + "…") if len(user_message) > 28 else user_message
    try:
        titler = ChatOpenAI(temperature=0.2, model_name="gpt-3.5-turbo", api_key=api_key)
        title_prompt = [
            SystemMessage(
                content=(
                    "You write short chat titles, like conversation titles in "
                    "ChatGPT. Reply with ONLY the title — 3 to 6 words, no "
                    "quotes, no punctuation at the end, no prefixes like 'Title:'."
                )
            ),
            HumanMessage(
                content=f"User message: {user_message}\nAssistant reply: {ai_message}\n\nTitle:"
            ),
        ]
        result = titler.invoke(title_prompt)
        title = result.content.strip().strip('"').strip("'").strip()
        if not title:
            return fallback
        if len(title) > 45:
            title = title[:42].rstrip() + "…"
        return title
    except Exception:
        return fallback


# ------------------------------------------------------------------
# PAGE 1 — LOGIN: split-card design — illustration panel on the left,
# "Apna AI" branded API-key form on the right (matches reference design)
# ------------------------------------------------------------------
def render_login():
    panel_b64 = get_image_base64(LOGIN_PANEL_PATH)
    badge_b64 = get_image_base64(LOGO_BADGE_PATH)

    # NOTE: Streamlit's real widgets (text_input/button) always render as
    # their own top-level blocks inside `.block-container` — they can't be
    # nested inside a custom <div> written via st.markdown. So instead of
    # trying to wrap them in a hand-written "card" div, we style
    # `.block-container` itself to BE the white card, and place the
    # illustration as an absolutely-positioned layer behind its left edge.
    st.markdown(
        f"""
        <style>
        #MainMenu, footer, header {{visibility: hidden;}}

        .stApp {{
            background:
                radial-gradient(circle at 0% 0%, #c9cdd3 0%, rgba(201,205,211,0) 42%),
                radial-gradient(circle at 100% 0%, #8fdce4 0%, rgba(143,220,228,0) 48%),
                linear-gradient(180deg, #eef1f4 0%, #ffffff 55%);
        }}

        .block-container {{
            position: relative;
            max-width: 1300px;
            min-height: 670px;
            margin: 2.5rem auto;
            border-radius: 24px;
            overflow: hidden;
            box-shadow: 0 25px 70px rgba(20, 25, 40, 0.28);
            background: #ffffff;
            padding: 3.2rem 3.6rem 2.6rem calc(58% + 3.6rem);
            display: flex;
            flex-direction: column;
        }}

        .login-illustration {{
            position: fixed;
            top: 2.5rem;
            left: calc(50vw - 650px);
            width: 754px;
            height: 670px;
            border-radius: 24px 0 0 24px;
            background-image: url("data:image/jpg;base64,{panel_b64}");
            background-size: cover;
            background-position: center;
            z-index: 0;
        }}

        @media (max-width: 1000px) {{
            .login-illustration {{ display: none; }}
            .block-container {{ padding-left: 2.2rem !important; max-width: 520px !important; }}
        }}

        .block-container > div {{
            position: relative;
            z-index: 1;
        }}

        .logo-row {{
            display: flex;
            align-items: center;
            gap: 0.8rem;
            margin-bottom: 2.2rem;
        }}
        .logo-badge {{
            width: 52px;
            height: 52px;
            border-radius: 14px;
        }}
        .logo-text {{
            font-size: 1.7rem;
            font-weight: 800;
            color: #14161f;
            letter-spacing: -0.3px;
        }}

        .welcome-heading {{
            font-size: 1.7rem;
            font-weight: 800;
            color: #10121a;
            margin: 0 0 0.35rem 0;
        }}
        .welcome-sub {{
            font-size: 0.95rem;
            color: #6b7280;
            margin: 0 0 2.2rem 0;
        }}
        .field-label {{
            font-size: 0.88rem;
            font-weight: 600;
            color: #232733;
            margin-bottom: 0.4rem;
        }}

        .stTextInput > div > div > input {{
            background: #ffffff !important;
            color: #14121f !important;
            -webkit-text-fill-color: #14121f !important;
            border: 1px solid #d9dce1 !important;
            border-radius: 10px !important;
            padding: 0.8rem 0.9rem !important;
        }}
        .stTextInput > div > div > input::placeholder {{
            color: #a7abb4 !important;
        }}

        .stButton {{
            width: 100% !important;
        }}
        div[data-testid="stElementContainer"]:has(div[data-testid="stButton"]) {{
            width: 100% !important;
        }}
        .stButton > button {{
            width: 100%;
            background: #2f7d34;
            color: #ffffff;
            font-weight: 700;
            font-size: 1rem;
            border: none;
            border-radius: 10px;
            padding: 0.75rem 0;
            margin-top: 0.6rem;
            transition: background 0.15s ease-in-out;
        }}
        .stButton > button:hover {{
            background: #266b2a;
            color: #ffffff;
        }}

        .login-footer {{
            margin-top: auto;
            padding-top: 2.5rem;
            text-align: center;
            font-size: 0.9rem;
            color: #6b7280;
        }}
        .login-footer a {{
            color: #2f6fed;
            text-decoration: none;
            font-weight: 600;
        }}
        .login-footer a:hover {{
            text-decoration: underline;
        }}
        </style>

        <div class="login-illustration"></div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="logo-row">
            <img class="logo-badge" src="data:image/png;base64,{badge_b64}" />
            <span class="logo-text">Apna AI</span>
        </div>
        <h2 class="welcome-heading">Welcome back.</h2>
        <p class="welcome-sub">Please enter your API Key to continue.</p>
        <div class="field-label">Enter API Key</div>
        """,
        unsafe_allow_html=True,
    )

    key_input = st.text_input(
        "Enter API Key",
        type="password",
        placeholder="your_api_key_here_...",
        label_visibility="collapsed",
    )

    if st.button("Initialize"):
        if key_input.strip():
            st.session_state.api_key = key_input.strip()
            os.environ["OPENAI_API_KEY"] = key_input.strip()
            st.session_state.page = "chat"
            st.rerun()
        else:
            st.error("Please enter a valid API key.")

    st.markdown(
        """
        <div class="login-footer">
            Don't have an API Key?
            <a href="https://platform.openai.com/api-keys" target="_blank">Learn more.</a>
        </div>
        """,
        unsafe_allow_html=True,
    )



# ------------------------------------------------------------------
# DOMAIN GATE (new): user picks/types the single domain this chatbot
# is allowed to talk about. Shown once before the chat UI unlocks.
# ------------------------------------------------------------------
DOMAIN_PRESETS = ["Cooking", "Fitness & Health", "Finance", "Travel", "Coding & Tech", "Other (type your own)"]


def render_domain_select():
    st.subheader("🎯 Choose your assistant's domain")
    st.caption("Pick a topic (or write your own). The assistant will only answer questions related to it.")

    choice = st.selectbox("Domain", DOMAIN_PRESETS)
    custom = ""
    if choice == "Other (type your own)":
        custom = st.text_input("Enter your domain", placeholder="e.g. Wedding Planning")

    if st.button("Confirm Domain"):
        final_domain = custom.strip() if choice == "Other (type your own)" else choice
        if final_domain:
            st.session_state.domain = final_domain
            st.rerun()
        else:
            st.error("Please enter a domain.")


# ------------------------------------------------------------------
# PAGE 2 — CHAT (your original code, kept as-is, just relocated /
# wrapped so the message bar sits at the bottom and the sidebar now
# also shows chat history + a logout button)
# ------------------------------------------------------------------
def render_chat():
    if not st.session_state.domain:
        render_domain_select()
        return

    ensure_conversation()

    # ---- background graphics: ambient app bg, sidebar texture, and a
    # WhatsApp-style doodle wallpaper behind the message list ----
    app_bg_b64 = get_image_base64(APP_BG_PATH)
    sidebar_tex_b64 = get_image_base64(SIDEBAR_TEXTURE_PATH)
    doodle_b64 = get_image_base64(CHAT_DOODLE_PATH)

    st.markdown(
        f"""
        <style>
        html, body,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > .main,
        [data-testid="stMain"] {{
            min-height: 100vh;
            height: 100%;
        }}

        .stApp {{
            background-image:
                linear-gradient(180deg, rgba(9,10,14,0.55), rgba(9,10,14,0.55)),
                url("data:image/jpg;base64,{app_bg_b64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            background-repeat: no-repeat;
            min-height: 100vh;
        }}

        section[data-testid="stSidebar"] {{
            background-image:
                linear-gradient(180deg, rgba(21,23,30,0.75), rgba(21,23,30,0.75)),
                url("data:image/jpg;base64,{sidebar_tex_b64}");
            background-size: cover;
            background-position: top center;
            background-attachment: fixed;
            background-repeat: no-repeat;
            min-height: 100vh;
        }}

        [data-testid="stMain"] {{
            background-image:
                linear-gradient(180deg, rgba(10,12,16,0.85), rgba(10,12,16,0.85)),
                url("data:image/jpg;base64,{doodle_b64}");
            background-repeat: repeat;
            background-size: 280px auto;
            min-height: 100vh;
        }}

        .main .block-container {{
            min-height: 100vh;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }}

        /* Streamlit's own header bar and the fixed bottom chat-input bar
           paint solid backgrounds by default, which is what was blocking
           the doodle pattern from reaching the very top/bottom edges —
           make both transparent so the background shows through fully. */
        [data-testid="stHeader"] {{
            background: transparent !important;
        }}
        [data-testid="stBottom"],
        [data-testid="stBottom"] > div,
        [data-testid="stBottomBlockContainer"] {{
            background: transparent !important;
        }}

        /* Pin the Logout button (last widget in the sidebar) to the very
           bottom of the sidebar, and give it a maroon color. */
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
            min-height: calc(80vh - 2rem);
            display: flex;
            flex-direction: column;
        }}
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div:last-child {{
            margin-top: auto;
        }}
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div:last-child button {{
            background: #7a1f2b;
            border: 1px solid #58151e;
            color: #ffe4e6;
        }}
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div:last-child button:hover {{
            background: #5c1620;
            border-color: #7a1f2b;
            color: #ffffff;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    icon_b64 = get_image_base64(BOT_ICON_PATH)
    icon_col, title_col = st.columns([0.07, 0.93])
    with icon_col:
        st.markdown(
            f'<img src="data:image/png;base64,{icon_b64}" style="width:44px; height:44px; '
            f'border-radius:50%; margin-top:6px;" />',
            unsafe_allow_html=True,
        )
    with title_col:
        st.subheader("A custom Chatgpt")
    chat = ChatOpenAI(temperature=0.9, model_name="gpt-3.5-turbo", api_key=st.session_state.api_key)

    # st.session_state.messages now points at the CURRENT conversation's
    # message list, so everything below behaves exactly like your original code
    st.session_state.messages = st.session_state.conversations[st.session_state.current_conv]["messages"]

    with st.sidebar:
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.3rem;">
                <img src="data:image/png;base64,{icon_b64}" style="width:32px; height:32px; border-radius:50%;" />
                <span style="font-size:1.1rem; font-weight:600;">Chat History</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("➕ New Chat"):
            new_conversation()
            st.rerun()

        for conv_id in reversed(st.session_state.conv_order):
            conv = st.session_state.conversations[conv_id]
            label = ("👉 " if conv_id == st.session_state.current_conv else "🗨️ ") + conv["title"]
            if st.button(label, key=f"hist_{conv_id}"):
                st.session_state.current_conv = conv_id
                st.rerun()

        st.markdown("---")
        st.caption(f"📌 Domain: **{st.session_state.domain}**")
        if st.button("🔄 Change Domain"):
            st.session_state.domain = ""
            st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state.page = "login"
            st.session_state.api_key = ""
            st.session_state.conversations = {}
            st.session_state.conv_order = []
            st.session_state.current_conv = None
            st.session_state.domain = ""
            st.rerun()

    domain_system_prompt = (
        f"You are a helpful assistant that ONLY answers questions related to "
        f"'{st.session_state.domain}'. If the user asks anything outside this "
        f"domain, politely decline and remind them you can only help with "
        f"'{st.session_state.domain}', then invite them to ask a relevant question. "
        f"Do not answer unrelated questions even if you know the answer."
    )

    if len(st.session_state.messages) >= 1:
        if not isinstance(st.session_state.messages[0], SystemMessage):
            st.session_state.messages.insert(0, SystemMessage(content=domain_system_prompt))
        else:
            st.session_state.messages[0] = SystemMessage(content=domain_system_prompt)

    for msg in st.session_state.messages[1:]:
        if isinstance(msg, HumanMessage):
            with st.chat_message('user'):
                st.write(msg.content)
        elif isinstance(msg, AIMessage):
            with st.chat_message('assistant'):
                st.write(msg.content)

    # ---- empty-state hero: shown only when this conversation has no
    # messages yet (just the hidden domain SystemMessage at index 0) ----
    if len(st.session_state.messages) <= 1:
        hero_b64 = get_image_base64(EMPTY_HERO_PATH)
        st.markdown(
            f"""
            <div style="display:flex; flex-direction:column; align-items:center;
                        justify-content:center; padding: 3rem 0 2rem 0; opacity:0.95;">
                <img src="data:image/jpg;base64,{hero_b64}" style="max-width:360px;
                     width:100%; border-radius:16px; box-shadow: 0 15px 40px rgba(0,0,0,0.45);" />
                <p style="color:#8b93a3; margin-top:1.2rem; font-size:0.95rem;">
                    Ask me anything about <b style="color:#5eead4;">{st.session_state.domain}</b> to get started
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---- message bar moved to the bottom of the conversation ----
    user_prompt = st.chat_input("Your message")
    if user_prompt:
        st.session_state.messages.append(HumanMessage(content=user_prompt))
        with st.chat_message('user'):
            st.write(user_prompt)

        with st.chat_message('assistant'):
            with st.spinner("Generating response..."):
                response = chat.invoke(st.session_state.messages)
                st.write(response.content)

        st.session_state.messages.append(AIMessage(content=response.content))

        conv = st.session_state.conversations[st.session_state.current_conv]
        if conv["title"] == "New chat":
            with st.spinner("Naming chat..."):
                conv["title"] = generate_chat_title(st.session_state.api_key, user_prompt, response.content)
            st.rerun()


# ------------------------------------------------------------------
# ROUTER
# ------------------------------------------------------------------
if st.session_state.page == "login":
    render_login()
else:
    render_chat()