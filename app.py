"""
app.py
แอป Daily Habit Tracker
- ปฏิทิน FullCalendar
- รองรับการตั้งค่ากิจกรรมทั้งแบบ "ทำทุก N วัน" และ "ทำเฉพาะวันในสัปดาห์" (เช่น ไปมหาลัยทุกวันจันทร์)
- แถบกิจกรรมรูปทรงกล่องสีเทาอ่อน มี Checkbox อยู่ด้านใน
"""

from datetime import date, datetime, timedelta
import streamlit as st
from streamlit_calendar import calendar

import db
from schedule_utils import is_due, upcoming_due_dates, thai_weekday

st.set_page_config(page_title="🌸 Daily Habit Tracker", page_icon="🌸", layout="centered")

db.init_db()

# ---------- Custom Styling ----------
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(180deg, #fff5f7 0%, #f3f0ff 100%); }
    
    /* ตกแต่ง Container ให้กลายเป็นกล่องแถบสี่เหลี่ยมผืนผ้าสีเทาอ่อน */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #f1f3f5 !important;
        border: 1.5px solid #e9ecef !important;
        border-radius: 16px !important;
        padding: 10px 18px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"] .stCheckbox label p {
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        color: #343a40 !important;
    }

    h1, h2, h3 { color: #6b4c8a; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🌸 Daily Habit Tracker")
st.caption("ปฏิทินบันทึกประจำวัน + กิจกรรมวนซ้ำ ✨")

today = date.today()

# -------------------------------------------------------------
# 🪟 POPUP DIALOG 1: บันทึกประจำวัน (เมื่อคลิกปฏิทิน)
# -------------------------------------------------------------
@st.dialog("📝 บันทึกกิจกรรมประจำวัน")
def open_entry_dialog(selected_d: date):
    st.markdown(f"### 📅 วันที่: **{thai_weekday(selected_d)} {selected_d.strftime('%d/%m/%Y')}**")
    
    habits = db.get_habits()
    due_on_selected = [h for h in habits if is_due(date.fromisoformat(h["start_date"]), h["interval_days"], selected_d)]

    if due_on_selected:
        st.markdown("✨ **กิจกรรมในวันนี้:**")
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

    st.markdown("✍️ **พิมพ์เรื่องราว/ไดอารี่วันนี้:**")
    note_input = st.text_area("วันนี้มีอะไรเกิดขึ้นบ้าง เล่าให้ฟังหน่อย...", height=100, key=f"note_area_{selected_d}")
    
    if st.button("💾 บันทึกเรื่องราว", use_container_width=True, key=f"save_btn_{selected_d}"):
        if note_input.strip():
            db.add_log(habit_id=None, log_date=selected_d, note=note_input.strip(), completed=False)
            st.success("บันทึกเรียบร้อย!")
            st.rerun()
        else:
            st.warning("กรุณาพิมพ์ข้อความก่อนบันทึกนะ")

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
            if st.button("🗑️", key=f"del_log_btn_{log['id']}"):
                db.delete_log(log["id"])
                st.rerun()


# -------------------------------------------------------------
# 🪟 POPUP DIALOG 2: แก้ไขกิจกรรมวนซ้ำ
# -------------------------------------------------------------
@st.dialog("✏️ แก้ไขกิจกรรมวนซ้ำ")
def open_edit_habit_dialog(habit):
    st.markdown(f"### แก้ไขกิจกรรม: **{habit['emoji']} {habit['name']}**")
    
    with st.form(key=f"edit_habit_form_{habit['id']}"):
        c1, c2 = st.columns([1, 3])
        new_emoji = c1.text_input("อีโมจิ", value=habit["emoji"], max_chars=2)
        new_name = c2.text_input("ชื่อกิจกรรม", value=habit["name"])
        
        c3, c4 = st.columns(2)
        new_interval = c3.number_input("ทำทุกกี่วัน", min_value=1, max_value=365, value=int(habit["interval_days"]))
        current_start = date.fromisoformat(habit["start_date"])
        new_start = c4.date_input("เริ่มนับจากวันที่", value=current_start)
        
        submit_edit = st.form_submit_button("💾 บันทึกการแก้ไข", use_container_width=True)
        if submit_edit:
            if new_name.strip():
                db.update_habit(habit["id"], new_name.strip(), new_emoji or "✨", int(new_interval), new_start)
                st.success("แก้ไขกิจกรรมเรียบร้อยแล้ว!")
                st.rerun()
            else:
                st.warning("กรุณาใส่ชื่อกิจกรรมด้วยนะ")


# -------------------------------------------------------------
# 📌 MAIN TABS
# -------------------------------------------------------------
tab_calendar, tab_habits = st.tabs(["📅 ปฏิทิน", "🔁 ตั้งค่ากิจกรรม"])
habits = db.get_habits()

# ================= TAB 1: ปฏิทิน =================
with tab_calendar:
    events = []
    start_search = today - timedelta(days=90)
    
    # 1. แสดงกิจกรรมที่ทำสำเร็จแล้วลงปฏิทิน
    all_logs = db.get_all_logs(limit=500)
    for log in all_logs:
        if log["completed"]:
            h_name = f"{log['habit_emoji'] or '✨'} {log['habit_name'] or 'กิจกรรม'}"
            events.append({
                "title": f"✅ {h_name}",
                "start": log["log_date"],
                "end": log["log_date"],
                "allDay": True,
                "backgroundColor": "#ff9eb5",
                "borderColor": "#ff9eb5"
            })
        elif log["note"]:
            short_note = log["note"] if len(log["note"]) <= 12 else log["note"][:12] + "..."
            events.append({
                "title": f"📝 {short_note}",
                "start": log["log_date"],
                "end": log["log_date"],
                "allDay": True,
                "backgroundColor": "#70a1ff",
                "borderColor": "#70a1ff"
            })

    # แสดงกำหนดการล่วงหน้าบนปฏิทิน
    for h in habits:
        start_d = date.fromisoformat(h["start_date"])
        due_dates = upcoming_due_dates(start_d, h["interval_days"], start_search, count=60)
        for d in due_dates:
            if not db.is_done_today(h["id"], d) and d >= today:
                events.append({
                    "title": f"⏳ {h['emoji']} {h['name']}",
                    "start": d.isoformat(),
                    "end": d.isoformat(),
                    "allDay": True,
                    "backgroundColor": "#a5b1c2",
                    "borderColor": "#a5b1c2"
                })

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

    cal_res = calendar(
        events=events,
        options=calendar_options,
        callbacks=["dateClick", "select"],
        key="waan_fullcalendar_v12"
    )

    # ---------------------------------------------------------
    # 📌 แถบกิจกรรมรูปทรงกล่องสีเทาอ่อน มี Checkbox อยู่ด้านใน
    # ---------------------------------------------------------
    st.divider()
    st.subheader(f"📌 กิจกรรมที่ต้องทำวันนี้ ({thai_weekday(today)}ที่ {today.strftime('%d/%m/%Y')})")
    
    due_today_not_done = [
        h for h in habits 
        if is_due(date.fromisoformat(h["start_date"]), h["interval_days"], today) 
        and not db.is_done_today(h["id"], today)
    ]

    if not due_today_not_done:
        st.info("🎉 วันนี้ไม่มีกิจกรรมค้างแล้ว! พักผ่อนได้เลย 🛋️")
    else:
        for h in due_today_not_done:
            with st.container(border=True):
                freq_label = f"ทำทุกวัน{thai_weekday(date.fromisoformat(h['start_date']))}" if h['interval_days'] == 7 else f"ทำทุกๆ {h['interval_days']} วัน"
                is_checked = st.checkbox(
                    f"{h['emoji']} **{h['name']}** *({freq_label})*",
                    key=f"chk_todo_{h['id']}"
                )
                if is_checked:
                    db.add_log(h["id"], today, note=None, completed=True)
                    st.rerun()

    # ตรวจจับคลิกวันที่
    clicked_date_str = None
    if cal_res:
        if "select" in cal_res:
            select_info = cal_res["select"]
            clicked_date_str = select_info.get("startStr") or select_info.get("start")
        elif "dateClick" in cal_res:
            click_info = cal_res["dateClick"]
            clicked_date_str = click_info.get("dateStr") or click_info.get("date")

    if clicked_date_str:
        clean_str = str(clicked_date_str).split("T")[0].split(" ")[0]
        try:
            selected_date = date.fromisoformat(clean_str)
            open_entry_dialog(selected_date)
        except ValueError:
            pass


# ================= TAB 2: ตั้งค่ากิจกรรม =================
with tab_habits:
    st.subheader("🔁 ตั้งค่ากิจกรรมวนซ้ำ / กิจกรรมประจำวัน")
    
    # สลับประเภทรูปแบบกิจกรรม
    repeat_type = st.radio(
        "รูปแบบกิจกรรม:",
        ["ทำตามวันในสัปดาห์ (เช่น ทุกวันจันทร์)", "ทำทุกๆ N วัน (เช่น ทุกๆ 2 วัน)"],
        horizontal=True
    )
    
    with st.form("add_habit_form", clear_on_submit=True):
        c1, c2 = st.columns([1, 3])
        emoji = c1.text_input("อีโมจิ", value="🎓" if "วันในสัปดาห์" in repeat_type else "✨", max_chars=2)
        name = c2.text_input("ชื่อกิจกรรม เช่น ไปมหาลัย, สระผม, รดน้ำต้นไม้")
        
        if "วันในสัปดาห์" in repeat_type:
            weekday_choice = st.selectbox(
                "เลือกวันในสัปดาห์ที่ต้องทำ:",
                ["วันจันทร์", "วันอังคาร", "วันพุธ", "วันพฤหัสบดี", "วันศุกร์", "วันเสาร์", "วันอาทิตย์"]
            )
            # หา offset วันถัดไปที่ตรงกับวันที่เลือก
            weekday_map = {"วันจันทร์": 0, "วันอังคาร": 1, "วันพุธ": 2, "วันพฤหัสบดี": 3, "วันศุกร์": 4, "วันเสาร์": 5, "วันอาทิตย์": 6}
            target_weekday = weekday_map[weekday_choice]
            
            # คำนวณหา วันที่ ของวันในสัปดาห์นั้นถัดไป
            days_ahead = target_weekday - today.weekday()
            if days_ahead < 0:
                days_ahead += 7
            start_date_input = today + timedelta(days=days_ahead)
            interval_days = 7  # 7 วันวนซ้ำ 1 ครั้ง
        else:
            c3, c4 = st.columns(2)
            interval_days = c3.number_input("ทำทุกกี่วัน", min_value=1, max_value=365, value=2)
            start_date_input = c4.date_input("เริ่มนับจากวันที่", value=today)

        submitted = st.form_submit_button("บันทึกกิจกรรม 💾")
        if submitted:
            if name.strip():
                db.add_habit(name.strip(), emoji or "✨", int(interval_days), start_date_input)
                st.success(f"เพิ่ม '{name}' เรียบร้อยแล้ว!")
                st.rerun()
            else:
                st.warning("กรุณาใส่ชื่อกิจกรรมด้วยนะ")

    st.divider()
    st.subheader("📋 รายการกิจกรรมทั้งหมด")
    if not habits:
        st.info("ยังไม่มีกิจกรรมวนซ้ำ ลองเพิ่มดูด้านบนได้เลย")
    for h in habits:
        start_d = date.fromisoformat(h["start_date"])
        upcoming = upcoming_due_dates(start_d, h["interval_days"], today, count=4)
        upcoming_str = ", ".join(f"{thai_weekday(d)[:2]} {d.strftime('%d/%m')}" for d in upcoming)
        
        freq_text = f"ทำทุกวัน{thai_weekday(start_d)}" if h["interval_days"] == 7 else f"ทุก {h['interval_days']} วัน"
        
        col_info, col_btns = st.columns([3, 2])
        with col_info:
            st.markdown(
                f"**{h['emoji']} {h['name']}** — {freq_text}  \n"
                f"<small style='color: gray;'>📆 กำหนดถัดไป: {upcoming_str}</small>",
                unsafe_allow_html=True
            )
        with col_btns:
            btn1, btn2 = st.columns(2)
            with btn1:
                if st.button("✏️ แก้ไข", key=f"edit_h_{h['id']}", use_container_width=True):
                    open_edit_habit_dialog(h)
            with btn2:
                if st.button("🗑️ ลบ", key=f"del_h_{h['id']}", use_container_width=True):
                    db.delete_habit(h["id"])
                    st.rerun()
