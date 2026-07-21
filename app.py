"""
app.py
แอป Daily Habit Tracker
- ปฏิทินแบบตาราง (Grid) พร้อมพรีวิวข้อมูลในแต่ละวัน
- คลิกที่วันนั้นๆ แล้วเด้ง Popup Dialog กลางหน้าจอเพื่อดู/เพิ่ม/ลบ บันทึกและกิจกรรม
"""

from datetime import date, timedelta
import calendar
import streamlit as st

import db
from schedule_utils import is_due, upcoming_due_dates, thai_weekday

st.set_page_config(page_title="🌸 Daily Habit Tracker", page_icon="🌸", layout="centered")

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
st.caption("ปฏิทินบันทึกประจำวัน + กิจกรรมวนซ้ำ N วัน ✨")

today = date.today()

# จัดการ Session State สำหรับเปลี่ยนเดือนในปฏิทินตาราง
if "cal_year" not in st.session_state:
    st.session_state.cal_year = today.year
if "cal_year" not in st.session_state:
    st.session_state.cal_year = today.year
if "cal_month" not in st.session_state:
    st.session_state.cal_month = today.month


# -------------------------------------------------------------
# 🪟 POPUP DIALOG: หน้าต่างเด้งกลางจอเมื่อคลิกวันที่
# -------------------------------------------------------------
@st.dialog("📝 จัดการบันทึกและกิจกรรม")
def open_entry_dialog(selected_d: date):
    st.markdown(f"### 📅 วันที่: **{thai_weekday(selected_d)} {selected_d.strftime('%d/%m/%Y')}**")
    
    habits = db.get_habits()
    due_on_selected = [h for h in habits if is_due(date.fromisoformat(h["start_date"]), h["interval_days"], selected_d)]

    # 1. เช็ค/ติ๊กกิจกรรมที่ต้องทำในวันนั้น
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
            # ปุ่มลบ
            if st.button("🗑️", key=f"del_log_btn_{log['id']}"):
                db.delete_log(log["id"])
                st.rerun()


# -------------------------------------------------------------
# 📌 TABS หลัก
# -------------------------------------------------------------
tab_calendar, tab_habits = st.tabs(["📅 ปฏิทิน", "🔁 กิจกรรมวนซ้ำ"])
habits = db.get_habits()

# ================= TAB 1: ปฏิทินตาราง Grid =================
with tab_calendar:
    # ปุ่มเปลี่ยนเดือน
    col_prev, col_title, col_next = st.columns([1, 3, 1])
    with col_prev:
        if st.button("◀ เดือนก่อน"):
            if st.session_state.cal_month == 1:
                st.session_state.cal_month = 12
                st.session_state.cal_year -= 1
            else:
                st.session_state.cal_month -= 1
            st.rerun()
    with col_title:
        thai_months = [
            "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
            "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
        ]
        st.markdown(f"<h3 style='text-align: center;'>{thai_months[st.session_state.cal_month]} {st.session_state.cal_year + 543}</h3>", unsafe_allow_html=True)
    with col_next:
        if st.button("เดือนถัดไป ▶"):
            if st.session_state.cal_month == 12:
                st.session_state.cal_month = 1
                st.session_state.cal_year += 1
            else:
                st.session_state.cal_month += 1
            st.rerun()

    st.markdown("---")

    # ดึงข้อมูล Log และ Habit ทั้งหมดของเดือนนี้มาเตรียมไว้แสดงผลในช่องปฏิทิน
    month_logs = db.get_logs_for_month(st.session_state.cal_year, st.session_state.cal_month)
    
    # สร้างโครงสร้างปฏิทินตาราง (เริ่มวันจันทร์)
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(st.session_state.cal_year, st.session_state.cal_month)

    # หัวตารางวันในสัปดาห์
    weekdays_header = ["จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส.", "อา."]
    cols = st.columns(7)
    for idx, day_name in enumerate(weekdays_header):
        cols[idx].markdown(f"<div style='text-align: center; font-weight: bold; color: #6b4c8a;'>{day_name}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # วาดตารางวัน
    for week in month_days:
        cols = st.columns(7)
        for idx, day in enumerate(week):
            with cols[idx]:
                if day == 0:
                    st.markdown("<div style='padding: 20px;'></div>", unsafe_allow_html=True)
                else:
                    current_date_obj = date(st.session_state.cal_year, st.session_state.cal_month, day)
                    date_str = current_date_obj.isoformat()
                    
                    # เช็คข้อมูลในวันนี้
                    is_today = (current_date_obj == today)
                    
                    # หากิจกรรมที่ต้องทำวันนี้
                    due_today_list = [h for h in habits if is_due(date.fromisoformat(h["start_date"]), h["interval_days"], current_date_obj)]
                    
                    # หาโน้ตหรือบันทึกในวันนี้
                    logs_today = [l for l in month_logs if l["log_date"] == date_str]
                    
                    # ตกแต่งปุ่มเลือกวัน
                    btn_label = f"{day}"
                    if is_today:
                        btn_label = f"📌 {day} (วันนี้)"
                    
                    # ปุ่มคลิกวันที่เพื่อเปิด Popup
                    if st.button(btn_label, key=f"grid_day_{date_str}", use_container_width=True):
                        open_entry_dialog(current_date_obj)

                    # แสดงพรีวิวข้อมูลเล็กๆ ใต้ปุ่มในช่องปฏิทิน
                    preview_html = "<div style='font-size: 11px; min-height: 40px; background: rgba(255,255,255,0.7); border-radius: 6px; padding: 2px 4px; margin-top: 2px;'>"
                    
                    # แสดงไอคอนกิจกรรม
                    for h in due_today_list:
                        done = db.is_done_today(h["id"], current_date_obj)
                        check_mark = "✅" if done else "⏳"
                        preview_html += f"<div>{check_mark} {h['emoji']} {h['name']}</div>"
                    
                    # แสดงโน้ตย่อ
                    for l in logs_today:
                        if l["note"]:
                            short_note = l["note"] if len(l["note"]) <= 10 else l["note"][:10] + "..."
                            preview_html += f"<div style='color: #0984e3;'>📝 {short_note}</div>"
                    
                    preview_html += "</div>"
                    st.markdown(preview_html, unsafe_allow_html=True)


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
