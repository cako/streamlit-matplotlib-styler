import re
from difflib import get_close_matches
from io import BytesIO

import matplotlib.pyplot as plt
import streamlit as st
from matplotlib import matplotlib_fname
from PIL import Image
from streamlit_js_eval import streamlit_js_eval

from helper import DFHelper, RCHelper
from style_sheets_reference import plot_figure


@st.cache_data
def get_keys_options():
    options = {}
    with open(matplotlib_fname(), "r") as f:
        for line in f:
            s = line.split(": ")
            if len(s) > 1 and not s[0].startswith("##"):
                vals = re.findall(r"^.*\{(.*)\}.*$", s[1], re.UNICODE)
                if len(vals) > 0:
                    key = re.sub(r"^(\#*)(.*?)$", r"\2", s[0], flags=re.UNICODE).strip()
                    options[key] = [v.strip() for v in vals[0].split(",")]
    options["legend.loc"] = [
        "best",
        "upper right",
        "upper left",
        "lower left",
        "lower right",
        "right",
        "center left",
        "center right",
        "lower center",
        "upper center",
        "center",
    ]
    return options


def main():
    # Decrease whitespace at the top of the document.
    st.markdown(
        """
            <style>
                .appview-container .main .block-container {{
                    padding-top: {padding_top}rem;
                    padding-bottom: {padding_bottom}rem;
                    }}
            </style>""".format(padding_top=1, padding_bottom=1),
        unsafe_allow_html=True,
    )
    col_sidebar, col_content = st.columns([1, 3])

    # UI: Sidebar
    with col_sidebar:
        # UI: Header
        st.markdown(
            "<h2 style='text-align: center; margin: 0px;'>Style Editor</h2>",
            unsafe_allow_html=True,
        )
        st.image(
            Image.open("./static/logo_light.png"),
            caption="Edit styles, persist changes, export.",
            use_column_width=True,
        )
        st.markdown("<div style='margin: 0px;'><br></hdiv>", unsafe_allow_html=True)

        # UI: rcParam selector
        param = st.selectbox(
            "rcParam",
            st.session_state["rckeys"],
            index=None,
            placeholder="Choose an rcParam",
            label_visibility="collapsed",
        )
        if param is None:
            value = st.text_input(
                "Value",
                label_visibility="collapsed",
                placeholder="Enter a value",
                disabled=param is None,
            )
        else:
            select_options = get_keys_options()
            write_to = st
            widget_is_picker = False
            if "color" in param:
                cola, colb = st.columns([1, 1])
                widget_is_picker = cola.toggle("Name/Picker")
                write_to = colb
            widget_desc = RCHelper.get_input_widget_description(
                param, select_options=select_options, widget_is_picker=widget_is_picker
            )
            value = getattr(write_to, widget_desc["widget"])(
                *widget_desc["args"], **widget_desc["kwargs"]
            )
        # Some parameters are not converted properly, they must be fixed
        value = RCHelper.fix_string(param, value)

        # UI: Persist button
        addme = st.button(
            "Persist change", use_container_width=True, disabled=param is None
        )
        if addme and value is not None and param is not None:
            RCHelper.insert(st.session_state["rc"], param, value)
            DFHelper.insert(st.session_state["df"], param, value)

        # UI: Dataframe editor
        df_edit = st.data_editor(st.session_state["df"], num_rows="dynamic")
        # Check that all keys exist
        for key in df_edit.index:
            if key not in st.session_state["rc"].keys():
                key_sugest = get_close_matches(key, st.session_state["rckeys"], n=1)[0]
                st.error(f"Invalid rcParam '{key}'. Do you mean '{key_sugest}'?")

        # Update all keys with new values, but also revert any keys not present
        # in edited_df with default value
        for key in st.session_state["rc"].keys():
            replace = key in df_edit.index and df_edit.loc[key]["Value"] is not None
            val = (
                df_edit.loc[key]["Value"]
                if replace
                else st.session_state["rc_default"][key]
            )
            RCHelper.insert(st.session_state["rc"], key, val)
        # st.session_state["df"] = df_edit # Not sure if this is required or not

        # UI: Download button
        enable_download = not st.session_state["df"].empty
        contents = BytesIO()
        if enable_download:
            RCHelper.write_binary(st.session_state["rc"], out=contents)
        st.download_button(
            "Download",
            contents,
            file_name="rcParams.mplstyle",
            mime="text/csv",
            use_container_width=True,
            disabled=not enable_download,
        )

    # UI: Plots
    with col_content:
        rc_tmp = st.session_state["rc"].copy()
        if value is not None and param is not None:
            RCHelper.insert(rc_tmp, param, value)
        figwidth_px = streamlit_js_eval(js_expressions="screen.width", want_output=True)
        if figwidth_px is None:
            figwidth_px = 1000

        with plt.rc_context(rc_tmp):
            fig = plot_figure((0.5 * figwidth_px, 0.25 * figwidth_px))
            st.pyplot(fig)


if __name__ == "__main__":
    im = Image.open("./static/sphx_glr_logos2_002.png")
    st.set_page_config(page_title="Matplotlib Styles", layout="wide", page_icon=im)

    # Store state variables
    if "rc_default" not in st.session_state:
        st.session_state["rc_default"] = RCHelper.default()
    if "rc" not in st.session_state:
        st.session_state["rc"] = RCHelper.default()
    if "df" not in st.session_state:
        st.session_state["df"] = DFHelper.empty()
    if "rckeys" not in st.session_state:
        st.session_state["rckeys"] = RCHelper.get_sorted_keys(st.session_state["rc"])

    main()
