import os
import streamlit.components.v1 as components

_RELEASE = True

if not _RELEASE:
    _component_func = components.declare_component(
        "ppt_editor",
        url="http://localhost:5173",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "dist")
    _component_func = components.declare_component("ppt_editor", path=build_dir)

def st_ppt_editor(presentation_state, key=None):
    component_value = _component_func(presentation_state=presentation_state, key=key, default={"slides": presentation_state.get("slides", [])})
    return component_value
