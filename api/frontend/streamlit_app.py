import os

import requests
import streamlit as st

API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000",
)


# ===
# Configuration
# ===

st.set_page_config(
    page_title="GuitarFlow Transcriber",
    page_icon="🎼",
    layout="wide",
)


# ===
# CSS
# ===

st.markdown(
    """
<style>

.block-container {
    max-width: 1200px;
    padding-top: 2rem;
}

h1 {
    font-weight: 600;
}

.status-card {
    padding: 1rem;
    border-radius: 10px;
    border: 1px solid #ddd;
    background-color: #fafafa;
}

.metric {
    font-size: 0.9rem;
    color: #666;
}

</style>
""",
    unsafe_allow_html=True,
)


# ===
# API helpers
# ===


def api_get(path: str):
    try:
        response = requests.get(
            f"{API_URL}{path}",
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    except Exception:
        return None


def unwrap_api_response(response: dict) -> dict:
    """
    Extract data from generic API response.
    """

    if not response:
        raise RuntimeError("Empty API response")

    if response.get("success") != "success":
        raise RuntimeError(response)

    return response.get("data", {})


def api_download(path: str):
    response = requests.get(
        f"{API_URL}{path}",
        timeout=60,
    )

    response.raise_for_status()

    return response.content


# ===
# Header
# ===

st.title("GuitarFlow Transcriber")
st.caption(
    "Transcription automatique d'un audio de guitare "
    "en fichier MIDI et partition musicale "
    "par une technique de deep learning."
)

health_response = api_get("/health")
health = unwrap_api_response(health_response)

if health:
    api_status = health.get("status")
    if api_status == "ok":
        st.success("API Healthy")
    else:
        st.warning(f"API status: {api_status}")

    col1, col2, col3 = st.columns(3)

    model_loaded = health.get("model_loaded", False)
    with col1:
        st.metric("Modèle chargé", "Oui" if model_loaded else "Non")

    with col2:
        st.metric("Device", health.get("device", "unknown"))

    with col3:
        st.metric("TensorFlow", health.get("tensorflow_version", "unknown"))

    with st.expander("Détails API"):
        st.json(health_response)

else:
    st.error("API indisponible")


st.divider()


# ===
# Sidebar : modèle
# ===

with st.sidebar:
    st.header("Modèle")

    model_response = api_get("/model")
    model_info = unwrap_api_response(model_response)

    if model_info:
        st.write(f"**{model_info.get('name', 'Unknown')}**")
        st.caption(model_info.get("description", ""))

        st.divider()

        st.write("**Framework**")
        st.caption(model_info.get("framework", "unknown"))
        st.write("**Version**")
        st.caption(model_info.get("version", "unknown"))
        st.write("**Dataset entraînement**")
        st.caption(model_info.get("train_dataset", "unknown"))
        st.write("**Input shape**")
        st.caption(str(model_info.get("input_shape", [])))
        st.write("**Output shape**")
        st.caption(str(model_info.get("output_shape", [])))
        st.write("**Threshold**")
        st.caption(str(model_info.get("threshold", None)))

        with st.expander("Payload complet"):
            st.json(model_response)

    else:
        st.warning("Informations modèle indisponibles")


# ===
# Upload
# ===

st.subheader("1. Charger un fichier audio")
st.caption(
    "Le fichier audio doit respecter les contraintes suivantes :"
    "\n- format WAV uniquement,"
    "\n- une seule guitare sur l'enregistrement,"
    "\n- l'accordage de la guitare est standard (EADGBE),"
    "\n- aucun effet de modulation ou de distortion (son clean),"
    "\n- aucun effet de jeu (bend, slide, tapping, ...)."
)

uploaded_file = st.file_uploader(
    "Importer un fichier WAV",
    type=["wav"],
)

if uploaded_file:
    st.audio(
        uploaded_file,
        format="audio/wav",
    )


# ===
# Transcription
# ===

if uploaded_file:
    if st.button(
        "Transcrire",
        type="primary",
        use_container_width=True,
    ):
        with st.spinner("Transcription en cours..."):
            try:
                files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        "audio/wav",
                    )
                }

                response = requests.post(
                    f"{API_URL}/predict",
                    files=files,
                    timeout=900,
                )

                response.raise_for_status()
                prediction_response = response.json()
                prediction = unwrap_api_response(prediction_response)
                st.session_state["prediction"] = prediction
                st.success("Transcription terminée")

            except Exception as exc:
                st.error(f"Erreur pendant la transcription : {exc}")


# ===
# Results
# ===

prediction = st.session_state.get("prediction")
if prediction:
    processing_id = prediction["processing_id"]

    st.divider()

    st.subheader("2. Résultats")

    # ===
    # Summary
    # ===

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Notes détectées", prediction["detected_notes"])

    with col2:
        st.metric("Notes quantifiées", prediction["quantized_notes"])

    with col3:
        st.metric("Durée traitement", f"{prediction['metrics']['total_seconds']:.2f}s")

    # ===
    # Downloads
    # ===

    st.subheader("2.1. Téléchargements")

    col1, col2 = st.columns(2)

    midi = api_download(f"/artifacts/{processing_id}/midi")

    with col1:
        st.download_button(
            label="Télécharger MIDI",
            data=midi,
            file_name="transcription.mid",
            mime="audio/midi",
            use_container_width=True,
        )

    pdf = api_download(f"/artifacts/{processing_id}/score/pdf")

    with col2:
        st.download_button(
            label="Télécharger partition PDF",
            data=pdf,
            file_name="partition.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.divider()

    # ===
    # Piano roll
    # ===

    st.subheader("2.2. Piano roll")

    piano_svg = requests.get(
        f"{API_URL}/artifacts/{processing_id}/piano_roll/svg",
        timeout=60,
    ).text

    st.components.v1.html(
        piano_svg,
        height=500,
        scrolling=True,
    )

    # ===
    # Score
    # ===

    st.subheader("2.3. Partition")

    score_svg = requests.get(
        f"{API_URL}/artifacts/{processing_id}/score/svg",
        timeout=60,
    ).text

    st.components.v1.html(
        score_svg,
        height=900,
        scrolling=True,
    )

    # ===
    # Technical details
    # ===

    with st.expander("Détails techniques"):
        st.json(
            {
                "processing_id": processing_id,
                "metrics": prediction["metrics"],
                "model": prediction["model"],
            }
        )
