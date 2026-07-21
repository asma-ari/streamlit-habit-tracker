"""
schedule_utils.py
คำนวณว่ากิจกรรมแบบ "ทำทุก N วัน" ถึงกำหนดวันไหนบ้าง

หลักการ: กำหนด start_date เป็นวันเริ่มนับ แล้วกิจกรรมจะถึงกำหนดทุกๆ
N วันนับจากวันนั้น "ตลอดไป" ไม่ว่าจะข้ามวันในสัปดาห์ไหนก็ตาม
เช่น start_date = จันทร์, interval = 2 วัน
    -> ถึงกำหนด: จันทร์, พุธ, ศุกร์, อาทิตย์, อังคาร, พฤหัส, เสาร์, จันทร์, ...
(รูปแบบวนไปเรื่อยๆ ตามที่ผู้ใช้อยากได้ ไม่ใช่แค่ "ทุกวันจันทร์/พฤหัส" ตายตัว)
"""

import calendar as _calendar
from datetime import date, timedelta

THAI_WEEKDAYS = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
THAI_WEEKDAYS_SHORT = ["จ", "อ", "พ", "พฤ", "ศ", "ส", "อา"]
THAI_MONTHS = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]


def is_due(start_date: date, interval_days: int, on_date: date) -> bool:
    """เช็คว่าวันที่ on_date ถึงกำหนดของกิจกรรมนี้หรือไม่"""
    if on_date < start_date:
        return False
    delta = (on_date - start_date).days
    return delta % interval_days == 0


def next_due_date(start_date: date, interval_days: int, from_date: date) -> date:
    """หาว่าวันถัดไปที่ถึงกำหนด (รวมวันนี้ถ้าถึงกำหนดพอดี)"""
    if from_date < start_date:
        return start_date
    delta = (from_date - start_date).days
    remainder = delta % interval_days
    if remainder == 0:
        return from_date
    return from_date + timedelta(days=interval_days - remainder)


def upcoming_due_dates(start_date: date, interval_days: int, from_date: date, count: int = 5):
    """คืนลิสต์วันที่ถึงกำหนด N ครั้งถัดไป (รวมวันนี้ถ้าถึงกำหนด)"""
    dates = []
    current = next_due_date(start_date, interval_days, from_date)
    for _ in range(count):
        dates.append(current)
        current = current + timedelta(days=interval_days)
    return dates


def thai_weekday(d: date) -> str:
    return THAI_WEEKDAYS[d.weekday()]


def month_weeks(year: int, month: int):
    """คืนลิสต์ของสัปดาห์สำหรับตารางปฏิทินเดือนนั้นๆ
    แต่ละสัปดาห์คือลิสต์ของ 7 วัน (datetime.date) เริ่มจันทร์ถึงอาทิตย์
    รวมวันจากเดือนก่อน/หลังที่ล้นมาเติมเต็มสัปดาห์แรกและสุดท้ายด้วย"""
    cal = _calendar.Calendar(firstweekday=0)  # 0 = Monday
    return list(cal.monthdatescalendar(year, month))
