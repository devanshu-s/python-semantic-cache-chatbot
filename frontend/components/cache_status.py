import streamlit as st
import requests

def render_cache_status(backend_url: str):
    """
    Render Semantic Cache inspector showing stored vector metadata and entry details.
    """
    st.markdown("### 🗄️ FAISS Semantic Cache Inspector")
    st.caption("Inspect all semantically indexed Python query-response pairs currently saved in vector store.")

    try:
        stats_res = requests.get(f"{backend_url}/api/cache/stats", timeout=5)
        entries_res = requests.get(f"{backend_url}/api/cache/entries", timeout=5)

        if stats_res.status_code == 200 and entries_res.status_code == 200:
            stats = stats_res.json()
            entries = entries_res.json()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Vector Store Count", stats["total_entries"])
            with col2:
                st.metric("Vector Dimension", f"{stats['dimension']}-D")
            with col3:
                st.metric("Default Threshold", stats["similarity_threshold"])

            st.divider()

            if entries:
                filter_text = st.text_input("🔍 Search Cache Entries", placeholder="Filter by prompt or code...")
                filtered = [
                    e for e in entries
                    if filter_text.lower() in e["query"].lower() or filter_text.lower() in e["response"].lower()
                ] if filter_text else entries

                st.write(f"Showing **{len(filtered)}** of **{len(entries)}** entries:")

                for entry in filtered:
                    with st.expander(f"📌 Entry #{entry['id']}: {entry['query'][:80]}..."):
                        st.markdown(f"**Query:** {entry['query']}")
                        st.markdown(f"**Cached Response:**\n{entry['response']}")
                        st.caption(f"**Timestamp:** {entry['timestamp']} | **Vector ID:** {entry['vector_id']}")
            else:
                st.info("No cached queries found in FAISS vector index yet. Start asking questions in the chat!")

        else:
            st.error("Failed to load cache inspector data.")
    except Exception as e:
        st.error(f"Error connecting to cache endpoint: {e}")
