import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="CAT STOCK", page_icon="📦", layout="centered")

# ใส่ URL เว็บแอปของ Google Apps Script ที่คุณคัดลอกมาตรงนี้
WEB_APP_URL = "https://google.com"

def get_thai_time():
    tz = timezone(timedelta(hours=7))
    return datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S")

@st.cache_data(ttl=60)
def load_data():
    res = requests.get(WEB_APP_URL)
    data = res.json()
    if len(data) <= 1:
        return pd.DataFrame(columns=["รหัสสินค้า", "ชื่อสินค้า", "จำนวนสินค้า"])
    df = pd.DataFrame(data[1:], columns=data[0])
    df["รหัสสินค้า"] = df["รหัสสินค้า"].astype(str)
    df["ชื่อสินค้า"] = df["ชื่อสินค้า"].astype(str)
    df["จำนวนสินค้า"] = pd.to_numeric(df["จำนวนสินค้า"], errors="coerce").fillna(0).astype(int)
    return df

@st.cache_data(ttl=60)
def load_history():
    res = requests.get(f"{WEB_APP_URL}?action=history")
    data = res.json()
    if len(data) <= 1:
        return pd.DataFrame(columns=["วันที่-เวลา", "ประเภท", "รหัสสินค้า", "ชื่อสินค้า", "จำนวน", "ผู้ทำรายการ"])
    df_hist = pd.DataFrame(data[1:], columns=data[0])
    df_hist["รหัสสินค้า"] = df_hist["รหัสสินค้า"].astype(str)
    df_hist["ชื่อสินค้า"] = df_hist["ชื่อสินค้า"].astype(str)
    return df_hist

def save_data(df):
    rows = [df.columns.tolist()] + df.values.tolist()
    requests.post(WEB_APP_URL, json={"type": "stock", "rows": rows})
    st.cache_data.clear()

def save_history(action_type, code, name, amount, user):
    timestamp = get_thai_time()
    row = [timestamp, action_type, str(code), str(name), int(amount), str(user)]
    requests.post(WEB_APP_URL, json={"type": "history", "row": row})
    st.cache_data.clear()

def highlight_low_stock(val):
    if val <= 2:
        return 'color: #FF4B4B; font-weight: bold;'
    return ''

st.title("📦 CAT STOCK")
st.caption("ระบบจัดการสต็อกสินค้าครบวงจร")

df = load_data()

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🔍 ค้นหาสินค้า",
    "🆕 สินค้าใหม่", 
    "➕ เพิ่มจำนวน", 
    "➖ ลดจำนวน", 
    "🗑️ ลบรายการ",
    "📜 ประวัติเบิกเข้า-ออก",
    "📦 สินค้าทั้งหมด",
    "⚠️ สินค้าขาดแคลน"
])

with tab1:
    with st.form("search_form"):
        s_query = st.text_input("ใส่รหัสสินค้า หรือ ชื่อสินค้าที่ต้องการตรวจสอบ", placeholder="เช่น A0001 หรือ มอเตอร์")
        if st.form_submit_button("ค้นหาข้อมูล", type="primary", use_container_width=True):
            q = s_query.strip()
            if q == "":
                st.warning("⚠️ กรุณากรอกรหัสหรือชื่อสินค้า")
            else:
                result = df[
                    (df["รหัสสินค้า"].str.lower() == q.lower()) | 
                    (df["ชื่อสินค้า"].str.contains(q, case=False, na=False))
                ]
                if not result.empty:
                    st.success(f"✅ พบข้อมูลที่ตรงกับ '{q}' จำนวน {len(result)} รายการ")
                    st.dataframe(result, use_container_width=True, hide_index=True)
                else:
                    st.error(f"❌ ไม่พบข้อมูลสินค้า '{q}' ในระบบ")

with tab2:
    with st.form("add_new_form", clear_on_submit=True):
        code = st.text_input("รหัสสินค้า", placeholder="เช่น P001")
        name = st.text_input("ชื่อสินค้า", placeholder="เช่น อาหารแมว 1kg")
        amount = st.number_input("จำนวนสินค้าเริ่มต้น", min_value=1, step=1, value=1)
        user_new = st.text_input("ชื่อผู้บันทึก", placeholder="ระบุชื่อของคุณ")
        if st.form_submit_button("บันทึกสินค้าใหม่", type="primary", use_container_width=True):
            code, name, user_new = code.strip(), name.strip(), user_new.strip()
            if code == "" or name == "" or user_new == "":
                st.warning("⚠️ กรุณากรอกข้อมูลและชื่อผู้บันทึกให้ครบถ้วน")
            elif not df.empty and code in df["รหัสสินค้า"].values:
                st.error(f"❌ รหัสสินค้า '{code}' มีในระบบแล้ว (ให้ไปบวกเพิ่มที่แท็บ '➕ เพิ่มจำนวน')")
            else:
                new_row = pd.DataFrame([{"รหัสสินค้า": code, "ชื่อสินค้า": name, "จำนวนสินค้า": int(amount)}])
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                save_history("เบิกเข้า (สินค้าใหม่)", code, name, amount, user_new)
                st.success(f"✅ เพิ่มสินค้า {code} : {name} ({amount} ชิ้น) โดย {user_new} สำเร็จ!")
                st.rerun()

with tab3:
    with st.form("add_stock_form", clear_on_submit=True):
        a_code = st.text_input("รหัสสินค้าที่ต้องการเพิ่มสต็อก", placeholder="เช่น P001")
        a_amount = st.number_input("จำนวนที่รับเข้ามาเพิ่ม", min_value=1, step=1, value=1)
        a_user = st.text_input("ชื่อผู้เบิกเข้า / ผู้บวกสต็อก", placeholder="ระบุชื่อของคุณ")
        if st.form_submit_button("ยืนยันการเพิ่มจำนวน", type="primary", use_container_width=True):
            a_code, a_user = a_code.strip(), a_user.strip()
            if a_code == "" or a_user == "":
                st.warning("⚠️ กรุณากรอกรหัสสินค้าและชื่อผู้ทำรายการให้ครบถ้วน")
            elif df.empty or a_code not in df["รหัสสินค้า"].values:
                st.error("❌ ไม่พบรหัสสินค้านี้ในระบบ")
            else:
                idx = df[df["รหัสสินค้า"] == a_code].index[0]
                p_name = df.at[idx, "ชื่อสินค้า"]
                df.at[idx, "จำนวนสินค้า"] += int(a_amount)
                new_stock = df.at[idx, "จำนวนสินค้า"]
                save_data(df)
                save_history("เบิกเข้า", a_code, p_name, a_amount, a_user)
                st.success(f"✅ บวกเพิ่ม '{p_name}' ({a_code}) อีก {a_amount} ชิ้น โดย {a_user} (รวม {new_stock} ชิ้น)")
                st.rerun()

with tab4:
    with st.form("reduce_form", clear_on_submit=True):
        r_code = st.text_input("รหัสสินค้าที่ต้องการลดจำนวน", placeholder="เช่น P001")
        r_amount = st.number_input("จำนวนที่ต้องการเบิกออก", min_value=1, step=1, value=1)
        r_user = st.text_input("ชื่อผู้เบิกออก / ผู้ตัดสต็อก", placeholder="ระบุชื่อของคุณ")
        if st.form_submit_button("ยืนยันการลดจำนวน", type="primary", use_container_width=True):
            r_code, r_user = r_code.strip(), r_user.strip()
            if r_code == "" or r_user == "":
                st.warning("⚠️ กรุณากรอกรหัสสินค้าและชื่อผู้เบิกออกให้ครบถ้วน")
            elif df.empty or r_code not in df["รหัสสินค้า"].values:
                st.error("❌ ไม่พบรหัสสินค้านี้ในระบบ")
            else:
                idx = df[df["รหัสสินค้า"] == r_code].index[0]
                p_name = df.at[idx, "ชื่อสินค้า"]
                current_stock = df.at[idx, "จำนวนสินค้า"]
                if r_amount > current_stock:
                    st.error(f"⚠️ สินค้าไม่พอให้ตัดสต็อก (เหลืออยู่แค่ {current_stock} ชิ้น)")
                else:
                    df.at[idx, "จำนวนสินค้า"] -= int(r_amount)
                    new_stock = df.at[idx, "จำนวนสินค้า"]
                    save_data(df)
                    save_history("เบิกออก", r_code, p_name, r_amount, r_user)
                    st.success(f"✅ เบิกออก '{p_name}' ({r_code}) จำนวน {r_amount} ชิ้น โดย {r_user} (คงเหลือ {new_stock} ชิ้น)")
                    st.rerun()

with tab5:
    with st.form("delete_form", clear_on_submit=True):
        st.warning("⚠️ การลบรายการสินค้าจะลบข้อมูลรหัสนี้ออกจากตารางถาวร")
        d_code = st.text_input("รหัสสินค้าที่ต้องการลบ", placeholder="เช่น P001")
        d_user = st.text_input("ชื่อผู้ลบรายการ", placeholder="ระบุชื่อของคุณ")
        if st.form_submit_button("ลบรายการสินค้านี้", type="primary", use_container_width=True):
            d_code, d_user = d_code.strip(), d_user.strip()
            if d_code == "" or d_user == "":
                st.warning("⚠️ กรุณากรอกรหัสสินค้าและชื่อผู้ลบให้ครบถ้วน")
            elif df.empty or d_code not in df["รหัสสินค้า"].values:
                st.error(f"❌ ไม่พบรหัสสินค้า '{d_code}' ในระบบ")
            else:
                target_row = df[df["รหัสสินค้า"] == d_code].iloc[0]
                p_name = target_row["ชื่อสินค้า"]
                p_amount = target_row["จำนวนสินค้า"]
                df = df[df["รหัสสินค้า"] != d_code]
                save_data(df)
                save_history("ลบรายการถาวร", d_code, p_name, p_amount, d_user)
                st.success(f"🗑️ ลบสินค้ารหัส '{d_code}' ({p_name}) โดย {d_user} เรียบร้อยแล้ว")
                st.rerun()

with tab6:
    st.subheader("📜 ประวัติการเคลื่อนไหวสต็อก")
    df_hist = load_history()
    hist_mode = st.radio(
        "เลือกประเภทประวัติที่ต้องการดู:",
        ["📥 1. ประวัติการเบิกเข้า", "📤 2. ประวัติการเบิกออก"],
        horizontal=True
    )
    search_hist = st.text_input("🔍 ค้นหาประวัติ (พิมพ์รหัสสินค้า หรือ ชื่อสินค้า)", placeholder="ปล่อยว่างเพื่อดูทั้งหมด หรือพิมพ์คำค้นหา...")
    if not df_hist.empty:
        if "เบิกเข้า" in hist_mode:
            filtered_hist = df_hist[df_hist["ประเภท"].str.contains("เบิกเข้า", na=False)]
        else:
            filtered_hist = df_hist[df_hist["ประเภท"].str.contains("เบิกออก", na=False)]
        if search_hist.strip() != "":
            q_h = search_hist.strip()
            filtered_hist = filtered_hist[
                (filtered_hist["รหัสสินค้า"].str.contains(q_h, case=False, na=False)) |
                (filtered_hist["ชื่อสินค้า"].str.contains(q_h, case=False, na=False))
            ]
        if not filtered_hist.empty:
            filtered_hist = filtered_hist.iloc[::-1]
            st.dataframe(filtered_hist, use_container_width=True, hide_index=True)
        else:
            st.info("ไม่พบข้อมูลประวัติตามเงื่อนไขที่ค้นหา")
    else:
        st.info("ยังไม่มีประวัติการทำรายการในระบบ")

with tab7:
    st.subheader("📦 สินค้าทั้งหมด")
    if not df.empty:
        st.info(f"มีรายการสินค้าทั้งหมด **{len(df)}** รายการ (รวมจำนวน **{df['จำนวนสินค้า'].sum()}** ชิ้น)")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("ยังไม่มีรายการสินค้าในระบบ")
with tab8:
    st.subheader("⚠️ สินค้าขาดแคลน (คงเหลือ ≤ 2 ชิ้น)")
    if not df.empty:
        low_stock_df = df[df["จำนวนสินค้า"] <= 2]
        if low_stock_df.empty:
            st.success("✅ ไม่มีสินค้าขาดแคลนในขณะนี้")
        else:
            st.warning(f"พบสินค้าขาดแคลนจำนวน **{len(low_stock_df)}** รายการ")
            styled_low_df = low_stock_df.style.map(highlight_low_stock, subset=["จำนวนสินค้า"])
            st.dataframe(styled_low_df, use_container_width=True, hide_index=True)
    else:
        st.info("ยังไม่มีรายการสินค้าในระบบ")
