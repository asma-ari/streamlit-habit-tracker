# 🌸 Daily Habit Tracker & Diary Calendar

> **"สร้างนิสัยที่ดีและบันทึกความทรงจำในทุกๆ วัน ด้วยแอปปฏิทินพาสเทลสุดละมุน"**

👉 **[คลิกที่นี่เพื่อทดลองใช้งานแอปพลิเคชัน (Live Demo)](https://waan-waan-kgjg6irz6mbz2psyxfujdr.streamlit.app/)** 🚀

---

## ✨ ฟีเจอร์เด่น (Key Features)

* **📅 ปฏิทินโชว์ภาพรวม (Interactive Calendar):** 
  * แสดงสถานะกิจกรรมที่ทำสำเร็จ และข้อความบันทึกย้อนหลังแบบภาพรวมด้วย FullCalendar
  * คลิกที่วันที่บนปฏิทินเพื่อเปิด Dialog พิมพ์ไดอารี่ หรือเช็คกิจกรรมย้อนหลังได้ทันที
* **🔁 จัดการกิจกรรมวนซ้ำหลากหลายรูปแบบ (Flexible Habit Tracking):**
  * **เลือกวันในสัปดาห์:** เช่น ไปมหาลัยทุกวันจันทร์ หรือสระผมทุกวันพุธและศุกร์ (รวมอยู่ในแถบเดียวกัน ไม่เกะกะ)
  * **วนซ้ำทุก N วัน:** เช่น รดน้ำต้นไม้ทุกๆ 2 วัน หรือออกกำลังกายทุกๆ 3 วัน
  * **📌 นัดหมายทำครั้งเดียว:** ตั้งเตือนกิจกรรมล่วงหน้าเฉพาะวัน เช่น วันพุธมีสอบ, ไปพบหมอ
* **☑️ เช็คลิสต์ประจำวันสุดคลีน:**
  * แถบแสดงรายการกิจกรรมที่ต้องทำในแต่ละวัน สีเทาพาสเทลสบายตา
  * ติ๊กถูกทำสำเร็จในแถบได้ทันที ระบบจะอัปเดตลงปฏิทินให้อัตโนมัติ
* **📱 รองรับ PWA / Mobile Responsive:**
  * ใช้งานได้ลื่นไหลทั้งบนคอมพิวเตอร์ แท็บเล็ต และสมาร์ตโฟน
  * สามารถเพิ่มลงหน้าจอหลัก (Add to Home Screen) เพื่อใช้งานเหมือนแอปจริงได้

---

## 🛠️ เทคโนโลยีที่ใช้ (Tech Stack)

* **Frontend & Web Framework:** [Streamlit](https://streamlit.io/)
* **Calendar Component:** [streamlit-calendar](https://github.com/u/streamlit-calendar) (FullCalendar integration)
* **Database:** SQLite3 (จัดเก็บข้อมูล habits และ logs)
* **Deployment:** Streamlit Cloud

---

## 📂 โครงสร้างโปรเจกต์ (Project Structure)

```text
├── app.py              # หน้าต่างอินเทอร์เฟซหลักของ Streamlit และ UI Components
├── db.py               # จัดการฐานข้อมูล SQLite (CRUD operations)
├── schedule_utils.py   # ฟังก์ชันคำนวณวันกำหนดทำกิจกรรม (Due dates calculation)
├── requirements.txt    # รายการ Library ที่จำเป็นต้องใช้
└── README.md           # เอกสารอธิบายโปรเจกต์
