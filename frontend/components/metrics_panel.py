import streamlit as st
import requests

def render_metrics_panel(backend_url: str):
    """
    Render real-time performance analytics dashboard and KPI metrics.
    """
    st.markdown("### 📊 Real-Time Metrics & Performance Analytics")
    st.caption("Live monitoring of semantic cache efficiency, latency reduction, and LLM API call savings.")

    col_btn, _ = st.columns([1, 4])
    with col_btn:
        if st.button("🔄 Refresh Metrics"):
            st.rerun()

    try:
        res = requests.get(f"{backend_url}/api/metrics", timeout=5)
        if res.status_code == 200:
            m = res.json()

            # KPI Grid
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Total Queries", m["total_requests"])
            with c2:
                st.metric("Cache Hits", m["cache_hits"], delta=f"{m['hit_rate_percentage']}% Hit Rate")
            with c3:
                st.metric("Cache Misses", m["cache_misses"], delta=f"{m['miss_rate_percentage']}% Miss Rate", delta_color="inverse")
            with c4:
                st.metric("API Calls Saved", m["gemini_api_calls_saved"], delta="100% Cost Saved")

            st.divider()

            c5, c6, c7, c8 = st.columns(4)
            with c5:
                st.metric("Avg Total Latency", f"{m['avg_total_latency_ms']} ms")
            with c6:
                st.metric("Avg Gemini Latency", f"{m['avg_gemini_latency_ms']} ms")
            with c7:
                st.metric("Avg Cache Lookup", f"{m['avg_cache_latency_ms']} ms")
            with c8:
                st.metric("Current Cache Size", f"{m['cache_size']} entries")

            st.divider()

            # Chart: Latency Comparison (Gemini API vs Semantic Cache)
            st.subheader("⚡ Response Latency Comparison (ms)")
            chart_data = {
                "Source": ["Gemini LLM API (Cache Miss)", "FAISS Semantic Cache (Cache Hit)"],
                "Latency (ms)": [m["avg_gemini_latency_ms"], m["avg_cache_latency_ms"]]
            }
            st.bar_chart(data=chart_data, x="Source", y="Latency (ms)", use_container_width=True)

        else:
            st.error("Failed to load metrics from backend.")
    except Exception as e:
        st.error(f"Error fetching backend metrics: {e}")
