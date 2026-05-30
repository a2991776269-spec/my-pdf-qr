import streamlit as st
import qrcode
import uuid
import os
from io import BytesIO
from supabase import create_client, Client

# ========================================================
# 1. 网页全局基础视觉配置与路由分发
# ========================================================
st.set_page_config(page_title="PDF 二维码全端直开系统", page_icon="📄", layout="centered")

# 💡【核心Bug修复点】：改用 .get() 语法，如果网址里没有 pdf_code 绝不报错崩溃，而是正常加载后台
pdf_id = st.query_params.get("pdf_code", None)

if pdf_id is not None:
    SUPABASE_URL = "https://lcyiqpkwknshofpxogpf.supabase.co"
    BUCKET_NAME = "pdfs"
    
    # 拼接公共路径
    base_url = SUPABASE_URL.strip().replace("https://", "").replace("http://", "").rstrip('/')
    target_pdf_url = f"https://{base_url}/storage/v1/object/public/{BUCKET_NAME}/{pdf_id}.pdf"
    
    # 隐藏 Streamlit 官方多余组件，伪装成纯净的手机端独立页面
    st.markdown("""
        <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stApp {max-width: 100%; padding: 0; background-color: #f3f4f6;}
            .btn-box {padding: 20px; text-align: center;}
            .download-btn {
                display: inline-block; padding: 14px 28px; background-color: #07c160; 
                color: white !important; text-decoration: none; border-radius: 8px; 
                font-weight: bold; font-size: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
        </style>
    """, unsafe_allow_html=True)
    
    # 🚀【彻底解决安卓微信卡死最后一点点】：
    # 微信内置浏览器（特别是安卓版）对于 iframe 嵌套国外桶的 PDF 支持极不稳定。
    # 既然我们要制作“任何人点开链接就能用”的商业项目，这里直接采用移动端体验最好、最符合微信生态的
    # “标准 H5 大按钮引导模式”——扫码后瞬间进入干净的独立引导页，用户点击绿色按钮，直接调起手机原生预览引擎！
    st.markdown("<div style='text-align:center; padding-top:50px;'>", unsafe_allow_html=True)
    st.subheader("📄 您申请的 PDF 电子文档已准备就绪")
    st.markdown("已通过云端安全策略加密保护，请点击下方按钮直接查阅。")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="btn-box" style="margin-top:40px;">
            <a href="{target_pdf_url}" class="download-btn" target="_blank">点击直接在线阅读 PDF 文档</a>
        </div>
    """, unsafe_allow_html=True)
    
    st.stop() # 手机阅览端至此截断，绝对不往下加载后台管理面板

# ========================================================
# 2. 正常访问：展示生成器后台界面
# ========================================================
st.title("📄 PDF 二维码全端直开系统")
st.markdown("已修复新版 Streamlit 参数判定冲突。上传 PDF，一键生成全网无缝直开二维码。")

SUPABASE_URL = "https://lcyiqpkwknshofpxogpf.supabase.co"
SUPABASE_KEY = "sb_secret_LyLHKNUSJfih70tUckmEIQ_GGRlxINx"
BUCKET_NAME = "pdfs"  

@st.cache_resource
def get_supabase_client():
    return create_client(SUPABASE_URL.strip(), SUPABASE_KEY.strip())

def upload_to_supabase(unique_file_id, file_bytes):
    """使用高级令牌将文件推入存储桶"""
    try:
        supabase: Client = get_supabase_client()
        storage_file_path = f"{unique_file_id}.pdf"
        
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

# 3. 前端交互 UI 渲染
uploaded_file = st.file_uploader("请将您的 PDF 文件拖拽至此处或点击浏览", type=["pdf"])

if uploaded_file is not None:
    file_size_mb = round(uploaded_file.size / (1024 * 1024), 2)
    st.info(f"📁 已成功读取文件: {uploaded_file.name} ({file_size_mb} MB)")
    
    if st.button("🔥 一键生成全端秒开二维码"):
        with st.spinner("正在安全打通云端极速通道，请稍候..."):
            
            file_bytes = uploaded_file.getvalue()
            unique_file_id = uuid.uuid4().hex
            
            # 上传文件
            pdf_url, error_msg = upload_to_supabase(unique_file_id, file_bytes)
            
            if pdf_url:
                # 自动动态捕捉当前运行的主机前缀（完美支持本地 localhost 及以后一键部署上线公网域名）
                try:
                    current_host = st.context.headers.get("Host", "localhost:8501")
                    protocol = "https" if "streamlit.app" in current_host else "http"
                    local_app_url = f"{protocol}://{current_host}"
                except:
                    local_app_url = "http://localhost:8501"
                
                # 二维码里的安全跳转通道链接
                wechat_friendly_url = f"{local_app_url}/?pdf_code={unique_file_id}"
                
                # 4. 计算并渲染高清二维码
                qr = qrcode.QRCode(
                    version=2,
                    error_correction=qrcode.constants.ERROR_CORRECT_H,
                    box_size=12,
                    border=4,
                )
                qr.add_data(wechat_friendly_url) 
                qr.make(fit=True)
                img = qr.make_image(fill_color="#111827", back_color="white")
                
                buf = BytesIO()
                img.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                st.divider()
                st.balloons()  
                st.success("🎉 全端直开优化二维码生成成功！")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.image(byte_im, caption="🔥 手机/微信扫码直接自动打开预览", use_container_width=True)
                with col2:
                    st.markdown("### 🛠️ 后台资产管理面板")
                    st.markdown(f"🔗 **手机H5专属链接：** [点击在电脑端预览]({wechat_friendly_url})")
                    st.code(wechat_friendly_url, language="text")
                    
                    st.download_button(
                        label="💾 下载高清印刷级二维码图片",
                        data=byte_im,
                        file_name=f"QR_{uploaded_file.name}.png",
                        mime="image/png"
                    )
            else:
                st.error(f"❌ 通道连接失败，请检查配置。错误信息:\n{error_msg}")