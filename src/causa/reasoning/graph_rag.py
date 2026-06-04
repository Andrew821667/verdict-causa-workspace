import networkx as nx

from causa.core.models import LegalSource


def build_source_graph(sources: list[LegalSource]) -> nx.DiGraph:
    graph = nx.DiGraph()
    for source in sources:
        graph.add_node(source.id, title=source.title, source_type=source.source_type.value)
    return graph
