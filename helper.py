from io import BytesIO
from typing import Optional, TypedDict

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import RcParams, rcParamsDefault
from matplotlib import colors as mcolors


class InputsDict(TypedDict):
    widget: str
    args: tuple
    kwargs: dict


COLORS = sorted(mcolors.get_named_colors_mapping().keys()) + ["none"]


class DFHelper:
    def __init__(self) -> None:
        pass

    @staticmethod
    def empty():
        df = pd.DataFrame(dict(rcParam=[], Value=[])).set_index("rcParam")
        df = df.astype(str)
        df.index = df.index.astype(str)
        return df

    @staticmethod
    def insert(df: pd.DataFrame, key, val):
        df.loc[key] = val


class RCHelper:
    @staticmethod
    def default() -> RcParams:
        return rcParamsDefault.copy()

    @staticmethod
    def get_sorted_keys(rc: RcParams) -> list[str]:
        return sorted(
            [
                k
                for k in rc.keys()
                if not (
                    k.startswith("_")
                    or k.startswith("figure.hooks")
                    or k.startswith("path.effects")
                )
            ]
        )

    @staticmethod
    def insert(rc: RcParams, key, val):
        rc[key] = val

    @staticmethod
    def fix_string(key, val):
        if (
            key is not None
            and val is not None
            and (
                "figure.figsize" in key
                or "axes.formatter.limits" in key
                or "lines.dashdot_pattern" in key
                or "lines.dotted_pattern" in key
            )
        ):
            val = val.replace("[", "").replace("]", "")
        return val

    @staticmethod
    def get_input_widget_description(
        key: str,
        rc: Optional[RcParams] = None,
        select_options: Optional[dict[str, list]] = None,
        widget_is_picker: bool = True,
    ) -> InputsDict:
        if rc is None:
            rc = rcParamsDefault
        val = None if key is None else rc[key]
        args: tuple
        kwargs: dict
        if key == "lines.dash_capstyle" or key == "lines.solid_capstyle":
            val = val.value  # Convert enum
        if select_options is not None and key in select_options.keys():
            widget = "selectbox"
            args = ("Value" if key is None else key, select_options[key])
            if val in select_options[key]:
                index = select_options[key].index(val)
            elif str(val) in select_options[key]:
                index = select_options[key].index(str(val))
            else:
                index = 0
            kwargs = dict(label_visibility="collapsed", index=index, key=key)
        elif "cmap" in key:
            index = COLORS.index(key) if key in plt.colormaps() else None
            widget = "selectbox"
            args = ("Select a colormap", plt.colormaps())
            kwargs = dict(index=index, label_visibility="collapsed", key=key)
        elif "linewidth" in key:
            widget = "slider"
            args = ("Value" if key is None else key,)
            kwargs = dict(
                value=float(val),
                min_value=0.0,
                max_value=10.0,
                label_visibility="collapsed",
                key=key,
            )
        elif "alpha" in key:
            widget = "slider"
            args = ("Value" if key is None else key,)
            kwargs = dict(
                value=float(val),
                min_value=0.0,
                max_value=1.0,
                label_visibility="collapsed",
                key=key,
            )
        elif (
            "color" in key
            and "patch.force_edgecolor" not in key
            and "pcolor" not in key
            and "pdf.inheritcolor" not in key
        ):
            if widget_is_picker:
                color_hex = "none" if val is None else mcolors.to_hex(val)
                widget = "color_picker"
                args = ("Pick a color",)
                kwargs = dict(value=color_hex, label_visibility="collapsed", key=key)
            else:
                widget = "selectbox"
                colors = COLORS
                if key == "axes.titlecolor":
                    colors += ["auto"]
                elif key == "legend.facecolor":
                    colors += ["inherit"]
                index = colors.index(key) if key in colors else colors.index("none")
                args = ("Select a color", colors)
                kwargs = dict(index=index, label_visibility="collapsed", key=key)
        elif isinstance(val, bool):
            widget = "toggle"
            args = ("Off/On",)
            kwargs = dict(value=bool(val), label_visibility="visible", key=key)
        else:
            widget = "text_input"
            args = ("Value" if key is None else key,)
            kwargs = dict(value=f"{rc[key]}", label_visibility="collapsed", key=key)
        return InputsDict(widget=widget, args=args, kwargs=kwargs)

    @staticmethod
    def write_binary(rc: RcParams, out: Optional[BytesIO] = None):
        if out is None:
            out = BytesIO()
        for k, v in rc.items():
            w = RCHelper.fix_string(k, f"{k}: {v}\n")
            out.write(w.encode("utf8"))
        return out
