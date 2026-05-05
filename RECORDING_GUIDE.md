# Recording Guide: Section 7, Streamlit for the AI Era

Internal recording script for Section 7 of the Streamlit course. Not shared with students. Keep it next to you during recording.

**Total target duration:** ~55-65 minutes across 8 lectures.
**Codebase:** `streamlit-llm-csv-chat/` in your Udemy workspace.
**Data:** `sample_data/sample.csv` (NYC TLC yellow taxi August 2025, 300 rows). Loaded via the **Load NYC taxi sample** button. Larger demo files (parquet, full CSV, 100k sample, e-commerce CSV) live in `data/` (gitignored, distributed via Udemy supplemental materials).

## Lecture structure at a glance

```
L27  The new Streamlit playbook                          3-4 min
L28  Business case + architecture                        2-3 min
L29  Layout that doesn't look like a demo               10-12 min
L30  Wire in the LLM with streaming                     12-14 min
L31  Suggested questions and auto-visualizations         8-10 min
L32  Lock the app with a password gate                   6-8 min
L33  Deploying for free on Streamlit Community Cloud     8-10 min
L34  Where to go next                                    3-5 min
```

L32 sits between viz and deploy on purpose: students learn to lock the app down BEFORE pushing it to the public internet, so the deployed URL is gated from the very first request.

---

## Before you start recording

Do this ONCE before Lecture 29, not on camera:

1. Open a clean folder (not the final project) where you will "build" the app from scratch during recording. Call it something like `streamlit-llm-demo`.
2. Inside, create an empty `venv` and install dependencies one at a time as the lectures introduce them:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install streamlit openai pandas plotly
   ```
3. Have the final codebase (the project folder) open in a second editor window as your reference.
4. Have the sample CSV at `sample_data/sample.csv` ready in your demo folder so the sample button works on camera.
5. Test that your OpenAI key works with a quick `curl` or Python snippet.
6. Clear your terminal history and set a clean prompt.
7. Set a hard spend cap of $5 on your OpenAI account at [platform.openai.com/account/limits](https://platform.openai.com/account/limits). Safety net for any student who forgets the same step.

**Visual checklist for all lectures:**
- Hide your desktop icons
- Mute Slack, email, browser notifications
- Close any tab not needed for the demo
- Use one large terminal + one browser window layout

---

## Lecture 27: The new Streamlit playbook (LLM apps changed the game)

**Target duration:** 3-4 minutes
**On screen:** You on camera + optional slide overlay
**Code:** None
**Goal:** Set the stage. Students walk away understanding why this section exists.

### Talking points

- Streamlit started as a way to turn data scripts into web apps. That is still its core job.
- What changed: `st.chat_message` and `st.chat_input` shipped, then `st.write_stream` was added, then chat patterns became standard. Overnight Streamlit went from "data dashboards" to "the fastest way to prototype an LLM chat app in Python."
- Every data team is now building internal LLM tools: chatbots over company docs, CSV Q&A, model demo interfaces, prompt playgrounds. Streamlit gets you from idea to shippable app in an afternoon.
- In this section we will build one of those apps: **Chat with Your CSV.** Upload any CSV, ask questions in plain English, get streaming grounded answers from OpenAI. Plus an instant metrics dashboard, an auto-generated visualizations tab, a model selector, a token / cost counter, and a password gate so you can share it only with your team.
- Deploy for free on Streamlit Community Cloud so you can share it with whoever you want.
- You will leave this section with a real production pattern you can reuse for any LLM-powered data app.

### Pacing note

Keep this lecture punchy. It is orientation, not teaching. Students want to get to the code.

---

## Lecture 28: Business case + architecture sketch

**Target duration:** 2-3 minutes
**On screen:** A slide or whiteboard with the architecture sketch
**Code:** None
**Goal:** Define the problem clearly enough that the next four lectures feel purposeful.

### Talking points

**The problem.** Non-technical colleagues constantly ask analysts "what is in this spreadsheet?" or "what does this dataset mean?" The analyst spends 20 minutes opening it, grouping, aggregating, writing a Slack reply. Imagine if the analyst could send a URL: "upload your CSV here and ask it anything."

**What we are building.** A Streamlit web app where:
1. User uploads a CSV (or loads our bundled sample with one click).
2. App profiles the data: shape, dtypes, summary stats, sample rows, missing values.
3. Top-of-page metric cards show key dataset facts at a glance.
4. Three tabs: Chat, Data overview, Visualize.
5. User asks questions in the chat; answers stream in token-by-token like ChatGPT.
6. Sidebar lets the user pick the model and shows a running token / cost counter.
7. Optional shared-password gate keeps the deployed app private to people who know the password.

**The data.** We use NYC TLC yellow taxi trips for the demo, but the app is data-agnostic. Every feature works the same on sales data, web analytics, customer feedback, anything tabular.

**Architecture sketch.** (Draw or show slide)

```
[User] → [Streamlit UI: tabs + chat + viz]
           │
           ├── pd.read_csv → DataFrame
           │        │
           │        ├── auto-metrics (rows / cols / numeric / missing)
           │        ├── data overview tab
           │        ├── visualize tab (Plotly auto-charts)
           │        └── build_data_context → text summary
           │                                    │
           └── chat input ──── ask_llm_stream(msg, context, history, model) → OpenAI
                                                                              │
                          ◄────── streaming chunks ◄─────────────────────────┘
                          ◄────── token usage     ◄─────────────────────────┘
```

**Why this architecture.** One-liner each:
- No code execution, so no security headaches on Community Cloud
- No vector database, so the app stays simple
- Statistical summary is rich enough to answer most real questions
- Works for any CSV shape, not just this one
- Streaming gives the perceived speed of commercial AI apps

### Transition

"Next up, we build the layout that makes this look like a real product, not a Hello World demo."

---

## Lecture 29: Layout that doesn't look like a demo (tabs, metrics, sample button)

**Target duration:** 10-12 minutes
**On screen:** Terminal + code editor + browser showing the app
**Code:** Build `app.py` up to the layout layer, before the LLM
**Goal:** Students have a polished UI structure with tabs, metric cards, and a one-click sample loader. No LLM yet.

### Live coding sequence

Start with an empty `app.py`. Type (not paste) these pieces on camera:

**Step 1: Page config + title.** Show the app running with just this. Refresh the browser, point at the title.

```python
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Chat with Your CSV", page_icon="📊", layout="wide")

st.title("Chat with Your CSV")
st.caption("Upload a CSV, get an instant dashboard, then chat with your data.")
```

**Step 2: Sidebar with file uploader and sample button.** Walk students through `st.file_uploader`. Show that the return value is None until a file is dropped. Then add the sample button.

```python
with st.sidebar:
    st.header("1. Load your data")
    uploaded_file = st.file_uploader("Drop a CSV file here", type="csv")

    st.caption("…or try the sample dataset:")
    if st.button("Load NYC taxi sample", use_container_width=True):
        st.session_state.use_sample = True

# Decide which DataFrame we are working with
if "use_sample" not in st.session_state:
    st.session_state.use_sample = False

df = None
file_label = None
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    file_label = uploaded_file.name
    st.session_state.use_sample = False
elif st.session_state.use_sample:
    df = pd.read_csv("sample_data/sample.csv")
    file_label = "sample.csv (NYC taxi)"

if df is None:
    st.info("Use the sidebar to upload a CSV or load the sample.")
    st.stop()
```

Click the sample button on camera. Show that the page reloads with the sample data.

**Step 3: Top metric cards.** Explain `st.columns` and `st.metric`. Emphasize: these are *generic*, they work for any CSV.

```python
total_cells = df.shape[0] * df.shape[1]
missing_cells = int(df.isna().sum().sum())
missing_pct = missing_cells / total_cells * 100 if total_cells else 0
numeric_cols = df.select_dtypes(include="number").columns.tolist()

st.caption(f"Data source: `{file_label}`")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Rows", f"{len(df):,}")
m2.metric("Columns", f"{len(df.columns)}")
m3.metric("Numeric columns", f"{len(numeric_cols)}")
m4.metric("Missing values", f"{missing_pct:.1f}%")
```

Refresh. Point at the four cards lined up at the top. Say: "this is what makes the app look like a product, not a script."

**Step 4: Three tabs.** Introduce `st.tabs`.

```python
tab_chat, tab_overview, tab_viz = st.tabs(
    ["💬 Chat", "📋 Data overview", "📊 Visualize"]
)

with tab_chat:
    st.write("Chat goes here")  # placeholder for now

with tab_overview:
    st.subheader("Sample rows")
    st.dataframe(df.head(20), use_container_width=True)

    st.subheader("Column profile")
    profile = pd.DataFrame({
        "Column": df.columns,
        "Type": [str(t) for t in df.dtypes],
        "Non-null": [int(df[c].notna().sum()) for c in df.columns],
        "Null": [int(df[c].isna().sum()) for c in df.columns],
        "Unique": [int(df[c].nunique()) for c in df.columns],
    })
    st.dataframe(profile, use_container_width=True, hide_index=True)

    if numeric_cols:
        st.subheader("Numeric column statistics")
        st.dataframe(df[numeric_cols].describe().round(2), use_container_width=True)

with tab_viz:
    st.write("Visualizations go here")  # placeholder for now
```

Click through the tabs. Say: "this is the moment your app stops looking like a demo and starts looking like a product."

### Callouts during this lecture

- `st.tabs` is the most under-used Streamlit primitive. Three lines of code, massive UX win.
- `st.metric` accepts a `delta` parameter for trend indicators, useful in dashboards.
- `st.session_state.use_sample` is your first session state usage. Foreshadow: you'll use it more in the chat.

### Gotcha to flag

If `pd.read_csv("sample_data/sample.csv")` fails because the file isn't there, show the error. Then add the file. Pedagogical: file paths matter.

---

## Lecture 30: Wire in the LLM with streaming, model selector, and token counter

**Target duration:** 12-14 minutes
**On screen:** Terminal + editor + browser + briefly platform.openai.com
**Code:** Create `llm_utils.py`, wire it into `app.py`, add streaming + model selector + token counter
**Goal:** Students have a working LLM-powered chat with streaming responses, the ability to pick models, and a real-time cost counter.

### Live coding sequence

**Step 1: Get an OpenAI key.** (Quick browser tour)
- Navigate to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- Show the "Create new secret key" button
- Emphasize the spend cap at [platform.openai.com/account/limits](https://platform.openai.com/account/limits). Tell students to set a $5 cap now.
- Remind them: never commit your key to Git.

**Step 2: Set up Streamlit secrets.**
- Create `.streamlit/secrets.toml`:
  ```toml
  OPENAI_API_KEY = "sk-proj-..."
  ```
- Immediately create `.gitignore` and add `.streamlit/secrets.toml` to it.
- Explain: `.streamlit/secrets.toml` works locally. When we deploy to Community Cloud, we paste the same key into the cloud UI instead.

**Step 3: Build `llm_utils.py` — the data profiler first.**

```python
import pandas as pd
import streamlit as st
from openai import OpenAI

MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.150, "output": 0.600},
    "gpt-4o":      {"input": 2.500, "output": 10.000},
}
AVAILABLE_MODELS = list(MODEL_PRICING.keys())

def build_data_context(df):
    parts = []
    parts.append(f"Dataset shape: {df.shape[0]:,} rows x {df.shape[1]} columns")

    parts.append("\nColumns and types:")
    for col, dtype in df.dtypes.items():
        parts.append(f"  - {col}: {dtype}")

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        parts.append("\nNumeric column statistics:")
        parts.append(df[numeric_cols].describe().round(2).to_string())

    parts.append("\nFirst 5 rows:")
    parts.append(df.head(5).to_string(index=False))

    return "\n".join(parts)
```

Run it in a Python REPL live, show the output. Say: "this is what the LLM will see. It's just text. The model is good at reading text."

**Step 4: Build the OpenAI client helper.**

```python
def get_openai_client():
    api_key = st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        st.error("OpenAI API key not found. Add it to .streamlit/secrets.toml.")
        st.stop()
    return OpenAI(api_key=api_key)
```

**Step 5: Build the streaming `ask_llm_stream`.** This is THE teaching moment of the lecture.

```python
SYSTEM_PROMPT = """You are a data analyst assistant. Answer questions \
using ONLY the data summary below. Be precise and data-driven. If the \
summary doesn't contain enough info, say so.

=== DATA SUMMARY ===
{data_context}
===================="""

def ask_llm_stream(user_message, data_context, history, model, usage_tracker=None):
    client = get_openai_client()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(data_context=data_context)}
    ]
    for msg in history[-6:]:
        messages.append(msg)
    messages.append({"role": "user", "content": user_message})

    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        max_tokens=700,
        stream=True,
        stream_options={"include_usage": True},
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
        if getattr(chunk, "usage", None) and usage_tracker is not None:
            usage_tracker["input_tokens"] = chunk.usage.prompt_tokens
            usage_tracker["output_tokens"] = chunk.usage.completion_tokens
```

Talk through:
- `stream=True` turns the API call into an iterator
- `stream_options={"include_usage": True}` makes the final chunk include token counts
- The function is a generator: it `yield`s strings as they arrive
- `usage_tracker` is a dict the caller passes in; we mutate it as a side effect

**Step 6: Wire it into `app.py`.** Replace the placeholder Chat tab content.

```python
from llm_utils import (
    AVAILABLE_MODELS, MODEL_PRICING,
    ask_llm_stream, build_data_context,
)

# Initialize session state
st.session_state.setdefault("messages", [])
st.session_state.setdefault("tokens_by_model", {})

# Sidebar: model selector + token counter
with st.sidebar:
    st.divider()
    st.header("2. Choose your model")
    selected_model = st.selectbox("OpenAI model", AVAILABLE_MODELS, index=0)

    st.divider()
    st.header("3. Usage")
    used = sum(b["input"] + b["output"] for b in st.session_state.tokens_by_model.values())
    cost = sum(
        (b["input"] * MODEL_PRICING[m]["input"] + b["output"] * MODEL_PRICING[m]["output"]) / 1_000_000
        for m, b in st.session_state.tokens_by_model.items()
        if m in MODEL_PRICING
    )
    st.metric("Tokens", f"{used:,}")
    st.metric("Cost", f"${cost:.4f}")

# Build the LLM context once
data_context = build_data_context(df)

# Chat tab
with tab_chat:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask anything about your data..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            usage = {}
            reply = st.write_stream(ask_llm_stream(
                user_message=prompt,
                data_context=data_context,
                history=st.session_state.messages[:-1],
                model=selected_model,
                usage_tracker=usage,
            ))
            if usage.get("input_tokens"):
                bucket = st.session_state.tokens_by_model.setdefault(
                    selected_model, {"input": 0, "output": 0}
                )
                bucket["input"] += usage["input_tokens"]
                bucket["output"] += usage["output_tokens"]

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()
```

**Demo time.** Click sample data button. Ask:
- "What does this dataset contain?"
- "What's the typical fare amount?"
- "How many rows have missing values?"

Watch the answer stream in token-by-token. Point at the sidebar token counter as it updates.

Switch to `gpt-4o`. Ask the same question. Show the cost jump in real time.

### Callouts during this lecture

- The streaming generator pattern is reusable: any time you want to stream OpenAI through Streamlit, this is the shape
- `st.write_stream` returns the concatenated final string after the stream finishes
- Usage tracking is a side-effect on a dict because you can't easily yield non-string values through `st.write_stream`
- `temperature=0.2` keeps the model grounded; raise it for more creative answers
- `max_tokens=700` caps cost per response; raise for longer answers

### Gotcha to flag

If `stream_options={"include_usage": True}` is missing, the final chunk has no usage and your counter stays at zero. Show the error / no-update by removing the flag, then add it back.

---

## Lecture 31: Suggested questions and auto-visualizations

**Target duration:** 8-10 minutes
**On screen:** Editor + browser
**Code:** Add suggestion chips to the Chat tab, fill in the Visualize tab
**Goal:** The app graduates from "works" to "feels polished."

### Live coding sequence

**Step 1: Suggestion chips.** Explain the design: chips appear ONLY when chat is empty. Click a chip → use it as the prompt.

```python
# Inside the Chat tab, before the chat history loop:
pending = st.session_state.pop("pending_prompt", None)

if not st.session_state.messages and not pending:
    st.markdown("**Not sure where to start? Try a question:**")
    starters = [
        "Describe this dataset in plain English.",
        "Are there any columns with missing values I should worry about?",
        "What patterns or anomalies stand out in the numeric columns?",
        "Which columns look most useful for analysis, and why?",
    ]
    chip_cols = st.columns(2)
    for i, q in enumerate(starters):
        if chip_cols[i % 2].button(q, key=f"starter_{i}", use_container_width=True):
            st.session_state.pending_prompt = q
            st.rerun()

# ...history loop...

typed = st.chat_input("Ask anything about your data...")
prompt = typed or pending
# ...rest of the chat flow uses `prompt`...
```

Talk through:
- Why the questions are GENERIC, not taxi-specific. The app needs to feel just as useful for sales data, web analytics, anything.
- Why we use session state + `st.rerun()`: a button click can't directly trigger the same code path as `chat_input`, so we relay through state.

Click a chip. Watch it stream a real answer. Show it disappears after the first message.

**Step 2: Visualize tab.** Introduce Plotly Express and `st.plotly_chart`.

```python
import plotly.express as px

with tab_viz:
    st.caption("Auto-generated visualizations from any CSV.")

    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if numeric_cols:
        st.subheader("Numeric column distributions")
        selected_numeric = st.multiselect(
            "Numeric columns to plot",
            options=numeric_cols,
            default=numeric_cols[:4],
        )
        chart_cols = st.columns(2)
        for i, col_name in enumerate(selected_numeric):
            with chart_cols[i % 2]:
                fig = px.histogram(df, x=col_name, nbins=30, title=col_name)
                fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig, use_container_width=True)

    if cat_cols:
        st.subheader("Categorical column counts")
        selected_cat = st.multiselect(
            "Categorical columns to plot",
            options=cat_cols,
            default=cat_cols[:2],
        )
        for col_name in selected_cat:
            counts = df[col_name].value_counts(dropna=False).head(10).reset_index()
            counts.columns = [col_name, "count"]
            fig = px.bar(counts, x=col_name, y="count", title=f"Top values: {col_name}")
            fig.update_layout(height=350, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
```

Click into the Visualize tab. Show the histograms render. Point out that Plotly charts are interactive: hover, zoom, pan.

Open the multiselect, deselect a column, watch the chart disappear. Show the multiselect IS the "data-agnostic" feature. Any CSV, any columns.

### Callouts during this lecture

- Why Plotly over `st.bar_chart`: interactive, more polished, standard in the modern data-app stack
- Why histograms for numeric and bar charts for categorical: that is the universal first-pass EDA pattern
- The multiselect lets students explore. Real product feel.

### Gotcha to flag

If you have a column with a million unique values (an ID column), the bar chart explodes. We mitigate by `head(10)` on `value_counts`. Show what happens without the head, then add it back.

---

## Lecture 32: Lock the app with a password gate

**Target duration:** 6-8 minutes
**On screen:** Editor + browser
**Code:** Add `check_password()` to `app.py`, set `APP_PASSWORD` in secrets, add Sign out button to sidebar
**Goal:** Students can ship a deployed app that's protected by a shared password, ready to share with their team without exposing it to the public internet.

### Talking points

**The gap.** Right now the app is wide open. Anyone who finds the URL hits your OpenAI key. For a personal demo that's fine. For sharing with your team, your boss, or your portfolio, you want a basic gate.

**The fix.** Shared password gate. About 30 lines of code. Anyone who knows the password gets in. Anyone who doesn't sees a sign-in screen. This is the right tool when you want "share with my team but not the public."

**What this is NOT.** This is shared-password auth, not per-user accounts. There's no "different password for different people." For real per-user auth you'd reach for `streamlit-authenticator` (community library, hashed passwords in YAML) or Streamlit's native OAuth (`st.login` / `st.user`, supports Google / Microsoft / GitHub login). Mention these as next horizons.

### Live coding sequence

**Step 1: Add the password to local secrets.**

Open `.streamlit/secrets.toml` and add:

```toml
APP_PASSWORD = "demo-password-2026"
```

Emphasize: this is a weak password for a demo. In production, use something long and random. Show students how to generate one with `python -c "import secrets; print(secrets.token_urlsafe(20))"`.

**Step 2: Build the `check_password` function.**

In `app.py`, near the top (right after the session-state init):

```python
def check_password() -> bool:
    """Render the password gate. Return True if the user is authenticated."""
    try:
        expected = st.secrets.get("APP_PASSWORD")
    except Exception:
        expected = None
    if not expected:
        return True   # No password configured: app is open

    if st.session_state.get("authenticated"):
        return True   # Already authenticated this session

    st.title("Sign in")
    st.caption("Enter the password to access this app.")
    pw = st.text_input("Password", type="password", label_visibility="collapsed")
    if pw:
        if pw == expected:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False


if not check_password():
    st.stop()
```

Walk students through what each piece does:

- The `try/except` around `st.secrets.get(...)`: handles the case where `secrets.toml` doesn't exist at all
- `if not expected: return True`: the app is open if no password is configured (fail-open default, friendly for local dev)
- `st.session_state.authenticated` flag: persists the "logged in" state across reruns within the browser tab session
- `st.text_input(type="password")`: hides the typed value
- `st.stop()` after `check_password()`: halts the script if not authenticated, so the rest of the app doesn't render

**Step 3: Demo it.**

Refresh the app. Sign-in screen appears. Type a wrong password, see the error. Type the right password, watch the app reload into its normal state.

**Step 4: Add a Sign out button to the sidebar.**

```python
# In the sidebar, after the Clear chat history button:
try:
    auth_enabled = bool(st.secrets.get("APP_PASSWORD"))
except Exception:
    auth_enabled = False
if auth_enabled:
    if st.button("Sign out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
```

Click Sign out on camera. Watch the app return to the gate.

**Step 5: Talk about how this works in production.**

After deploy, students will set `APP_PASSWORD` in Community Cloud's secrets UI alongside their OpenAI key. Anyone with the password gets in. To revoke access for someone who left the team, change the password and re-share with the others.

### Callouts during this lecture

- The fail-open default is deliberate. Students who forget to set a password don't get locked out of their own app.
- Refreshing the browser tab clears `session_state`, so users have to sign in again on refresh. That's a feature for security, a friction for UX. Mention `streamlit-authenticator` as the upgrade path if they want cookie-based persistence.
- Never put `APP_PASSWORD` in code. Always in `st.secrets`. Repeat this. Credential leaks are the #1 way deployed apps get abused.

### Gotcha to flag

If a student forgets to add `APP_PASSWORD` to Community Cloud secrets after deploy but their local code expects it, the cloud deploy will be unprotected. Show this on camera as a teaching moment: deploy without setting the cloud secret, refresh, see no gate, then add the secret and refresh again.

### Transition

"Now we have a real, gated app. Time to put it on the internet."

---

## Lecture 33: Deploying for free on Streamlit Community Cloud

**Target duration:** 8-10 minutes
**On screen:** Terminal + editor + browser (github.com + share.streamlit.io)
**Code:** Add `requirements.txt`, push to GitHub, configure cloud secrets
**Goal:** Students have a public URL sharing their app.

### Live sequence

**Step 1: Explain the shift from GitLab to GitHub.**
- Earlier in the course we used GitLab for CI/CD
- Streamlit Community Cloud only deploys from GitHub
- For a production app you still use GitLab; for free public demos, mirror or use GitHub directly
- Quick note: you can have the same repo in both places if you want to keep everything in one spot

**Step 2: Write `requirements.txt`.**

```
streamlit>=1.40
openai>=1.50
pandas>=2.0
plotly>=5.20
```

Explain: Community Cloud installs these into your app's container automatically.

**Step 3: Create a GitHub repo.**
- [github.com/new](https://github.com/new)
- Name it `streamlit-llm-csv-chat`, public
- Skip the README (we already have one) and the .gitignore (we already have one)

**Step 4: Push your code.**

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR-USERNAME/streamlit-llm-csv-chat.git
git push -u origin main
```

**Critical moment:** Check your repo in the browser. Confirm `.streamlit/secrets.toml` is NOT there. If it is, stop the recording and redo (or fix on camera as a teaching moment about how dangerous leaked keys are).

Confirm `sample_data/sample.csv` IS there. Students need it for the sample button to work in production.

**Step 5: Deploy.**
- Go to [share.streamlit.io](https://share.streamlit.io)
- Sign in with GitHub, authorize
- Click **New app**
- Pick your repo, `main` branch, `app.py` as the entry file
- Click **Deploy**
- Watch the logs scroll. Usually 60-90 seconds to build (may be longer the first time because of plotly).

**Step 6: Add secrets to the deployed app.**
- From the deployed app, three-dot menu → **Settings** → **Secrets**
- Paste BOTH the OpenAI key and the app password:
  ```toml
  OPENAI_API_KEY = "sk-proj-..."
  APP_PASSWORD = "your-strong-shared-password"
  ```
- Save. The app restarts automatically.

> If you forget to add `APP_PASSWORD` here, the deployed app will be unprotected even though your local copy is locked down. Always check both secrets are set before sharing the URL.

**Step 7: Demo.**
- Visit your public URL
- Click "Load NYC taxi sample"
- Click a starter question chip
- Watch the streaming response, the metric cards, the visualizations
- The app now works from anywhere in the world

Share the URL in Q&A as a teaser: "here is my demo, go try it." (Take it down after recording if you don't want long-term spend exposure.)

### Callouts during this lecture

- Community Cloud's free tier is plenty for most demos (memory-limited, goes to sleep on inactivity, wakes on request)
- Remind about the spend cap again
- Mention that the URL is public by default. If you want auth, you need the Streamlit paid tier or self-host

### Gotcha to flag

If you commit your `secrets.toml` by mistake, **rotate the key immediately** at platform.openai.com. Don't just delete the commit, the key is already leaked on GitHub's servers.

---

## Lecture 34: Where to go next: RAG, agents, and production patterns

**Target duration:** 3-5 minutes
**On screen:** You on camera + slide overlay with a "map" of the LLM-app landscape
**Code:** None
**Goal:** Send students off with clear next learning directions. Don't teach, just orient.

### Talking points

**What we built and what we didn't.**
- We built a grounded streaming chat app over tabular data, with a dashboard, auto-viz, and live cost tracking, deployed publicly for free.
- We did NOT build: RAG (retrieval augmented generation), code execution, agent workflows, function calling.
- Those are the next three horizons if you want to go deeper.

**Horizon 1: RAG for long text.**
- If your data is documents, not rows, you need embeddings + vector search
- Tools to explore: LangChain, LlamaIndex, Chroma, Weaviate, Pinecone
- Use case: "chat with my company's internal wiki"

**Horizon 2: Code execution for exact answers.**
- Instead of summary-grounded answers, have the LLM write pandas code, run it in a sandbox, return the real result
- Tools: OpenAI's code interpreter via the Assistants API, or sandboxed Python (E2B, Riza)
- Use case: "show me the 10 trips with the highest fares"

**Horizon 3: Agents and tool use.**
- Give the LLM a toolbox: query the DB, call an API, send an email, hit a webhook
- It decides which tool to use and when
- Tools: OpenAI function calling, LangChain agents, the Anthropic Agent SDK, CrewAI, AutoGen
- Use case: multi-step workflows like "find the lowest-tipping zones, then generate a report and email it"

**One practical piece of advice.**
Don't try to build an agent as your first LLM app. The app you just built is already more useful than 80% of the "AI tools" people launch. Ship it. Then iterate. Real usage tells you whether you need RAG, code execution, or agents next.

**Course wrap.**
- Thank students for making it through
- Remind them to leave a review (the congrats message will do this too, but a verbal nudge at the end of the last content lecture helps)
- Tease what else they could apply these skills to

### Transition to Career Life Hacks

"This wraps up the technical content. One more short section on how to put these skills to work in your career, and then you're done."

---

## Post-recording checklist

- [ ] Re-record Lecture 2 in Section 1 ("What will You Learn?") to include LLM content, model selector, token tracking, viz, and Community Cloud
- [ ] Add a course announcement on Udemy: "New Section 7: Streamlit + LLMs + Free Cloud Deploy added"
- [ ] Update the "Course Updates" line in the description with April 2026 entry (this is the change that will actually trigger the "Last updated" badge to refresh on the listing)
- [ ] Verify all new lecture captions are accurate (Udemy auto-generates, but check)
- [ ] Add practice quiz questions for Section 7 (optional but good for ratings)
- [ ] Tell your VA about the new section so review responses can reference it

## Reference materials you should have open while recording

1. This guide
2. The final codebase in this folder (`app.py`, `llm_utils.py`) as your "cheat sheet"
3. A fresh empty project folder where you'll build along
4. `sample_data/sample.csv` ready in your demo folder
5. Your OpenAI API keys page in a browser tab (but hide it when not demoing)
6. [share.streamlit.io](https://share.streamlit.io) logged in

Good luck. The better you make this section, the more you protect your instructor rating and the more this quiet-earner course keeps quietly earning.
