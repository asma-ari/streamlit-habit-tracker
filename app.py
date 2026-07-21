# -------------------------------------------------------------
# 💬 ฟังก์ชันป๊อปอัพบันทึกประจำวัน (แบบเดิม เพิ่มเติมคือปิดเองอัตโนมัติ)
# -------------------------------------------------------------
@st.dialog("📝 บันทึกกิจกรรมประจำวัน")
def open_diary_dialog(selected_d, user_id, habits):
    st.markdown(f"📅 **วันที่: {thai_weekday(selected_d)} {selected_d.strftime('%d/%m/%Y')}**")
    
    # 1. แสดงกิจกรรมที่ต้องทำในวันนั้น
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
                    if st.button("ทำแล้ว ✔️", key=f"dlg_done_{h['id']}_{selected_d}"):
                        db.add_log(user_id, h["id"], selected_d, note=None, completed=True)
                        # 💡 บันทึกเสร็จแล้วปิดป๊อปอัพทันที
                        st.session_state.selected_date = None
                        st.rerun()
        st.divider()

    # 2. ฟอร์มเขียนไดอารี่
    with st.form(key=f"dialog_diary_form_{selected_d}", clear_on_submit=True):
        st.markdown("✍️ **พิมพ์เรื่องราว/ไดอารี่วันนี้:**")
        note_input = st.text_area("วันนี้มีอะไรเกิดขึ้นบ้าง เล่าให้ฟังหน่อย...", height=100)
        
        save_diary = st.form_submit_button("💾 บันทึกเรื่องราว", use_container_width=True)
        if save_diary:
            if note_input.strip():
                db.add_log(user_id, habit_id=None, log_date=selected_d, note=note_input.strip(), completed=False)
                
                # 💡 จุดสำคัญ: สั่งล้างค่าวันที่ เพื่อปิดหน้าต่างป๊อปอัพทันทีหลังกดบันทึก!
                st.session_state.selected_date = None
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
            if st.button("🗑️", key=f"del_dlg_log_{log['id']}"):
                db.delete_log(log["id"], user_id)
                st.rerun()
