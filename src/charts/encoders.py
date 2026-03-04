import base64
from io import BytesIO

import matplotlib.pyplot as plt
from matplotlib.figure import Figure


def fig_to_base64(fig: Figure) -> str:
    buf = BytesIO()
    try:
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
    finally:
        plt.close(fig)
        buf.close()
