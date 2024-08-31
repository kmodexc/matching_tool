import importlib.metadata
try:
  __version__ = importlib.metadata.version("tufast_matching_tool")
except:
  pass