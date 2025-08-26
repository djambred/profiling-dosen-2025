import streamlit as st
import sqlite3, json
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Analisa Bidang Ilmu", layout="wide")

st.title("🔍 Analisa Bidang Ilmu Dosen")

conn = sqlite3.connect("profil_dosen.db")
df = pd.read_sql("SELECT * FROM profil_dosen", conn)

if df.empty:
    st.warning("Belum ada data dosen di database.")
    st.stop()

# Flatten bidang ilmu
all_records = []
for _, row in df.iterrows():
    bidang_list = json.loads(row["bidang_keilmuan"])
    for b in bidang_list:
        all_records.append({
            "Nama Dosen": row["name"],
            "Prodi": row["prodi"],
            "Bidang Ilmu": b["Bidang Ilmu"],
            "Kesesuaian": b["Kesesuaian (%)"]
        })

df_bidang = pd.DataFrame(all_records)

# Input bidang ilmu
pilihan = st.multiselect("Pilih Bidang Ilmu", sorted(df_bidang["Bidang Ilmu"].unique()))

if pilihan:
    st.subheader("📌 Dosen yang Cocok")
    hasil = df_bidang[df_bidang["Bidang Ilmu"].isin(pilihan)]
    hasil = hasil.sort_values(["Bidang Ilmu","Kesesuaian"], ascending=[True,False])
    st.dataframe(hasil)

    # Chart
    fig, ax = plt.subplots(figsize=(10,5))
    hasil.groupby("Bidang Ilmu")["Nama Dosen"].nunique().plot(kind="bar", ax=ax)
    ax.set_ylabel("Jumlah Dosen")
    ax.set_title("Distribusi Dosen per Bidang Ilmu")
    st.pyplot(fig)
