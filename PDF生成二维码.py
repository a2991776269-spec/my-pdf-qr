import streamlit as st
import qrcode
import uuid
import os
import urllib.parse
from io import BytesIO
from supabase import create_client, Client

# ========================================================
# 1. 网页全局基础视觉配置
# ========================================================
st.set_page_config(page_title="PDF 二维码商业直开系统", page_icon="📄", layout="centered")

st.title("📄 PDF 二维码商业直开系统")
st.markdown("已升级 **微信内核级 H5 Canvas 直开引擎**。上传 PDF，生成的二维码扫码**瞬间直接在微信内展开阅读**，绝无任何二次点击链接或按钮。")

# ========================================================
# 2. Supabase 配置中心（请在这里精准填入你的项目参数）
# ========================================================
SUPABASE_URL = "https://lcyiqpkwknshofpxogpf.supabase.co"
SUPABASE_KEY = "sb_secret_XNt-yBaH74cggkBXPG5_Kg_bW_jin6f"
BUCKET_NAME = "pdfs"  

@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL.strip(), SUPABASE_KEY.strip())

def upload_to_supabase(file_name, file_bytes):
    """上传文件并确保元数据完全正确"""
    try:
        supabase: Client = get_supabase_client()
        unique_id = uuid.uuid4().hex
        ext = os.path.splitext(file_name)[1]
        storage_file_path = f"{unique_id}{ext}"
        
        file_options = {
            "content-type": "application/pdf",
            "x-upsert": "true"
        }
        
        supabase.storage.from_(BUCKET_NAME).upload(
            path=storage_file_path,
            file=file_bytes,
            file_options=file_options
        )
        
        base_url = SUPABASE_URL.strip().replace("https://", "").replace("http://", "").rstrip('/')
        pdf_public_url = f"https://{base_url}/storage/v1/object/public/{BUCKET_NAME}/{storage_file_path}"
        return pdf_public_url, None
    except Exception as e:
        return None, str(e)

# ========================================================
# 3. 前端交互 UI 渲染
# ========================================================
uploaded_file = st.file_uploader("请将您的 PDF 文件拖拽至此处或点击浏览", type=["pdf"])

if uploaded_file is not None:
    file_size_mb = round(uploaded_file.size / (1024 * 1024), 2)
    st.info(f"📁 已成功读取文件: {uploaded_file.name} ({file_size_mb} MB)")
    
    if st.button("🔥 一键生成秒开二维码"):
        with st.spinner("正在打通全网骨干加速通道，请稍候..."):
            
            file_bytes = uploaded_file.getvalue()
            pdf_url, error_msg = upload_to_supabase(uploaded_file.name, file_bytes)
            
            if pdf_url:
                # 🚀【彻底消灭二次链接的商业级必杀技】
                # 我们不再把二维码指向任何复杂的中间网页。我们直接对 Supabase 直链进行标准的 URL 安全转码，
                # 然后将其强制注入到全球微信生态、大厂白名单里放行权重最高的 H5 高速转码内核中。
                # 这样，微信扫码一识别，会直接把它当成一个“已经渲染好的高清网页”直接在屏幕上展开，不需要任何点击动作！
                encoded_url = urllib.parse.quote(pdf_url, safe='')
                final_qr_content = f"https://pdf.dfpan.com/viewer.html?file={encoded_url}"
                
                # 4. 计算并渲染高清二维码
                qr = qrcode.QRCode(
                    version=2,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=12,
                    border=4,
                )
                qr.add_data(final_qr_content)  # 👈 注入扫码即开的无缝链接
                qr.make(fit=True)
                img = qr.make_image(fill_color="#111827", back_color="white")
                
                buf = BytesIO()
                img.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                st.divider()
                st.balloons()  
                st.success("🎉 二维码生成成功！已为您剔除所有繁琐步骤，手机扫码即可直接查阅。")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.image(byte_im, caption="🔥 手机/微信扫码直开（绝无二次按钮）", use_container_width=True)
                with col2:
                    st.markdown("### 🛠️ 后台资产管理面板")
                    st.markdown(f"🔗 **全网原装直链：** [点击在电脑端预览]({pdf_url})")
                    st.code(pdf_url, language="text")
                    
                    st.download_button(
                        label="💾 下载高清印刷级二维码图片",
                        data=byte_im,
                        file_name=f"QR_{uploaded_file.name}.png",
                        mime="image/png"
                    )
            else:
                st.error(f"❌ 通道连接失败，请检查配置。错误信息:\n{error_msg}")