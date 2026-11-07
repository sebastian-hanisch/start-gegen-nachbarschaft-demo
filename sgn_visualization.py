"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import math

import plotly.graph_objects as go

import sgn_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_map(inst, routes, title_prefix="Route", rays=None, start_ray=None, legend=True):
    """Karte: Depot als Quadrat, Kunden als Kreise (Größe = Nachfrage, Beschriftung = Nummer), jede Route eine Farbe. `rays`: Winkel (Bogenmaß) der Schnitte zwischen den Clustern als gestrichelte
    Strahlen vom Depot, `start_ray`: Winkel des Startkunden (durchgezogener grauer Strahl). Gleicher Maßstab in x und y über scaleanchor mit autorange; der Rand kommt von zwei unsichtbaren Eckmarken."""
    xs = [p[0] for p in inst.xy]
    ys = [p[1] for p in inst.xy]
    pad = 0.08 * max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[min(xs) - pad, max(xs) + pad], y=[min(ys) - pad, max(ys) + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    reach = 1.15 * max(math.dist(inst.xy[0], p) for p in inst.xy[1:]) if inst.n else 1.0
    for angle, dash, name in [(a, "dot", "Schnitt") for a in (rays or [])] + ([(start_ray, "solid", "Start")] if start_ray is not None else []):
        fig.add_trace(go.Scatter(x=[inst.xy[0][0], inst.xy[0][0] + reach * math.cos(angle)], y=[inst.xy[0][1], inst.xy[0][1] + reach * math.sin(angle)], mode="lines",
                                 line=dict(color="rgba(120,120,120,0.55)", width=1.5, dash=dash), hoverinfo="skip", showlegend=False))
    for r, route in enumerate(routes):
        pts = [inst.xy[0]] + [inst.xy[c] for c in route] + [inst.xy[0]]
        fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines", line=dict(color=C.ROUTE_COLORS[r % len(C.ROUTE_COLORS)], width=3),
                                 name=f"{title_prefix} {r + 1} (Last {inst.load(route)} von {inst.capacity})", hoverinfo="skip"))
    customers = list(range(1, inst.n + 1))
    fig.add_trace(go.Scatter(
        x=[inst.xy[c][0] for c in customers], y=[inst.xy[c][1] for c in customers], mode="markers+text", text=[str(c) for c in customers], textposition="top center",
        marker=dict(size=[9 + 2.5 * inst.demand[c - 1] for c in customers], color="rgba(150,150,150,0.55)", line=dict(color="#555", width=1)),
        customdata=[[inst.demand[c - 1]] for c in customers], hovertemplate="Kunde %{text}: Nachfrage %{customdata[0]}<extra></extra>", name="Kunden (Größe = Nachfrage)"))
    fig.add_trace(go.Scatter(x=[inst.xy[0][0]], y=[inst.xy[0][1]], mode="markers", marker=dict(symbol="square", size=15, color="#222"), name="Depot", hoverinfo="skip"))
    fig.update_yaxes(scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False, showticklabels=False)
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    fig = _base(fig, 380 if legend else 300)
    if not legend:
        fig.update_layout(showlegend=False)
    return fig


def build_heatmap(stats, title="Mittleres Bedauern in % nach der Lokalsuche"):
    """Wärmekarte: Zeilen die Startpläne, Spalten die Nachbarschaften; Zahlen in den Zellen."""
    keys = stats["keys"]
    z = [[stats["mean"][k][nk] for nk in C.NEIGH_KEYS] for k in keys]
    text = [[f"{v:.1f}".replace(".", ",") for v in row] for row in z]
    fig = go.Figure(go.Heatmap(z=z, x=[C.NEIGH[nk][0] for nk in C.NEIGH_KEYS], y=[C.STARTS[k][0] for k in keys], text=text, texttemplate="%{text}", colorscale=[[0, "#e8f3f1"], [1, "#c0504d"]],
                               zmin=0, zmax=max(max(r) for r in z), colorbar=dict(title="%"), hovertemplate="%{y}, %{x}: %{z:.2f} %<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    fig = _base(fig, 330)
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2))
    fig.update_layout(title=dict(text=title, font=dict(size=12)))
    return fig


def build_gain(stats):
    """Je Startplan: Bedauern des Startplans selbst und nach der Lokalsuche mit allen Zügen (Balken; bei Zufallsstarts reicht die Achse weit, darum logarithmisch)."""
    keys = stats["keys"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[C.STARTS[k][0] for k in keys], y=[max(stats["start"][k], 0.01) for k in keys], name="Startplan", marker_color="#9aa5b1", hovertemplate="%{x}: %{y:.1f} %<extra>Startplan</extra>"))
    fig.add_trace(go.Bar(x=[C.STARTS[k][0] for k in keys], y=[max(stats["mean"][k]["alle"], 0.01) for k in keys], name="nach der Lokalsuche (alle Züge)", marker_color="#2F6B65", hovertemplate="%{x}: %{y:.1f} %<extra>nach Lokalsuche</extra>"))
    fig.update_yaxes(title_text="Mittleres Bedauern in % (logarithmisch)", type="log")
    fig.update_layout(barmode="group")
    fig = _base(fig, 360)
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=60), legend=dict(orientation="h", y=-0.35))
    return fig
