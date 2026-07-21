"""
app.py
แอป Daily Habit Tracker (เปลี่ยนจาก Dialog เป็นกล่องข้อความอัจฉริยะ ปิด/เปิดอัตโนมัติ)
"""

from datetime import date, datetime, timedelta
import streamlit as st
from streamlit_calendar import calendar

import db
from schedule_utils import is_due, upcoming_due_dates, thai_weekday, THAI_WEEKDAYS

st.set_page_config(page_title="🌸 Daily Habit Tracker", page_icon="🌸", layout="centered")

db.init_db()

# --- Session States ---
if "user" not in st.session_state:
    st.session_state.user = None

if "selected_date" not in st.session_state:
    st.session_state.selected_date = None

if "editing_habit" not in st.session_state:
    st.session_state.editing_habit = None


# -------------------------------------------------------------
# 🔐 หน้าแรกเลือกเข้าสู่ระบบ / สมัครสมาชิก (แสดงเมื่อยังไม่ Login)
# -------------------------------------------------------------
if not st.session_state.user:
    st.markdown("<br>", unsafe_allow_html=True)
    st.title("🌸 Daily Habit Tracker")
    st.caption("พื้นที่บันทึกไดอารี่ และติดตามกิจกรรมประจำวันของคุณ ✨")
    
    st.divider()
    
    st.markdown(
        """
        ### 👋 ยินดีต้อนรับสู่ Daily Habit Tracker!
        
        เพื่อให้ข้อมูลปฏิทิน กิจกรรม และไดอารี่ของคุณเป็น**ส่วนตัว 100%**  
        ระบบของเราจึงแยกพื้นที่บันทึกของแต่ละคนออกจากกันอย่างชัดเจนครับ
        
        > 💡 **การสมัครสมาชิกทำได้ง่ายมาก!**  
        > ใช้เพียงการสร้าง **ชื่อผู้ใช้ (Username)** และ **รหัสผ่าน (Password)** เท่านั้น  
        > ไม่ต้องใช้อีเมล ไม่ต้องกรอกข้อมูลส่วนตัวใดๆ เพิ่มเติมเลยครับ 🔒✨
        """
    )
    
    st.divider()
    
    # ฟอร์มเข้าสู่ระบบ / สมัครสมาชิกแบบหน้าจอปกติ ไม่ติดปัญหาป๊อปอัปค้าง
    tab_login, tab_signup = st.tabs(["🔑 เข้าสู่ระบบ", "📝 สมัครสมาชิก"])
    
    with tab_login:
        with st.form("login_form"):
            username = st.text_input("ชื่อผู้ใช้ (Username)").strip()
            password = st.text_input("รหัสผ่าน (Password)", type="password").strip()
            btn_login = st.form_submit_button("เข้าสู่ระบบ 🚀", use_container_width=True)
            
            if btn_login:
                if username and password:
                    user = db.login_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง!")
                else:
                    st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน")
                    
    with tab_signup:
        with st.form("signup_form"):
            new_username = st.text_input("ตั้งชื่อผู้ใช้ (Username)").strip()
            new_password = st.text_input("ตั้งรหัสผ่าน (Password)", type="password").strip()
            confirm_password = st.text_input("ยืนยันรหัสผ่านอีกครั้ง", type="password").strip()
            btn_signup = st.form_submit_button("สร้างบัญชีใหม่ ✨", use_container_width=True)
            
            if btn_signup:
                if new_username and new_password:
                    if new_password != confirm_password:
                        st.error("❌ รหัสผ่านทั้งสองช่องไม่ตรงกัน!")
                    else:
                        success, msg = db.register_user(new_username, new_password)
                        if success:
                            st.success("🎉 สมัครสมาชิกสำเร็จ! สามารถเข้าสู่ระบบได้เลย")
                        else:
                            st.error(f"❌ {msg}")
                else:
                    st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน")
                    
    st.stop()

# -------------------------------------------------------------
# 🏠 หน้าจอหลักของแอป (แสดงเมื่อ Login แล้ว)
# -------------------------------------------------------------
user_id = st.session_state.user["id"]
user_name = st.session_state.user["username"]

col_header, col_logout = st.columns([3, 1])
with col_header:
    st.title("🌸 Daily Habit Tracker")
    st.caption(f"ยินดีต้อนรับคุณ **{user_name}** ✨")
with col_logout:
    st.write("")
    if st.button("ออกจากระบบ 🚪", use_container_width=True):
        st.session_state.user = None
        st.rerun()

today = date.today()

# 📌 MAIN TABS
tab_calendar, tab_habits = st.tabs(["📅 ปฏิทิน", "🔁 ตั้งค่ากิจกรรม"])
habits = db.get_habits(user_id)

# ================= TAB 1: ปฏิทิน =================
with tab_calendar:
    events = []
    start_search = today - timedelta(days=90)
    
    all_logs = db.get_all_logs(user_id, limit=500)
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

    for h in habits:
        start_d = date.fromisoformat(h["start_date"])
        w_str = h.get("weekdays", "")
        
        if w_str == "ONCE":
            if not db.is_done_today(h["id"], user_id, start_d) and start_d >= today:
                events.append({
                    "title": f"📌 {h['emoji']} {h['name']}",
                    "start": start_d.isoformat(),
                    "end": start_d.isoformat(),
                    "allDay": True,
                    "backgroundColor": "#ff7675",
                    "borderColor": "#ff7675"
                })
        else:
            due_dates = upcoming_due_dates(start_d, h["interval_days"], start_search, count=60, weekdays_str=w_str)
            for d in due_dates:
                if not db.is_done_today(h["id"], user_id, d) and d >= today:
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
        key="waan_fullcalendar_v27"
    )

    # ตรวจสอบว่ามีการคลิกวันที่บนปฏิทินหรือไม่
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
            st.session_state.selected_date = date.fromisoformat(clean_str)
        except ValueError:
            pass

    # 📝 ส่วนสำหรับแสดงกล่องบันทึกไดอารี่ (ปรากฏขึ้นมาเมื่อคลิกวันที่บนปฏิทิน และกดปิดได้สมบูรณ์)
    if st.session_state.selected_date:
        selected_d = st.session_state.selected_date
        st.divider()
        
        col_title, col_close = st.columns([5, 1])
        with col_title:
            st.markdown(f"### 📝 บันทึกประจำวัน: **{thai_weekday(selected_d)} {selected_d.strftime('%d/%m/%Y')}**")
        with col_close:
            if st.button("❌ ปิดหน้าต่าง", use_container_width=True):
                st.session_state.selected_date = None
                st.rerun()

        due_on_selected = [
            h for h in habits 
            if is_due(date.fromisoformat(h["start_date"]), h["interval_days"], selected_d, h.get("weekdays", ""))
        ]

        if due_on_selected:
            st.markdown("✨ **กิจกรรม/นัดหมายในวันนี้:**")
            for h in due_on_selected:
                done = db.is_done_today(h["id"], user_id, selected_d)
                c_h1, c_h2 = st.columns([3, 1])
                with c_h1:
                    status_text = "✅ ทำแล้ว" if done else "⏳ ยังไม่ได้ทำ"
                    st.markdown(f"- **{h['emoji']} {h['name']}** ({status_text})")
                with c_h2:
                    if not done:
                        if st.button("ทำแล้ว ✔️", key=f"box_done_{h['id']}_{selected_d}"):
                            db.add_log(user_id, h["id"], selected_d, note=None, completed=True)
                            st.rerun()
            st.divider()

        # ฟอร์มเขียนไดอารี่ กดบันทึกแล้วจะปิดกล่องอัตโนมัติทันที
        with st.form(key=f"inline_diary_form_{selected_d}", clear_on_submit=True):
            st.markdown("✍️ **พิมพ์เรื่องราว/ไดอารี่วันนี้:**")
            note_input = st.text_area("วันนี้มีอะไรเกิดขึ้นบ้าง เล่าให้ฟังหน่อย...", height=100)
            
            save_diary = st.form_submit_button("💾 บันทึกเรื่องราว", use_container_width=True)
            if save_diary:
                if note_input.strip():
                    db.add_log(user_id, habit_id=None, log_date=selected_d, note=note_input.strip(), completed=False)
                    st.session_state.selected_date = None  # ปิดกล่องทันทีหลังบันทึก
                    st.rerun()
                else:
                    st.warning("กรุณาพิมพ์ข้อความก่อนบันทึกนะ")

        st.markdown("📖 **บันทึกย้อนหลังของวันนี้:**")
        logs_on_selected = db.get_logs_for_date(user_id, selected_d)
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
                    db.delete_log(log["id"], user_id)
                    st.rerun()

    st.divider()
    st.subheader(f"📌 กิจกรรมที่ต้องทำวันนี้ ({thai_weekday(today)}ที่ {today.strftime('%d/%m/%Y')})")
    
    due_today_not_done = []
    for h in habits:
        w_str = h.get("weekdays", "")
        start_d = date.fromisoformat(h["start_date"])
        
        if w_str == "ONCE":
            if start_d == today and not db.is_done_today(h["id"], user_id, today):
                due_today_not_done.append(h)
        elif is_due(start_d, h["interval_days"], today, w_str) and not db.is_done_today(h["id"], user_id, today):
            due_today_not_done.append(h)

    if not due_today_not_done:
        st.info("🎉 วันนี้ไม่มีกิจกรรมค้างแล้ว! พักผ่อนได้เลย 🛋️")
    else:
        for h in due_today_not_done:
            w_str = h.get("weekdays", "")
            if w_str == "ONCE":
                freq_label = "นัดหมายครั้งเดียว"
            elif w_str:
                day_names = [THAI_WEEKDAYS[int(w)][3:] for w in w_str.split(",") if w.isdigit()]
                freq_label = f"ทำทุกวัน{', '.join(day_names)}"
            else:
                freq_label = f"ทำทุกๆ {h['interval_days']} วัน"

            is_checked = st.checkbox(
                f"{h['emoji']} **{h['name']}** *({freq_label})*",
                key=f"chk_todo_{h['id']}"
            )
            if is_checked:
                db.add_log(user_id, h["id"], today, note=None, completed=True)
                st.rerun()


# ================= TAB 2: ตั้งค่ากิจกรรม =================
with tab_habits:
    st.subheader("🔁 ตั้งค่ากิจกรรม / นัดหมายสำคัญ")
    
    # ส่วนแก้ไขกิจกรรม (แสดงขึ้นมาเมื่อกดปุ่มแก้ไข)
    if st.session_state.editing_habit:
        h_edit = st.session_state.editing_habit
        with st.container(border=True):
            st.markdown(f"### ✏️ แก้ไขกิจกรรม: **{h_edit['emoji']} {h_edit['name']}**")
            with st.form(key=f"edit_habit_form_{h_edit['id']}"):
                c1, c2 = st.columns([1, 3])
                new_emoji = c1.text_input("อีโมจิ", value=h_edit["emoji"], max_chars=2)
                new_name = c2.text_input("ชื่อกิจกรรม", value=h_edit["name"])
                
                weekdays_str = h_edit.get("weekdays", "")
                if weekdays_str == "ONCE":
                    current_start = date.fromisoformat(h_edit["start_date"])
                    new_start = st.date_input("วันที่ทำกิจกรรม:", value=current_start)
                    new_w_str = "ONCE"
                elif weekdays_str:
                    curr_days = [THAI_WEEKDAYS[int(w)] for w in weekdays_str.split(",") if w.isdigit()]
                    new_selected_weekdays = st.multiselect("เลือกวันในสัปดาห์:", THAI_WEEKDAYS, default=curr_days)
                    new_start = today
                else:
                    c3, c4 = st.columns(2)
                    new_interval = c3.number_input("ทำทุกกี่วัน", min_value=1, max_value=365, value=int(h_edit["interval_days"]))
                    current_start = date.fromisoformat(h_edit["start_date"])
                    new_start = c4.date_input("เริ่มนับจากวันที่", value=current_start)
                    new_w_str = ""
                
                c_save, c_cancel = st.columns(2)
                submit_edit = c_save.form_submit_button("💾 บันทึกการแก้ไข", use_container_width=True)
                cancel_edit = c_cancel.form_submit_button("❌ ยกเลิก", use_container_width=True)
                
                if submit_edit:
                    if new_name.strip():
                        if weekdays_str == "ONCE":
                            db.update_habit(h_edit["id"], user_id, new_name.strip(), new_emoji or "📝", 0, new_start, "ONCE")
                        elif weekdays_str:
                            weekday_map = {name: idx for idx, name in enumerate(THAI_WEEKDAYS)}
                            w_indices = sorted([str(weekday_map[d]) for d in new_selected_weekdays])
                            new_w_str = ",".join(w_indices)
                            db.update_habit(h_edit["id"], user_id, new_name.strip(), new_emoji or "✨", 1, today, new_w_str)
                        else:
                            db.update_habit(h_edit["id"], user_id, new_name.strip(), new_emoji or "✨", int(new_interval), new_start, "")
                        
                        st.session_state.editing_habit = None
                        st.rerun()
                    else:
                        st.warning("กรุณาใส่ชื่อกิจกรรมด้วยนะ")
                
                if cancel_edit:
                    st.session_state.editing_habit = None
                    st.rerun()
        st.divider()

    repeat_type = st.radio(
        "รูปแบบกิจกรรม:",
        ["📌 ทำครั้งเดียว/นัดหมายล่วงหน้า (เช่น สอบ, ไปพบหมอ)", "🗓️ ทำตามวันในสัปดาห์ (เช่น ทุกวันพุธ, ศุกร์)", "🔄 ทำทุกๆ N วัน (เช่น ทุกๆ 2 วัน)"],
        horizontal=False
    )
    
    with st.form("add_habit_form", clear_on_submit=True):
        c1, c2 = st.columns([1, 3])
        
        default_emoji = "📚" if "ครั้งเดียว" in repeat_type else ("🎓" if "วันในสัปดาห์" in repeat_type else "✨")
        emoji = c1.text_input("อีโมจิ", value=default_emoji, max_chars=2)
        name = c2.text_input("ชื่อกิจกรรม เช่น สอบวิชา Coding, สระผม, รดน้ำต้นไม้")
        
        if "ทำครั้งเดียว" in repeat_type:
            event_date = st.date_input("วันที่ทำกิจกรรม/สอบ:", value=today + timedelta(days=1))
        elif "วันในสัปดาห์" in repeat_type:
            selected_weekdays = st.multiselect("เลือกวันในสัปดาห์ที่ต้องทำ:", THAI_WEEKDAYS, default=["วันพุธ"])
        else:
            c3, c4 = st.columns(2)
            interval_days = c3.number_input("ทำทุกกี่วัน", min_value=1, max_value=365, value=2)
            start_date_input = c4.date_input("เริ่มนับจากวันที่", value=today)

        submitted = st.form_submit_button("บันทึกกิจกรรม 💾")
        if submitted:
            if not name.strip():
                st.warning("กรุณาใส่ชื่อกิจกรรมด้วยนะ")
            elif "ทำครั้งเดียว" in repeat_type:
                db.add_habit(user_id, name.strip(), emoji or "📌", 0, event_date, "ONCE")
                st.rerun()
            elif "วันในสัปดาห์" in repeat_type:
                if not selected_weekdays:
                    st.warning("กรุณาเลือกวันในสัปดาห์อย่างน้อย 1 วันนะ")
                else:
                    weekday_map = {day_name: idx for idx, day_name in enumerate(THAI_WEEKDAYS)}
                    w_indices = sorted([str(weekday_map[d]) for d in selected_weekdays])
                    w_str = ",".join(w_indices)
                    db.add_habit(user_id, name.strip(), emoji or "✨", 1, today, w_str)
                    st.rerun()
            else:
                db.add_habit(user_id, name.strip(), emoji or "✨", int(interval_days), start_date_input, "")
                st.rerun()

    st.divider()
    st.subheader("📋 รายการกิจกรรมทั้งหมด")
    if not habits:
        st.info("ยังไม่มีกิจกรรม ลองเพิ่มดูด้านบนได้เลย")
    for h in habits:
        start_d = date.fromisoformat(h["start_date"])
        w_str = h.get("weekdays", "")
        
        if w_str == "ONCE":
            freq_text = f"📌 ทำครั้งเดียววันที่ {start_d.strftime('%d/%m/%Y')}"
            upcoming_str = f"{thai_weekday(start_d)[:2]} {start_d.strftime('%d/%m')}"
        elif w_str:
            day_names = [THAI_WEEKDAYS[int(w)][3:] for w in w_str.split(",") if w.isdigit()]
            freq_text = f"ทำทุกวัน{', '.join(day_names)}"
            upcoming = upcoming_due_dates(start_d, h["interval_days"], today, count=4, weekdays_str=w_str)
            upcoming_str = ", ".join(f"{thai_weekday(d)[:2]} {d.strftime('%d/%m')}" for d in upcoming)
        else:
            freq_text = f"ทุก {h['interval_days']} วัน"
            upcoming = upcoming_due_dates(start_d, h["interval_days"], today, count=4, weekdays_str=w_str)
            upcoming_str = ", ".join(f"{thai_weekday(d)[:2]} {d.strftime('%d/%m')}" for d in upcoming)
        
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
                    st.session_state.editing_habit = h
                    st.rerun()
            with btn2:
                if st.button("🗑️ ลบ", key=f"del_h_{h['id']}", use_container_width=True):
                    db.delete_habit(h["id"], user_id)
                    st.rerun()
