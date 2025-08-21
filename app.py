import streamlit as st
import pandas as pd
from scholarly import scholarly
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Profiling Dosen Fasilkom Esa Unggul", layout="wide")
st.title("📚 Profiling Dosen Fasilkom Esa Unggul")

# ================= Layout 3 Kolom =================
col1, col2 = st.columns([1, 4])

# --- Input di Kolom Kiri ---
with col1:
    st.subheader("📝 Input Identitas Dosen")
    scholar_id = st.text_input("Google Scholar ID:", placeholder="UN80ApgAAAAJ")
    sim_url = st.text_input("URL SIM UEU Profil Dosen:", placeholder="https://simueu.esaunggul.ac.id/ueu/sdm/index.php?page=data_dosen&key=XXXXX")

    # Mata kuliah per prodi (contoh singkat)
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

    prodi = st.selectbox("Pilih Program Studi", ["Teknik Informatika", "Sistem Informasi", "Magister"])
    if prodi == "Teknik Informatika":
        courses = courses_TI
    elif prodi == "Sistem Informasi":
        courses = courses_SI
    else:
        courses = courses_S2

    proses = st.button("🔍 Proses Profiling")

# --- Hasil Scholar di Kolom Tengah ---
with col2:
    competency_text = ""
    author = None
    publications_texts = []
    if proses and scholar_id:
        try:
            author = scholarly.search_author_id(scholar_id)
            author = scholarly.fill(author, sections=["basics", "indices", "counts", "publications"])

            st.subheader("📖 Google Scholar")
            st.write(f"👤 **{author.get('name','-')}**")
            st.write(f"🏫 {author.get('affiliation','-')}")
            st.write(f"📊 h-index: {author.get('hindex','-')} | i10-index: {author.get('i10index','-')}")
            st.write(f"🌐 Bidang: {', '.join(author.get('interests', []))}")

            competency_text = " ".join(author.get("interests", []))
            for pub in author["publications"][:20]:
                try:
                    pub_filled = scholarly.fill(pub)
                    title = pub_filled['bib'].get('title', "")
                    abstract = pub_filled['bib'].get('abstract', "")
                    publications_texts.append(title)
                    competency_text += " " + title + " " + abstract
                except:
                    pass
        except Exception as e:
            st.error(f"⚠️ Gagal ambil data Google Scholar: {e}")

# --- Ambil Riwayat Pengajaran SIM UEU ---
sim_courses = []
if proses and sim_url:
    try:
        r = requests.get(sim_url)
        soup = BeautifulSoup(r.text, "html.parser")
        pengajaran_div = soup.find("div", text="Pengajaran")
        if pengajaran_div:
            table = pengajaran_div.find_next("table", {"class": "GridStyle"})
            if table:
                rows = table.find_all("tr")[1:]  # skip header
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 3:
                        matkul = cols[2].text.strip()
                        sim_courses.append(matkul)
            else:
                st.warning("⚠️ Tabel Pengajaran tidak ditemukan setelah div")
        else:
            st.warning("⚠️ Bagian 'Pengajaran' tidak ditemukan")
    except Exception as e:
        st.error(f"Gagal ambil riwayat mengajar SIM UEU: {e}")

# --- Rekomendasi Mata Kuliah di Kolom Kanan ---
with col2:
    if proses and scholar_id and competency_text:
        try:
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

            df_results = pd.DataFrame(results).sort_values("Pernah Diajar", ascending=False)
            st.subheader("🧑‍🏫 Rekomendasi Mata Kuliah")
            st.dataframe(df_results)

            # --- Export PDF ---
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer)
            styles = getSampleStyleSheet()
            elements = []
            if author:
                elements.append(Paragraph(f"Profil Dosen: {author.get('name','-')}", styles['Title']))
                elements.append(Spacer(1,12))
                elements.append(Paragraph(f"Afiliasi: {author.get('affiliation','-')}", styles['Normal']))
                elements.append(Paragraph(f"h-index: {author.get('hindex','-')} | i10-index: {author.get('i10index','-')}", styles['Normal']))
                elements.append(Spacer(1,12))

            if df_results.shape[0] > 0:
                table_data = [["Mata Kuliah", "Kesesuaian (%)", "Publikasi Relevan", "Pernah Diajar"]] + df_results.values.tolist()
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

             # --- Generate dynamic filename ---
            def slugify(text):
                return text.lower().replace(" ", "_")

            if author:
                nama_slug = slugify(author['name'])
                prodi_slug = slugify(prodi)
                filename = f"profil_dosen_{nama_slug}_{prodi_slug}.pdf"
            else:
                filename = "profil_dosen.pdf"

            st.download_button("⬇️ Download PDF", data=pdf, file_name=filename, mime="application/pdf")

        except Exception as e:
            st.error(f"Gagal mapping mata kuliah: {e}")
