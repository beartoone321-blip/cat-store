import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="CAT STOCK", page_icon="📦", layout="centered")

# URL เว็บแอปจาก Google Apps Script ของคุณ
WEB_APP_URL = "https://google.com"

def load_data():
    res = requests.get(WEB_APP_URL)
    data = res.json()
    if len(data) <= 1:
        return pd.DataFrame(columns=["รหัสสินค้า", "ชื่อสินค้า", "จำนวนสินค้า"])
    df = pd.DataFrame(data[1:], columns=data[0])
    df["รหัสสินค้า"] = df["รหัสสินค้า"].astype(str)
    df["จำนวนสินค้า"] = pd.to_numeric(df["จำนวนสินค้า"], errors="coerce").fillna(0).astype(int)
    return df

def save_data(df):
    rows = [df.columns.tolist()] + df.values.tolist()
    requests.post(WEB_APP_URL, json=rows)

st.title("📦 CAT STOCK")
st.caption("ระบบจัดการสต็อกสินค้าครบวงจร")

df = load_data()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 ค้นหาสินค้า",
    "🆕 สินค้าใหม่", 
    "➕ เพิ่มจำนวน", 
    "➖ ลดจำนวน", 
    "🗑️ ลบรายการ"
])

with tab1:
    with st.form("search_form"):
        s_code = st.text_input("ใส่รหัสสินค้าที่ต้องการตรวจสอบ", placeholder="เช่น P001")
        if st.form_submit_button("ค้นหาข้อมูล", type="primary", use_container_width=True):
            if s_code.strip() == "":
                st.warning("⚠️ กรุณากรอกรหัสสินค้า")
            else:
                result = df[df["รหัสสินค้า"] == s_code.strip()]
                if not result.empty:
                    p_name = result.iloc[0]["ชื่อสินค้า"]
                    p_amount = result.iloc[0]["จำนวนสินค้า"]
                    st.success(f"✅ พบข้อมูลรหัสสินค้า: **{s_code}**")
                    col1, col2 = st.columns(2)
                    col1.metric("ชื่อสินค้า", p_name)
                    col2.metric("จำนวนคงเหลือ", f"{p_amount} ชิ้น")
                else:
                    st.error(f"❌ ไม่พบรหัสสินค้า '{s_code}' ในระบบ")

with tab2:
    with st.form("add_new_form", clear_on_submit=True):
        code = st.text_input("รหัสสินค้า", placeholder="เช่น P001")
        name = st.text_input("ชื่อสินค้า", placeholder="เช่น อาหารแมว 1kg")
        amount = st.number_input("จำนวนสินค้าเริ่มต้น", min_value=1, step=1, value=1)
        if st.form_submit_button("บันทึกสินค้าใหม่", type="primary", use_container_width=True):
            code = code.strip()
            name = name.strip()
            if code == "" or name == "":
                st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน")
            elif not df.empty and code in df["รหัสสินค้า"].values:
                st.error(f"❌ รหัสสินค้า '{code}' มีในระบบแล้ว (ให้ไปบวกเพิ่มที่แท็บ '➕ เพิ่มจำนวน')")
            else:
                new_row = pd.DataFrame([{"รหัสสินค้า": code, "ชื่อสินค้า": name, "จำนวนสินค้า": int(amount)}])
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                st.success(f"✅ เพิ่มสินค้า {code} : {name} ({amount} ชิ้น) สำเร็จ!")
                st.rerun()

with tab3:
    with st.form("add_stock_form", clear_on_submit=True):
        a_code = st.text_input("รหัสสินค้าที่ต้องการเพิ่มสต็อก", placeholder="เช่น P001")
        a_amount = st.number_input("จำนวนที่รับเข้ามาเพิ่ม", min_value=1, step=1, value=1)
        if st.form_submit_button("ยืนยันการเพิ่มจำนวน", type="primary", use_container_width=True):
            a_code = a_code.strip()
            if a_code == "":
                st.warning("⚠️ กรุณากรอกรหัสสินค้า")
            elif df.empty or a_code not in df["รหัสสินค้า"].values:
                st.error("❌ ไม่พบรหัสสินค้านี้ในระบบ")
            else:
                idx = df[df["รหัสสินค้า"] == a_code].index[0]
                df.at[idx, "จำนวนสินค้า"] += int(a_amount)
                new_stock = df.at[idx, "จำนวนสินค้า"]
                save_data(df)
                st.success(f"✅ บวกเพิ่มสต็อกรหัส '{a_code}' อีก {a_amount} ชิ้น (รวมเป็น {new_stock} ชิ้น)")
                st.rerun()

with tab4:
    with st.form("reduce_form", clear_on_submit=True):
        r_code = st.text_input("รหัสสินค้าที่ต้องการลดจำนวน", placeholder="เช่น P001")
        r_amount = st.number_input("จำนวนที่ต้องการลบออก", min_value=1, step=1, value=1)
        if st.form_submit_button("ยืนยันการลดจำนวน", type="primary", use_container_width=True):
            r_code = r_code.strip()
            if r_code == "":
                st.warning("⚠️ กรุณากรอกรหัสสินค้า")
            elif df.empty or r_code not in df["รหัสสินค้า"].values:
                st.error("❌ ไม่พบรหัสสินค้านี้ในระบบ")
            else:
                idx = df[df["รหัสสินค้า"] == r_code].index[0]
                current_stock = df.at[idx, "จำนวนสินค้า"]
                if r_amount > current_stock:
                    st.error(f"⚠️ สินค้าไม่พอให้ตัดสต็อก (เหลืออยู่แค่ {current_stock} ชิ้น)")
                else:
                    df.at[idx, "จำนวนสินค้า"] -= int(r_amount)
                    new_stock = df.at[idx, "จำนวนสินค้า"]
                    save_data(df)
                    st.success(f"✅ ตัดสต็อกรหัส '{r_code}' ออก {r_amount} ชิ้น (คงเหลือ {new_stock} ชิ้น)")
                    st.rerun()

with tab5:
    with st.form("delete_form", clear_on_submit=True):
        st.warning("⚠️ การลบรายการสินค้าจะลบข้อมูลรหัสนี้ออกจากตารางถาวร")
        d_code = st.text_input("รหัสสินค้าที่ต้องการลบ", placeholder="เช่น P001")
        if st.form_submit_button("ลบรายการสินค้านี้", type="primary", use_container_width=True):
            d_code = d_code.strip()
            if d_code == "":
                st.warning("⚠️ กรุณากรอกรหัสสินค้าที่ต้องการลบ")
            elif df.empty or d_code not in df["รหัสสินค้า"].values:
                st.error(f"❌ ไม่พบรหัสสินค้า '{d_code}' ในระบบ")
            else:
                df = df[df["รหัสสินค้า"] != d_code]
                save_data(df)
                st.success(f"🗑️ ลบรายการสินค้ารหัส '{d_code}' ออกจากระบบเรียบร้อยแล้ว")
                st.rerun()

st.divider()

def highlight_low_stock(val):
    if val <= 2:
        return 'color: #FF4B4B; font-weight: bold;'
    return ''

st.subheader("⚠️ สินค้าขาดแคลน (คงเหลือ ≤ 2 ชิ้น)")
if not df.empty:
    low_stock_df = df[df["จำนวนสินค้า"] <= 2]
    if low_stock_df.empty:
        st.success("✅ ไม่มีสินค้าขาดแคลนในขณะนี้")
    else:
        styled_low_df = low_stock_df.style.map(highlight_low_stock, subset=["จำนวนสินค้า"])
        st.dataframe(styled_low_df, use_container_width=True, hide_index=True)
else:
    st.info("ยังไม่มีรายการสินค้าในระบบ")

st.divider()

st.subheader("📋 รายการสินค้าทั้งหมดในระบบ")
if df.empty:
    st.info("ยังไม่มีรายการสินค้าในระบบ")
else:
    styled_all_df = df.style.map(highlight_low_stock, subset=["จำนวนสินค้า"])
    st.dataframe(styled_all_df, use_container_width=True, hide_index=True)
