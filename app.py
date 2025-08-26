import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from scholarly import scholarly
import requests
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import textwrap
import json

st.set_page_config(page_title="Profiling Dosen Fasilkom Esa Unggul", layout="wide")
st.title("📚 Profiling Dosen Fasilkom Esa Unggul")

# ================= SQLite =================
conn = sqlite3.connect("profil_dosen.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS profil_dosen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    prodi TEXT,
    scholar_id TEXT,
    sim_url TEXT,
    h_index INTEGER,
    i10_index INTEGER,
    bidang_keilmuan TEXT,
    rekomendasi_mk TEXT
)
""")
conn.commit()

# ================= Helper Functions =================
def slugify(text):
    return text.lower().replace(" ", "_")

def wrap_text(text, width=50):
    if not text:
        return ""
    return "\n".join(textwrap.wrap(str(text), width=width))

def generate_pdf(name, prodi, author, df_fields, df_results):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(595,842), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    styles = getSampleStyleSheet()
    elements = []

    # Judul
    elements.append(Paragraph(f"Profil Dosen: {author.get('name','-')}", styles['Title']))
    elements.append(Spacer(1,12))
    elements.append(Paragraph(f"Afiliasi: {author.get('affiliation','-')}", styles['Normal']))
    elements.append(Paragraph(f"h-index: {author.get('hindex','-')} | i10-index: {author.get('i10index','-')}", styles['Normal']))
    elements.append(Spacer(1,12))

    # Bidang Keilmuan
    elements.append(Paragraph("Bidang Keilmuan", styles['Heading2']))
    field_table_data = [["Bidang Ilmu", "Kesesuaian (%)"]]
    for r in df_fields.itertuples(index=False):
        field_table_data.append([wrap_text(r[0],30), str(r[1])])
    field_table = Table(field_table_data, colWidths=[200,100], repeatRows=1)
    field_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("GRID", (0,0), (-1,-1), 1, colors.black)
    ]))
    elements.append(field_table)
    elements.append(Spacer(1,12))

    # Mata Kuliah
    elements.append(Paragraph("Rekomendasi Mata Kuliah", styles['Heading2']))
    table_data = [["Mata Kuliah", "Kesesuaian(%)", "Publikasi Relevan", "Pernah Diajar"]]
    for r in df_results.itertuples(index=False):
        table_data.append([
            wrap_text(r[0], 30),
            str(r[1]),
            wrap_text(r[2], 50),
            r[3]
        ])
    table = Table(table_data, colWidths=[150, 80, 300, 70], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("GRID", (0,0), (-1,-1), 1, colors.black)
    ]))
    elements.append(table)

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


# ================= Load Existing Data =================
st.subheader("📋 Data Dosen yang Sudah Terproses")
df_existing = pd.read_sql("SELECT * FROM profil_dosen", conn)

if not df_existing.empty:
    # 🔎 Search dosen
    search_query = st.text_input("Cari dosen berdasarkan nama:")

    # 🎓 Filter per prodi
    prodi_list = ["Semua"] + sorted(df_existing["prodi"].dropna().unique().tolist())
    selected_prodi = st.selectbox("Filter berdasarkan Prodi:", prodi_list)

    # 🔍 Apply filter
    df_filtered = df_existing.copy()
    if search_query:
        df_filtered = df_filtered[df_filtered["name"].str.contains(search_query, case=False, na=False)]
    if selected_prodi != "Semua":
        df_filtered = df_filtered[df_filtered["prodi"] == selected_prodi]

    # Tabel ringkas
    st.dataframe(df_filtered[["name","prodi","scholar_id","h_index","i10_index"]])

    to_delete = None
    # 🔽 Detail per dosen dalam collapse (expander)
    for idx, row in df_filtered.iterrows():
        with st.expander(f"👤 {row['name']} - {row['prodi']}"):
            bidang_df = pd.DataFrame(json.loads(row['bidang_keilmuan']))
            mk_df = pd.DataFrame(json.loads(row['rekomendasi_mk']))

            st.markdown("**🔬 Bidang Keilmuan (Top 5)**")
            st.table(bidang_df.head(5))

            st.markdown("**🧑‍🏫 Rekomendasi Mata Kuliah**")
            st.dataframe(mk_df)

            author_data = {
                "name": row['name'],
                "affiliation": "-",
                "hindex": row['h_index'],
                "i10index": row['i10_index']
            }
            pdf_bytes = generate_pdf(row['name'], row['prodi'], author_data, bidang_df, mk_df)
            
            st.download_button(
                f"⬇️ Download PDF {row['name']}",
                    data=pdf_bytes,
                    file_name=f"profil_dosen_{slugify(row['name'])}_{slugify(row['prodi'])}.pdf",
                    mime="application/pdf"
            )

            # 🗑️ Tombol delete
            if st.button(f"🗑️ Hapus {row['name']}", key=f"delete_{idx}"):
                c.execute("DELETE FROM profil_dosen WHERE name=? AND prodi=?", (row['name'], row['prodi']))
                conn.commit()
                to_delete = idx  # tandai row yang dihapus
                st.session_state["deleted"] = row['name']

            # ✅ Tampilkan notifikasi delete sekali
            if "deleted" in st.session_state:
                st.success(f"✅ Data {st.session_state['deleted']} berhasil dihapus")
                del st.session_state["deleted"]

            # 🔄 Hapus dari dataframe in-memory supaya langsung hilang dari UI
            if to_delete is not None:
                df_filtered = df_filtered.drop(to_delete).reset_index(drop=True)
            
else:
    st.info("Belum ada data dosen yang diproses.")

# ================= Upload CSV Baru =================
with st.sidebar:
    st.subheader("📂 Upload CSV Data Dosen")
    uploaded_file = st.file_uploader("Upload CSV (Kolom: name, scholar_id, sim_url, prodi)", type=["csv"])
    proses = st.button("🔍 Proses Profiling Semua Dosen")

if uploaded_file and proses:
    df_dosen = pd.read_csv(uploaded_file)
    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    total_dosen = len(df_dosen)

    # Mata kuliah per prodi
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

    courses_SI = ["Algoritma dan Pemrograman","Aljabar Linier dan Matriks","Analisis dan Perancangan Sistem Informasi",
                  "Analisis Kebutuhan Informasi","Analisis Resiko Sistem Informasi","Arsitektur Enterprise",
                  "Audit dan Kendali Sistem Informasi","Basis Data","Big Data","Dasar Sistem Informasi","Data Mining",
                  "Data Warehouse","E-Bisnis","Evaluasi Sistem Informasi","Implementasi Sistem Informasi",
                  "Infrastruktur dan Manajemen Layanan TI","Integrasi dan Kustomisasi ERP","Intelegensia Bisnis",
                  "Interaksi Manusia Komputer","Internet of Things","Isu Sosial dan Keprofesian Sistem Informasi",
                  "IT untuk Pemulihan Bencana","Jaminan dan Keamanan Informasi","Jaringan Komputer","Kapita Selekta Sistem Informasi",
                  "Manajemen Pengetahuan","Manajemen Proyek Sistem Informasi","Manajemen Sumber Daya Informasi",
                  "Masyarakat Virtual","Matematika Diskrit","Metode Sampling dan Survei SI","Metodologi Penelitian",
                  "Organisasi dan Arsitektur Komputer","Organisasi dan Manajemen","Pemodelan Proses Bisnis",
                  "Pemrograman Berorientasi Objek","Pemrograman Web","Pendidikan Agama","Rekayasa Layanan",
                  "Rekayasa Perangkat Lunak","Sistem Informasi Enterprise","Sistem Operasi","Statistik","Struktur Data"]

    courses_S2 = ["Manajemen Informasi","Metodologi Penelitian","Rekayasa Perangkat Lunak","Topik dalam Artificial Inteligence",
                  "Topik dalam Business Intelligence","Topik dalam Data Mining","Topik dalam Enterprise Architecture",
                  "Topik dalam Enterprise Information System","Topik dalam Image Processing","Topik dalam Information Retrieval",
                  "Topik dalam IT Governance","Topik dalam Knowledge Governance","Topik dalam Mobile Application",
                  "Topik dalam Risk Management","Topik dalam Wireless dan Mobile Technology","Topik dalam Pemrograman"]

    # Mapping bidang keilmuan
    fields_mapping = {
        "Software Engineering": ["software engineering", "software development", "software testing",
                                 "requirements engineering", "software quality", "SQA", "program analysis"],
        "Artificial Intelligence": ["artificial intelligence", "machine learning", "deep learning",
                                    "neural networks", "computer vision", "natural language processing", "AI"],
        "Networking": ["network", "computer networks", "wireless", "5G", "network security",
                       "network protocols", "SDN", "IoT networks"],
        "Internet of Things": ["internet of things", "IoT", "embedded systems", "cyber physical systems",
                               "sensor networks", "smart devices"],
        "Enterprise Architecture": ["enterprise architecture", "enterprise system", "ERP",
                                    "business process", "enterprise integration", "SOA"],
        "Information Systems": ["information systems", "IS", "business intelligence",
                                "knowledge management", "IT governance", "E-Business"],
        "Cyber Security": ["cybersecurity", "information security", "cryptography",
                           "malware", "intrusion detection", "digital forensics"],
        "Data Science": ["data science", "data mining", "big data", "analytics", "statistics"]
    }

    for idx, row in df_dosen.iterrows():
        progress = int((idx + 1) / total_dosen * 100)
        status_text.text(f"⏳ Memproses {row['name']} ({idx+1}/{total_dosen})...")
        progress_bar.progress(progress)
    # Skip jika scholar_id kosong
        if pd.isna(row['scholar_id']) or not str(row['scholar_id']).strip():
            st.warning(f"⚠️ Dosen {row['name']} dilewati karena scholar_id kosong")
            continue

    # 🔎 Cek apakah sudah ada di database
        c.execute("SELECT id FROM profil_dosen WHERE name=? AND prodi=?", (row['name'], row['prodi']))
        existing = c.fetchone()
        if existing:
            st.info(f"⏩ {row['name']} ({row['prodi']}) sudah ada di database, dilewati...")
            continue

        # --- proses profiling baru ---
        st.markdown(f"## 👤 {row['name']} - {row['prodi']}")
        scholar_id = row['scholar_id']
        sim_url = row['sim_url']
        prodi = row['prodi']

        if prodi == "Teknik Informatika":
            courses = courses_TI
        elif prodi == "Teknik Informatika (PJJ)":
            courses = courses_TI
        elif prodi == "Sistem Informasi":
            courses = courses_SI
        else:
            courses = courses_S2

        # --- Ambil data Google Scholar ---
        competency_text = ""
        publications_texts = []
        author = None
        try:
            author = scholarly.search_author_id(scholar_id)
            if author:
                author = scholarly.fill(author, sections=["basics","indices","counts","publications"])
                competency_text = " ".join(author.get("interests", []))
                for pub in author.get("publications", [])[:20]:
                    try:
                        pub_filled = scholarly.fill(pub)
                        title = pub_filled['bib'].get('title', "")
                        abstract = pub_filled['bib'].get('abstract', "")
                        publications_texts.append(title)
                        competency_text += " " + title + " " + abstract
                    except:
                        pass
        except:
            st.warning(f"⚠️ Gagal ambil data Google Scholar {row['name']}")

        # --- Ambil riwayat mengajar SIM UEU ---
        sim_courses = []
        try:
            r = requests.get(sim_url)
            soup = BeautifulSoup(r.text, "html.parser")
            pengajaran_div = soup.find("div", string="Pengajaran")
            if pengajaran_div:
                table = pengajaran_div.find_next("table", {"class":"GridStyle"})
                if table:
                    rows_table = table.find_all("tr")[1:]
                    for rrow in rows_table:
                        cols = rrow.find_all("td")
                        if len(cols)>=3:
                            sim_courses.append(cols[2].text.strip())
        except:
            pass

        # --- Mapping bidang keilmuan ---
        field_results = []
        for field, keywords in fields_mapping.items():
            field_text = " ".join(keywords)
            sim = cosine_similarity(TfidfVectorizer().fit_transform([competency_text, field_text]))[0,1]
            field_results.append({"Bidang Ilmu": field, "Kesesuaian (%)": round(sim*100)})
        df_fields = pd.DataFrame(field_results).sort_values("Kesesuaian (%)", ascending=False)

        # --- Rekomendasi mata kuliah ---
        corpus = [competency_text] + courses
        vectorizer = TfidfVectorizer().fit_transform(corpus)
        similarity_matrix = cosine_similarity(vectorizer)
        results = []
        for i, course in enumerate(courses):
            score = similarity_matrix[0, i+1]
            if score > 0:
                pub_scores = []
                for pub_text in publications_texts:
                    sim = cosine_similarity(TfidfVectorizer().fit_transform([pub_text, course]))[0,1]
                    pub_scores.append((pub_text, sim))
                pub_scores.sort(key=lambda x: x[1], reverse=True)
                top_pub_titles = [p[0] for p in pub_scores[:3]]
                pernah_diajar = "✅" if course in sim_courses else ""
                results.append({
                    "Mata Kuliah": course,
                    "Kesesuaian (%)": round(score*100),
                    "Publikasi Relevan": "; ".join(top_pub_titles),
                    "Pernah Diajar": pernah_diajar
                })
        df_results = pd.DataFrame(results)

        if not df_results.empty and "Pernah Diajar" in df_results.columns:
            df_results = df_results.sort_values("Pernah Diajar", ascending=False)
        else:
            # fallback: buat DataFrame kosong dengan kolom sesuai kebutuhan
            df_results = pd.DataFrame(columns=["Mata Kuliah", "Kesesuaian (%)", "Publikasi Relevan", "Pernah Diajar"])

        # --- Tampilkan detail ---
        st.markdown("**🔬 Bidang Keilmuan**")
        st.table(df_fields.head(5))
        st.markdown("**🧑‍🏫 Rekomendasi Mata Kuliah**")
        st.dataframe(df_results)

        # --- Generate PDF ---
        pdf_bytes = generate_pdf(row['name'], prodi, author if author else {"name":row['name']}, df_fields, df_results)
        st.download_button(f"⬇️ Download PDF {row['name']}", data=pdf_bytes,
                            file_name=f"profil_dosen_{slugify(row['name'])}_{slugify(prodi)}.pdf",
                            mime="application/pdf")

        # --- Simpan ke SQLite ---
        c.execute("""
            INSERT INTO profil_dosen
            (name, prodi, scholar_id, sim_url, h_index, i10_index, bidang_keilmuan, rekomendasi_mk)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row['name'],
            prodi,
            scholar_id,
            sim_url,
            author.get("hindex",0) if author else 0,
            author.get("i10index",0) if author else 0,
            df_fields.to_json(orient="records"),
            df_results.to_json(orient="records")
        ))
        conn.commit()
        status_text.text("✅ Semua dosen berhasil diproses!")
        progress_bar.empty()
