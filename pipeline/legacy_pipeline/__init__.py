SHOTGUN = False
try:
    import sgtk
    SHOTGUN = True
except:
    pass

if SHOTGUN:
    from legacy_pipeline.lib import pipeline_tools_shotgun as pipeline_tools
else:
    from legacy_pipeline.lib import pipeline_tools_regular as pipeline_tools

__all__ = [
    "pipeline_tools",
]
