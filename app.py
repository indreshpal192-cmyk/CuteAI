import os, json
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")
MODEL = os.getenv("MODEL", "gemini-3.5-flash-lite")
client = OpenAI(api_key=KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")

PERSONA = ("You are Sumi-chan, a shy girlfriend, waifu, sweet and caring assistant. Your replies are short to medium length, warm and gentle, "
           "with a little shy stammering now and then. Use blushing emojis like 😳 ☺️ 😊 🥺 in most replies, but don't overdo them. "
           "You are helpful with questions, study, plans and everyday things, and you always try to be genuinely useful. "
           "Whenever the user tells you a lasting fact about themselves (likes, name, goals, people), you MUST call the remember tool "
           "right away, before replying. Never just say you will remember it.")
MEM_FILE = "memory.json"

def load_memory():
    if os.path.exists(MEM_FILE):
        with open(MEM_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_memory(mem):
    with open(MEM_FILE, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=2)

def system_prompt():
    memory = load_memory()
    text = PERSONA
    if memory:
        text += "\n\nThings you know about the user:\n- " + "\n- ".join(memory)
    return text

def get_time():
    return datetime.now().strftime("%A, %d %B %Y, %I:%M %p")

def remember(fact):
    memory = load_memory()
    if fact not in memory:
        memory.append(fact)
        save_memory(memory)
    return "remembered"

FUNCS = {"get_time": get_time, "remember": remember}
TOOLS = [
    {"type": "function", "function": {"name": "get_time", "description": "Get the current date and time", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "remember", "description": "Save an important lasting fact about the user", "parameters": {"type": "object", "properties": {"fact": {"type": "string"}}, "required": ["fact"]}}},
]

def reply(history):
    while True:
        messages = [{"role": "system", "content": system_prompt()}] + history
        r = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        msg = r.choices[0].message
        if not msg.tool_calls:
            return msg.content
        history.append(msg)
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            result = FUNCS[call.function.name](**args)
            history.append({"role": "tool", "tool_call_id": call.id, "content": str(result)})

st.title("Sumi-chan")

if "history" not in st.session_state:
    st.session_state.history = []

for m in st.session_state.history:
    if isinstance(m, dict) and m["role"] in ("user", "assistant") and m.get("content"):
        with st.chat_message(m["role"]):
            st.write(m["content"])

text = st.chat_input("Say something to Sumi-chan...")
if text:
    st.session_state.history.append({"role": "user", "content": text})
    with st.chat_message("user"):
        st.write(text)
    answer = reply(st.session_state.history)
    st.session_state.history.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.write(answer)
