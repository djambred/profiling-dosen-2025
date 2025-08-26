import streamlit as st
import sqlite3
import pandas as pd
import json

st.title("📊 Analisa Kesesuaian Mata Kuliah per Dosen")

# --- ambil data dari DB ---
conn = sqlite3.connect("profil_dosen.db")
df = pd.read_sql_query("SELECT name, prodi, rekomendasi_mk FROM profil_dosen", conn)
conn.close()

data = []
for _, row in df.iterrows():
    if row["rekomendasi_mk"]:  # tidak kosong
        try:
            rekomendasi = json.loads(row["rekomendasi_mk"])
            for mk in rekomendasi:
                data.append({
                    "Nama Dosen": row["name"],
                    "Prodi": row["prodi"],
                    "Mata Kuliah": mk.get("Mata Kuliah", ""),
                    "Kesesuaian (%)": mk.get("Kesesuaian (%)", ""),
                    "Publikasi Relevan": mk.get("Publikasi Relevan", ""),
                    "Pernah Diajar": mk.get("Pernah Diajar", "")
                })
        except Exception as e:
            st.warning(f"⚠️ Data rekomendasi_mk rusak untuk {row['name']}: {e}")

if not data:
    st.info("Belum ada data mata kuliah yang diprofiling.")
else:
    df_mk = pd.DataFrame(data)

    # 🔽 Filter prodi dulu
    prodi_list = sorted(df_mk["Prodi"].unique())
    selected_prodi = st.selectbox("Pilih Prodi", ["(Semua)"] + prodi_list)

    if selected_prodi != "(Semua)":
        df_filtered = df_mk[df_mk["Prodi"] == selected_prodi]

        # 🔽 Filter mata kuliah berdasarkan prodi
        mk_list = sorted(df_filtered["Mata Kuliah"].unique())
        selected_mk = st.selectbox("Pilih Mata Kuliah", ["(Semua)"] + mk_list)

        if selected_mk != "(Semua)":
            st.subheader(f"📘 Analisa {selected_mk} untuk Prodi {selected_prodi}")
            st.dataframe(df_filtered[df_filtered["Mata Kuliah"] == selected_mk], use_container_width=True)
        else:
            st.subheader(f"📘 Semua Mata Kuliah untuk Prodi {selected_prodi}")
            st.dataframe(df_filtered, use_container_width=True)
    else:
        st.subheader("📘 Semua Data (tanpa filter Prodi)")
        st.dataframe(df_mk, use_container_width=True)
