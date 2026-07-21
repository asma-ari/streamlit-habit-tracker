"""
app.py
แอป Habit Tracker น่ารักๆ ทำด้วย Streamlit
- ตั้งกิจกรรมที่ทำวนซ้ำได้ทุก N วัน (เช่น สระผมทุก 2 วัน)
- ปฏิทินรายเดือน กดเข้าไปในแต่ละวันเพื่อบันทึกไดอารี่ / ลบบันทึกที่ผิดวันได้
- แถบ "วันนี้ต้องทำ" ใต้ปฏิทิน กดติ๊กว่าทำแล้ว แล้วจะไปโผล่ในปฏิทินวันนั้นทันที
"""

from datetime import date

import streamlit as st

import db
from schedule_utils import (
    THAI_MONTHS,
    THAI_WEEKDAYS_SHORT,
    is_due,
    month_weeks,
    next_due_date,
    thai_weekday,
    upcoming_due_dates,
)

st.set_page_config(page_title="🌸 Daily Habit Tracker", page_icon="🌸", layout="centered")

db.init_db()

# ---------- Cute custom styling ----------
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(180deg, #fff5f7 0%, #f3f0ff 100%); }
    div[data-testid="stMetric"] {
        background: white; padding: 12px; border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .habit-card {
        background: white; padding: 14px 18px; border-radius: 16px;
        margin-bottom: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .due-today { border-left: 6px solid #ff9eb5; }
    .not-due { border-left: 6px solid #d8d8f0; opacity: 0.7; }
    .cal-pad { text-align:center; color:#d8d0e6; padding:8px 0; }
    .cal-weekday { text-align:center; font-weight:bold; color:#6b4c8a; padding-bottom:4px; }
    h1, h2, h3 { color: #6b4c8a; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🌸 Daily Habit Tracker")
st.caption("ปฏิทินบันทึกประจำวัน + กิจกรรมวนซ้ำทุก N วัน ✨")

today = date.today()

# ---------- Session state ----------
if "cal_year" not in st.session_state:
    st.session_state.cal_year = today.year
if "cal_month" not in st.session_state:
    st.session_state.cal_month = today.month
if "selected_date" not in st.session_state:
    st.session_state.selected_date = today

tab_calendar, tab_habits = st.tabs(["📅 ปฏิทิน", "🔁 กิจกรรมวนซ้ำ"])

# ================= TAB: ปฏิทิน =================
with tab_calendar:
    # ---- month navigation ----
    nav1, nav2, nav3 = st.columns([1, 3, 1])
    with nav1:
        if st.button("◀", use_container_width=True, key="prev_month"):
            m, y = st.session_state.cal_month - 1, st.session_state.cal_year
            if m < 1:
                m, y = 12, y - 1
            st.session_state.cal_month, st.session_state.cal_year = m, y
            st.rerun()
    with nav2:
        st.markdown(
            f"<h3 style='text-align:center'>"
            f"{THAI_MONTHS[st.session_state.cal_month - 1]} "
            f"{st.session_state.cal_year + 543}</h3>",
            unsafe_allow_html=True,
        )
    with nav3:
        if st.button("▶", use_container_width=True, key="next_month"):
            m, y = st.session_state.cal_month + 1, st.session_state.cal_year
            if m > 12:
                m, y = 1, y + 1
            st.session_state.cal_month, st.session_state.cal_year = m, y
            st.rerun()

    # ---- weekday header ----
    header_cols = st.columns(7)
    for c, lbl in zip(header_cols, THAI_WEEKDAYS_SHORT):
        c.markdown(f"<div class='cal-weekday'>{lbl}</div>", unsafe_allow_html=True)

    # ---- summarize this month's logs so each day cell can show a tiny icon ----
    month_logs = db.get_logs_for_month(st.session_state.cal_year, st.session_state.cal_month)
    day_summary = {}
    for log in month_logs:
        s = day_summary.setdefault(log["log_date"], {"note": False, "done": False})
        if log["note"]:
            s["note"] = True
        elif log["completed"]:
            s["done"] = True

    # ---- calendar grid ----
    weeks = month_weeks(st.session_state.cal_year, st.session_state.cal_month)
    for week in weeks:
        cols = st.columns(7)
        for col, d in zip(cols, week):
            in_month = d.month == st.session_state.cal_month
            with col:
                if not in_month:
                    st.markdown(f"<div class='cal-pad'>{d.day}</div>", unsafe_allow_html=True)
                    continue
                summary = day_summary.get(d.isoformat(), {})
                icon = ("✅" if summary.get("done") else "") + ("📝" if summary.get("note") else "")
                marker = ("•" if d == today else "") + icon
                label = f"{d.day} {marker}".strip()
                btn_type = "primary" if d == st.session_state.selected_date else "secondary"
                if st.button(label, key=f"cal_{d.isoformat()}", use_container_width=True, type=btn_type):
                    st.session_state.selected_date = d
                    st.rerun()
    st.caption("• = วันนี้ · ✅ = ทำกิจกรรมแล้ว · 📝 = มีบันทึก — กดวันที่เพื่อดู/เพิ่มบันทึก")

    # ---- today's to-do bar (directly under the calendar) ----
    st.divider()
    st.subheader("✅ วันนี้ต้องทำ")
    habits = db.get_habits()
    due_habits = [h for h in habits if is_due(date.fromisoformat(h["start_date"]), h["interval_days"], today)]
    not_done = [h for h in due_habits if not db.is_done_today(h["id"], today)]

    if not due_habits:
        st.caption("วันนี้ไม่มีกิจกรรมที่ต้องทำ พักผ่อนได้เลย 🛋️")
    elif not not_done:
        st.success("ทำครบทุกอย่างของวันนี้แล้ว เก่งมาก! 🎉")
    else:
        for h in not_done:
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(
                    f"<div class='habit-card due-today'>{h['emoji']} <b>{h['name']}</b>"
                    f" — ทุก {h['interval_days']} วัน</div>",
                    unsafe_allow_html=True,
                )
            with c2:
                if st.button("ทำแล้ว ✔️", key=f"todo_{h['id']}", use_container_width=True):
                    db.add_log(h["id"], today, note=None, completed=True)
                    st.session_state.selected_date = today
                    st.rerun()

    # ---- day detail: journal for the selected date ----
    st.divider()
    sel = st.session_state.selected_date
    st.subheader(f"📖 บันทึกวันที่ {thai_weekday(sel)} {sel.strftime('%d/%m/%Y')}")

    day_logs = db.get_logs_for_date(sel)
    if not day_logs:
        st.caption("ยังไม่มีบันทึกในวันนี้")
    else:
        for log in day_logs:
            c1, c2 = st.columns([6, 1])
            with c1:
                if log["note"]:
                    st.markdown(f"🗒️ {log['note']}")
                elif log["completed"]:
                    st.markdown(f"✅ {log['habit_emoji'] or ''} {log['habit_name'] or 'กิจกรรม'}")
            with c2:
                if st.button("🗑️", key=f"del_{log['id']}", help="ลบบันทึกนี้ (เผื่อบันทึกผิดวัน)"):
                    db.delete_log(log["id"])
                    st.rerun()

    with st.form(f"note_form_{sel.isoformat()}", clear_on_submit=True):
        note_text = st.text_area("เขียนบันทึกเพิ่มเติมสำหรับวันนี้")
        submitted = st.form_submit_button("บันทึก 💌")
        if submitted:
            if note_text.strip():
                db.add_log(habit_id=None, log_date=sel, note=note_text.strip(), completed=False)
                st.success("บันทึกแล้ว!")
                st.rerun()
            else:
                st.warning("ยังไม่ได้เขียนอะไรเลยนะ")

# ================= TAB: กิจกรรมวนซ้ำ =================
with tab_habits:
    st.subheader("➕ เพิ่มกิจกรรมวนซ้ำใหม่")
    with st.form("add_habit_form", clear_on_submit=True):
        c1, c2 = st.columns([1, 3])
        emoji = c1.text_input("อีโมจิ", value="✨", max_chars=2)
        name = c2.text_input("ชื่อกิจกรรม เช่น สระผม, ซักผ้า, รดน้ำต้นไม้")
        c3, c4 = st.columns(2)
        interval_days = c3.number_input("ทำทุกกี่วัน", min_value=1, max_value=365, value=2)
        start_date_input = c4.date_input("เริ่มนับจากวันที่", value=today)
        submitted = st.form_submit_button("บันทึกกิจกรรม 💾")
        if submitted:
            if name.strip():
                db.add_habit(name.strip(), emoji or "✨", int(interval_days), start_date_input)
                st.success(f"เพิ่ม '{name}' เรียบร้อย!")
                st.rerun()
            else:
                st.warning("ใส่ชื่อกิจกรรมด้วยนะ")

    st.divider()
    st.subheader("📋 กิจกรรมทั้งหมด")
    habits = db.get_habits()
    if not habits:
        st.info("ยังไม่มีกิจกรรมวนซ้ำ ลองเพิ่มดูด้านบนได้เลย")
    for h in habits:
        start_d = date.fromisoformat(h["start_date"])
        upcoming = upcoming_due_dates(start_d, h["interval_days"], today, count=4)
        upcoming_str = ", ".join(f"{thai_weekday(d)[:2]} {d.strftime('%d/%m')}" for d in upcoming)
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(
                f"**{h['emoji']} {h['name']}** — ทุก {h['interval_days']} วัน  \n"
                f"📆 กำหนดถัดไป: {upcoming_str}"
            )
        with col2:
            if st.button("ลบ 🗑️", key=f"del_habit_{h['id']}"):
                db.delete_habit(h["id"])
                st.rerun()
