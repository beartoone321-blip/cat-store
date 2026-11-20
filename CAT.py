import sqlite3 as sql
import streamlit as st
import pandas as pd

# ==========================================
# ส่วนที่ 1: คลาสจัดการฐานข้อมูล (หลังบ้าน)
# ==========================================
class STORE:
    def __init__(self):
        self.conn = sql.connect("store.db", check_same_thread=False)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS products(
            รหัสสินค้า TEXT PRIMARY KEY,
            ชื่อสินค้า TEXT,
            จำนวนสินค้า INTEGER)""")

    def CheckProduct(self, code):
        self.cursor.execute("SELECT 1 FROM products WHERE รหัสสินค้า = ?", (code,))
        result = self.cursor.fetchone()
        return result is not None

    # 1. เพิ่มสินค้าใหม่ครั้งแรก
    def AddNewProduct(self, code, name, amount):
        if self.CheckProduct(code):
            print("มีรายการสินค้าอยู่ในระบบ")
        else:
            self.cursor.execute("INSERT INTO products VALUES(?, ?, ?)", (code, name, amount))
            self.conn.commit()

    # 2. บวกเพิ่มจำนวนสินค้าเดิม
    def AddStock(self, code, amount):
        self.cursor.execute("SELECT จำนวนสินค้า FROM products WHERE รหัสสินค้า = ?", (code,))
        result = self.cursor.fetchone()
        
        if result is None:
            return False, "❌ ไม่พบรหัสสินค้านี้ในระบบ (หากเป็นสินค้าใหม่ ให้เพิ่มที่แท็บ '🆕 สินค้าใหม่')"
            
        current_stock = result[0]
        new_stock = current_stock + amount
        self.cursor.execute("UPDATE products SET จำนวนสินค้า = ? WHERE รหัสสินค้า = ?", (new_stock, code))
        self.conn.commit()
        return True, f"✅ บวกเพิ่มสต็อกรหัส '{code}' อีก {amount} ชิ้น (รวมเป็น {new_stock} ชิ้น)"

    # 3. ลดจำนวนสินค้า
    def ReduceStock(self, code, amount):
        self.cursor.execute("SELECT จำนวนสินค้า FROM products WHERE รหัสสินค้า = ?", (code,))
        result = self.cursor.fetchone()
        
        if result is None:
            return False, "❌ ไม่พบรหัสสินค้านี้ในระบบ"
            
        current_stock = result[0]
        if amount > current_stock:
            return False, f"⚠️ สินค้าไม่พอให้ตัดสต็อก (เหลืออยู่แค่ {current_stock} ชิ้น)"
            
        new_stock = current_stock - amount
        self.cursor.execute("UPDATE products SET จำนวนสินค้า = ? WHERE รหัสสินค้า = ?", (new_stock, code))
        self.conn.commit()
        return True, f"✅ ตัดสต็อกรหัส '{code}' ออก {amount} ชิ้น (คงเหลือ {new_stock} ชิ้น)"

    # 4. ลบรายการสินค้าออกจากฐานข้อมูล
    def DeleteProduct(self, code):
        if not self.CheckProduct(code):
            return False, f"❌ ไม่พบรหัสสินค้า '{code}' ในระบบ"
        else:
            self.cursor.execute("DELETE FROM products WHERE รหัสสินค้า = ?", (code,))
            self.conn.commit()
            return True, f"🗑️ ลบรายการสินค้ารหัส '{code}' ออกจากระบบเรียบร้อยแล้ว"

    # 5. ค้นหาข้อมูลสินค้าตามรหัส
    def GetProductInfo(self, code):
        self.cursor.execute("SELECT ชื่อสินค้า, จำนวนสินค้า FROM products WHERE รหัสสินค้า = ?", (code,))
        return self.cursor.fetchone()

# ==========================================
# ส่วนที่ 2: หน้าต่างคุยกับผู้ใช้งาน (5 แท็บเมนู)
# ==========================================
st.set_page_config(page_title="CAT STOCK", page_icon="📦", layout="centered")
m = STORE()

st.title("📦 CAT STOCK")
st.caption("ระบบจัดการสต็อกสินค้าครบวงจร")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 ค้นหาสินค้า",
    "🆕 สินค้าใหม่", 
    "➕ เพิ่มจำนวน", 
    "➖ ลดจำนวน", 
    "🗑️ ลบรายการ"
])

# แท็บที่ 1: ค้นหาข้อมูลสินค้าตามรหัส
with tab1:
    with st.form("search_form"):
        s_code = st.text_input("ใส่รหัสสินค้าที่ต้องการตรวจสอบ", placeholder="เช่น P001")
        submit_search = st.form_submit_button("ค้นหาข้อมูล", type="primary", use_container_width=True)

        if submit_search:
            if s_code.strip() == "":
                st.warning("⚠️ กรุณากรอกรหัสสินค้า")
            else:
                info = m.GetProductInfo(s_code)
                if info is not None:
                    p_name, p_amount = info
                    st.success(f"✅ พบข้อมูลรหัสสินค้า: **{s_code}**")
                    col1, col2 = st.columns(2)
                    col1.metric("ชื่อสินค้า", p_name)
                    col2.metric("จำนวนคงเหลือ", f"{p_amount} ชิ้น")
                else:
                    st.error(f"❌ ไม่พบรหัสสินค้า '{s_code}' ในระบบ")

# แท็บที่ 2: เพิ่มสินค้าใหม่ครั้งแรก
with tab2:
    with st.form("add_new_form", clear_on_submit=True):
        code = st.text_input("รหัสสินค้า", placeholder="เช่น P001")
        name = st.text_input("ชื่อสินค้า", placeholder="เช่น อาหารแมว 1kg")
        amount = st.number_input("จำนวนสินค้าเริ่มต้น", min_value=1, step=1, value=1)
        submit_add = st.form_submit_button("บันทึกสินค้าใหม่", type="primary", use_container_width=True)

        if submit_add:
            if code.strip() == "" or name.strip() == "":
                st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน")
            elif m.CheckProduct(code):
                st.error(f"❌ รหัสสินค้า '{code}' มีในระบบแล้ว (ให้ไปบวกเพิ่มที่แท็บ '➕ เพิ่มจำนวน')")
            else:
                m.AddNewProduct(code, name, amount)
                st.success(f"✅ เพิ่มสินค้า {code} : {name} ({amount} ชิ้น) สำเร็จ!")

# แท็บที่ 3: บวกเพิ่มจำนวนสินค้าเดิม
with tab3:
    with st.form("add_stock_form", clear_on_submit=True):
        a_code = st.text_input("รหัสสินค้าที่ต้องการเพิ่มสต็อก", placeholder="เช่น P001")
        a_amount = st.number_input("จำนวนที่รับเข้ามาเพิ่ม", min_value=1, step=1, value=1)
        submit_plus = st.form_submit_button("ยืนยันการเพิ่มจำนวน", type="primary", use_container_width=True)

        if submit_plus:
            if a_code.strip() == "":
                st.warning("⚠️ กรุณากรอกรหัสสินค้า")
            else:
                success, msg = m.AddStock(a_code, a_amount)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

# แท็บที่ 4: ลดจำนวนสินค้า
with tab4:
    with st.form("reduce_form", clear_on_submit=True):
        r_code = st.text_input("รหัสสินค้าที่ต้องการลดจำนวน", placeholder="เช่น P001")
        r_amount = st.number_input("จำนวนที่ต้องการลบออก", min_value=1, step=1, value=1)
        submit_reduce = st.form_submit_button("ยืนยันการลดจำนวน", type="primary", use_container_width=True)

        if submit_reduce:
            if r_code.strip() == "":
                st.warning("⚠️ กรุณากรอกรหัสสินค้า")
            else:
                success, msg = m.ReduceStock(r_code, r_amount)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

# แท็บที่ 5: ลบรายการสินค้าออกจากระบบ
with tab5:
    with st.form("delete_form", clear_on_submit=True):
        st.warning("⚠️ การลบรายการสินค้าจะลบข้อมูลรหัสนี้ออกจากตารางถาวร")
        d_code = st.text_input("รหัสสินค้าที่ต้องการลบ", placeholder="เช่น P001")
        submit_delete = st.form_submit_button("ลบรายการสินค้านี้", type="primary", use_container_width=True)

        if submit_delete:
            if d_code.strip() == "":
                st.warning("⚠️ กรุณากรอกรหัสสินค้าที่ต้องการลบ")
            else:
                success, msg = m.DeleteProduct(d_code)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

# ==========================================
# ส่วนที่ 3: ตารางแสดงรายการสินค้าทั้งหมด และ สินค้าขาดแคลน
# ==========================================
st.divider()

# ดึงข้อมูลทั้งหมดจากฐานข้อมูล
df = pd.read_sql_query("SELECT * FROM products", m.conn)

# ฟังก์ชันสำหรับกำหนดสีตัวอักษร (ถ้า <= 2 ให้เป็นสีแดงตัวหนา)
def highlight_low_stock(val):
    if val <= 2:
        return 'color: #FF4B4B; font-weight: bold;'
    return ''

# --- หัวข้อใหม่: รายการสินค้าขาดแคลน ---
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

# --- หัวข้อเดิม: รายการสินค้าทั้งหมด ---
st.subheader("📋 รายการสินค้าทั้งหมดในระบบ")

if df.empty:
    st.info("ยังไม่มีรายการสินค้าในระบบ")
else:
    styled_all_df = df.style.map(highlight_low_stock, subset=["จำนวนสินค้า"])
    st.dataframe(styled_all_df, use_container_width=True, hide_index=True)
