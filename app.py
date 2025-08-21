import streamlit as st
import pandas as pd
import re
from scholarly import scholarly
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from dotenv import load_dotenv
import os
import requests

# --- Load API keys from .env ---
load_dotenv()
SCOPUS_API_KEY = os.getenv("SCOPUS_API_KEY")

st.set_page_config(page_title="Profiling Dosen - Scholar, Sinta & Scopus", layout="wide")
st.title("📚 Profiling Dosen (Google Scholar + Sinta + Scopus)")

# --- Input Identitas Dosen ---
scholar_url = st.text_input("Masukkan URL Google Scholar:",
                            "https://scholar.google.com/citations?hl=id&user=fzCJZDAAAAAJ")
sinta_id = st.text_input("Masukkan Sinta ID (opsional):", "6758820")
scopus_id = st.text_input("Masukkan Scopus ID (opsional):", "")

# =========================
# List mata kuliah per prodi
# =========================
courses_TI = ["Algoritma dan Pemrograman","Aljabar Linier dan Matriks","Analisis dan Perancangan Sistem Informasi",
              "Arsitektur Berbasis Layanan","Arsitektur Enterprise","Bahasa Pemrograman","Basis Data","Big Data",
              "Cyber Security","Dasar Sistem Informasi","Data Mining","Data Warehouse","Desain dan Analisis Algoritma",
              "Game Development","Interaksi Manusia Komputer","Internet of Things","Isu Sosial dan Keprofesian Teknologi Informasi",
              "Jaringan Komputer","Jaringan Komputer Lanjut","Jaringan Mobile","Kalkulus 1","Kalkulus 2",
              "Kapita Selekta Informatika","Keamanan Informasi","Kecerdasan Artifisial","Kriptografi","Machine Learning",
              "Manajemen Proyek Perangkat Lunak","Matematika Diskrit","Metodologi Penelitian","Mobile Application and Technology",
              "Organisasi dan Arsitektur Komputer","Organisasi dan Manajemen","Pemrograman Berorientasi Objek",
              "Pemrograman Mobile","Pemrograman Web","Pendidikan Agama","Pengembangan Perangkat Lunak","Pengolahan Citra",
              "Perancangan Aplikasi Mobile","Rekayasa Perangkat Lunak","Sistem Basis Data Terdistribusi","Sistem Operasi",
              "Software Quality Assurance","Statistik","Struktur Data"]

courses_SI = ["Analisis Kebutuhan Informasi","Analisis Resiko Sistem Informasi","Arsitektur Enterprise",
              "Audit dan Kendali Sistem Informasi","Big Data","Dasar Sistem Informasi","Data Mining","Data Warehouse",
              "E-Bisnis","Evaluasi Sistem Informasi","Implementasi Sistem Informasi","Infrastruktur dan Manajemen Layanan TI",
              "Integrasi dan Kustomisasi ERP","Intelegensia Bisnis","Interaksi Manusia Komputer","Internet of Things",
              "Isu Sosial dan Keprofesian Sistem Informasi","IT untuk Pemulihan Bencana","Jaminan dan Keamanan Informasi",
              "Kapita Selekta Sistem Informasi","Manajemen Pengetahuan","Manajemen Proyek Sistem Informasi",
              "Manajemen Sumber Daya Informasi","Masyarakat Virtual","Metode Sampling dan Survei SI","Metodologi Penelitian",
              "Pemodelan Proses Bisnis","Rekayasa Layanan","Rekayasa Perangkat Lunak","Sistem Informasi Enterprise"]

courses_S2 = ["Manajemen Informasi","Metodologi Penelitian","Rekayasa Perangkat Lunak","Topik dalam Artificial Inteligence",
              "Topik dalam Business Intelligence","Topik dalam Data Mining","Topik dalam Enterprise Architecture",
              "Topik dalam Enterprise Information System","Topik dalam Image Processing","Topik dalam Information Retrieval",
              "Topik dalam IT Governance","Topik dalam Knowledge Governance","Topik dalam Mobile Application",
              "Topik dalam Risk Management","Topik dalam Wireless dan Mobile Technology","Topik dalam Pemrograman"]

# Pilih Prodi
prodi = st.selectbox("Pilih Program Studi", ["Teknik Informatika", "Sistem Informasi", "Magister"])
if prodi == "Teknik Informatika":
    courses = courses_TI
elif prodi == "Sistem Informasi":
    courses = courses_SI
else:
    courses = courses_S2

# --- Button proses ---
if st.button("🔍 Proses Profiling"):
    match = re.search(r"user=([a-zA-Z0-9_-]+)", scholar_url)
    if match:
        user_id = match.group(1)
        try:
            # ===== Google Scholar =====
            author = scholarly.search_author_id(user_id)
            author = scholarly.fill(author, sections=["basics", "indices", "counts", "publications"])

            st.subheader(author["name"])
            st.write(f"🏫 {author.get('affiliation','-')}")
            st.write(f"📊 h-index: {author['hindex']} | i10-index: {author['i10index']}")
            st.write(f"🌐 Bidang: {', '.join(author.get('interests', []))}")

            competency_text = " ".join(author.get("interests", []))
            for pub in author["publications"][:20]:
                try:
                    pub_filled = scholarly.fill(pub)
                    competency_text += " " + pub_filled['bib'].get('title', "")
                except:
                    pass

            # ===== SINTA =====
            if sinta_id:
                sinta_url = f"https://sinta.kemdikbud.go.id/authors/profile/{sinta_id}"
                st.info(f"🔗 Profil SINTA: [Klik di sini]({sinta_url})")

            # ===== Scopus =====
            if scopus_id and SCOPUS_API_KEY:
                scopus_url = f"https://api.elsevier.com/content/author/author_id/{scopus_id}?apiKey={SCOPUS_API_KEY}"
                r = requests.get(scopus_url, headers={"Accept": "application/json"})
                if r.status_code == 200:
                    data = r.json()
                    st.success("✅ Data Scopus berhasil diambil")
                    st.json(data)  # sementara tampilkan mentah
                else:
                    st.error("❌ Gagal ambil data Scopus")

            # ===== Mapping ke Mata Kuliah =====
            corpus = [competency_text] + courses
            vectorizer = TfidfVectorizer().fit_transform(corpus)
            similarity_matrix = cosine_similarity(vectorizer)

            results = []
            for i, course in enumerate(courses):
                score = similarity_matrix[0, i+1]
                if score > 0:
                    results.append({"Mata Kuliah": course, "Kesesuaian (%)": round(score*100, 2)})

            df_results = pd.DataFrame(results).sort_values("Kesesuaian (%)", ascending=False)

            st.markdown("### 🧑‍🏫 Pemetaan Kompetensi Dosen ke Mata Kuliah")
            st.dataframe(df_results)

            # --- Export PDF ---
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer)
            styles = getSampleStyleSheet()
            elements = []

            elements.append(Paragraph(f"Profil Dosen: {author['name']}", styles['Title']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Afiliasi: {author.get('affiliation','-')}", styles['Normal']))
            elements.append(Paragraph(f"h-index: {author['hindex']} | i10-index: {author['i10index']}", styles['Normal']))
            elements.append(Spacer(1, 12))

            if not df_results.empty:
                table_data = [["Mata Kuliah", "Kesesuaian (%)"]] + df_results.values.tolist()
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (-1,0), colors.grey),
                    ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
                    ("ALIGN", (0,0), (-1,-1), "CENTER"),
                    ("GRID", (0,0), (-1,-1), 1, colors.black),
                ]))
                elements.append(table)

            doc.build(elements)
            pdf = buffer.getvalue()
            buffer.close()

            st.download_button("⬇️ Download PDF", data=pdf, file_name="profil_dosen.pdf", mime="application/pdf")

        except Exception as e:
            st.error(f"Gagal mengambil data Google Scholar: {e}")
