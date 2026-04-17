# ui/help_dialog.py
from pathlib import Path
import streamlit as st


def _safe_image(path: str, caption: str):
    p = Path(path)
    if p.exists():
        st.image(str(p), caption=caption, use_column_width=True)


def render_help_button(t):
    """
    右上ヘルプボタン + ダイアログ本体
    t: 翻訳関数（ui.i18n.t）
    """
    if st.button(f":material/info: {t('help.button')}", help=t("help.button_help")):
        _show_help_dialog(t)


@st.dialog("JyotiSON User Guide", width="large")
def _show_help_dialog(t):
    _inject_style()

    tab_how, tab_about, tab_faq, tab_trouble = st.tabs([
        f":material/help: {t('help.tab.how')}",
        f":material/description: {t('help.tab.about')}",
        f":material/quiz: {t('help.tab.faq')}",
        f":material/build: {t('help.tab.trouble')}",
    ])

    _tab_how(tab_how, t)
    _tab_about(tab_about, t)
    _tab_faq(tab_faq, t)
    _tab_trouble(tab_trouble, t)

    st.divider()
    st.caption(t("help.footer"))


def _tab_how(tab, t):
    with tab:
        st.markdown(f"## {t('help.how.title')}")

        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown(f"### {t('help.how.step1.title')}")
            st.markdown(t("help.how.step1.body"))
        with c2:
            _safe_image("assets/guide_step1.png", t("help.how.step1.image"))

        st.divider()

        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown(f"### {t('help.how.step2.title')}")
            st.markdown(t("help.how.step2.body"))
            st.info(t("help.how.step2.note"))
        with c2:
            _safe_image("assets/guide_step2.png", t("help.how.step2.image"))

        st.divider()

        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown(f"### {t('help.how.step3.title')}")
            st.markdown(t("help.how.step3.body"))
        with c2:
            _safe_image("assets/guide_step3.png", t("help.how.step3.image"))

        st.divider()
        st.markdown(f"### {t('help.how.output.title')}")
        st.markdown(t("help.how.output.body"))


def _tab_about(tab, t):
    with tab:
        st.markdown(f"## {t('help.about.title')}")
        st.write(t("help.about.body"))

        st.markdown(f"### {t('help.about.philosophy.title')}")
        st.markdown(t("help.about.philosophy.body"))

        st.markdown(f"### {t('help.about.assumptions.title')}")
        st.markdown(t("help.about.assumptions.body"))

        st.warning(t("help.about.disclaimer"))


def _tab_faq(tab, t):
    with tab:
        st.markdown(f"## {t('help.faq.title')}")

        with st.expander(t("help.faq.q1.q")):
            st.markdown(t("help.faq.q1.a"))

        with st.expander(t("help.faq.q2.q")):
            st.markdown(t("help.faq.q2.a"))

        with st.expander(t("help.faq.q3.q")):
            st.markdown(t("help.faq.q3.a"))

        with st.expander(t("help.faq.q4.q")):
            st.code(t("help.faq.q4.a"), language="text")


def _tab_trouble(tab, t):
    with tab:
        st.markdown(f"## {t('help.trouble.title')}")
        st.markdown(t("help.trouble.checklist"))

        with st.expander(t("help.trouble.slow.q")):
            st.markdown(t("help.trouble.slow.a"))

        with st.expander(t("help.trouble.large.q")):
            st.markdown(t("help.trouble.large.a"))


def _inject_style():
    st.markdown(
        """
        <style>
        .stDialog { max-width: 1100px; }
        </style>
        """,
        unsafe_allow_html=True
    )