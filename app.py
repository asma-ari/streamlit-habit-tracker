"""
app.py
แอป Waan-Waan Habit Tracker
- ใช้ FullCalendar สวยงาม
- แก้ไขการคลิกวันที่ให้ทำงาน 100% ด้วย callback 'select' และ 'dateClick'
- คลิกวันที่แล้วเด้ง Popup Dialog กลางจอเพื่อบันทึก/ลบ
"""

from datetime import date, datetime, timedelta
import streamlit as st
from streamlit_calendar import calendar

import db
from schedule_utils import is_due, upcoming_due_dates, thai_weekday

st.set_page_config(page_title="🌸 Waan-Waan Habit Tracker", page_icon="🌸", layout="centered")

db.init_db()

# ---------- Cute custom styling ----------
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(180deg, #fff5f7 0%, #f3f0ff 100%); }
    .habit-card {
        background: white; padding: 14px 18px; border-radius: 16px;
        margin-bottom: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .due-today { border-left: 6px solid #ff9eb5; }
    h1, h2, h3 { color: #6b4c8a; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🌸 Daily Habit Tracker")
st.caption("ปฏิทินบันทึกประจำวัน + กิจกรรมวนซ้ำทุก N วัน ✨")

today = date.today()

# -------------------------------------------------------------
# 🪟 POPUP DIALOG: เด้งขึ้นมากลางจอเมื่อคลิกเลือกวันที่
# -------------------------------------------------------------
@st.dialog("📝 บันทึกกิจกรรมประจำวัน")
def open_entry_dialog(selected_d: date):
    st.markdown(f"### 📅 วันที่: **{thai_weekday(selected_d)} {selected_d.strftime('%d/%m/%Y')}**")
    
    habits = db.get_habits()
    due_on_selected = [h for h in habits if is_due(date.fromisoformat(h["start_date"]), h["interval_days"], selected_d)]

    # 1. เช็ค/ติ๊กกิจกรรมที่ต้องทำในวันนั้น
    if due_on_selected:
        st.markdown("✨ **กิจกรรมที่ต้องทำวันนี้:**")
        for h in due_on_selected:
            done = db.is_done_today(h["id"], selected_d)
            col1, col2 = st.columns([3, 1])
            with col1:
                status_text = "✅ ทำแล้ว" if done else "⏳ ยังไม่ได้ทำ"
                st.markdown(f"- **{h['emoji']} {h['name']}** ({status_text})")
            with col2:
                if not done:
                    if st.button("ทำแล้ว ✔️", key=f"dlg_done_{h['id']}_{selected_d}"):
                        db.add_log(h["id"], selected_d, note=None, completed=True)
                        st.rerun()
                else:
                    st.caption("เรียบร้อย")
        st.divider()

    # 2. ฟอร์มเขียนบันทึก/ไดอารี่
    st.markdown("✍️ **พิมพ์เรื่องราว/ไดอารี่วันนี้:**")
    note_input = st.text_area("วันนี้มีอะไรเกิดขึ้นบ้าง เล่าให้ฟังหน่อย...", height=100, key=f"note_area_{selected_d}")
    
    if st.button("💾 บันทึกเรื่องราว", use_container_width=True, key=f"save_btn_{selected_d}"):
        if note_input.strip():
            db.add_log(habit_id=None, log_date=selected_d, note=note_input.strip(), completed=False)
            st.success("บันทึกเรียบร้อย!")
            st.rerun()
        else:
            st.warning("กรุณาพิมพ์ข้อความก่อนบันทึกนะ")

    # 3. แสดงประวัติที่มีอยู่แล้วของวันนั้น + ปุ่มลบ 🗑️
    st.divider()
    st.markdown("📖 **บันทึกย้อนหลังของวันนี้:**")
    logs_on_selected = db.get_logs_for_date(selected_d)
    if not logs_on_selected:
        st.caption("ยังไม่มีบันทึกข้อความในวันนี้")
    for log in logs_on_selected:
        c_log1, c_log2 = st.columns([5, 1])
        with c_log1:
            if log["note"]:
                st.markdown(f"🗒️ {log['note']}")
            elif log["completed"]:
                h_name = "กิจกรรม"
                for h in habits:
                    if h["id"] == log["habit_id"]:
                        h_name = f"{h['emoji']} {h['name']}"
                st.markdown(f"✅ ทำสำเร็จ: {h_name}")
        with c_log2:
            # ปุ่มลบบันทึก
            if st.button("🗑️", key=f"del_log_btn_{log['id']}"):
                db.delete_log(log["id"])
                st.rerun()


# -------------------------------------------------------------
# 📌 MAIN TABS
# -------------------------------------------------------------
tab_calendar, tab_habits = st.tabs(["📅 ปฏิทิน", "🔁 กิจกรรมวนซ้ำ"])
habits = db.get_habits()

# ================= TAB 1: ปฏิทิน =================
with tab_calendar:
    events = []
    start_search = today - timedelta(days=90)
    
    # 1. ดึง "กิจกรรมวนซ้ำ" มาใส่ปฏิทิน
    for h in habits:
        start_d = date.fromisoformat(h["start_date"])
        due_dates = upcoming_due_dates(start_d, h["interval_days"], start_search, count=60)
        for d in due_dates:
            if start_search <= d <= today + timedelta(days=90):
                events.append({
                    "title": f"{h['emoji']} {h['name']}",
                    "start": d.isoformat(),
                    "end": d.isoformat(),
                    "allDay": True,
                    "backgroundColor": "#ff9eb5" if d == today else "#6b4c8a",
                    "borderColor": "#ff9eb5" if d == today else "#6b4c8a"
                })

    # 2. ดึง "ข้อความบันทึก" มาแสดงสั้นๆ บนช่องปฏิทิน
    all_logs = db.get_all_logs(limit=500)
    for log in all_logs:
        if log["note"]:
            short_note = log["note"] if len(log["note"]) <= 12 else log["note"][:12] + "..."
            events.append({
                "title": f"📝 {short_note}",
                "start": log["log_date"],
                "end": log["log_date"],
                "allDay": True,
                "backgroundColor": "#70a1ff",
                "borderColor": "#70a1ff"
            })

    # คอนฟิกปฏิทิน
    calendar_options = {
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,listMonth"
        },
        "initialView": "dayGridMonth",
        "selectable": True,
        "selectMirror": True,
        "timeZone": "UTC",
    }

    # แสดงปฏิทิน (เพิ่ม callbacks ให้ครอบคลุมทั้ง dateClick และ select)
    cal_res = calendar(
        events=events,
        options=calendar_options,
        callbacks=["dateClick", "select"],
        key="waan_fullcalendar_v3"
    )

    # ================= ตรวจจับการคลิกวันที่ =================
    clicked_date_str = None

    if cal_res:
        # กรณีใช้ select (คลิกเลือกวัน)
        if "select" in cal_res:
            select_info = cal_res["select"]
            clicked_date_str = select_info.get("startStr") or select_info.get("start")
        # กรณีใช้ dateClick
        elif "dateClick" in cal_res:
            click_info = cal_res["dateClick"]
            clicked_date_str = click_info.get("dateStr") or click_info.get("date")

    if clicked_date_str:
        # ตัดเวลาออก เอาเฉพาะ YYYY-MM-DD
        clean_str = str(clicked_date_str).split("T")[0].split(" ")[0]
        try:
            selected_date = date.fromisoformat(clean_str)
            open_entry_dialog(selected_date)
        except ValueError:
            pass


# ================= TAB 2: กิจกรรมวนซ้ำ =================
with tab_habits:
    st.subheader("🔁 ตั้งค่ากิจกรรมวนซ้ำ (ทุก N วัน)")
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
    st.subheader("📋 รายการกิจกรรมทั้งหมด")
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
            if st.button("ลบ 🗑️", key=f"del_{h['id']}"):
                db.delete_habit(h["id"])
                st.rerun()
