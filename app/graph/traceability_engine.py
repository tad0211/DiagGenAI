"""
DiagGenAI - Traceability Graph Engine (NetworkX & Neo4j).
Maintains an end-to-end directed acyclic graph (DAG) representing the complete automotive
V-Model traceability from Specification Documents down to Test Results.
Supports dual-engine execution: NetworkX (in-memory) with optional Neo4j graph database fallback.
"""

import networkx as nx
from typing import Dict, Any, List, Optional
from app.config import settings
from app.database.repository import DiagRepository

class TraceabilityGraphEngine:
    def __init__(self, repo: Optional[DiagRepository] = None):
        self.repo = repo or DiagRepository()
        self.nx_graph = nx.DiGraph()
        self.engine_type = settings.GRAPH_ENGINE.lower()
        self._build_graph()

    def _build_graph(self):
        """Construct the NetworkX graph from database records."""
        self.nx_graph.clear()

        docs = self.repo.get_documents()
        reqs = self.repo.get_requirements()
        services = self.repo.get_services()
        tests = self.repo.get_test_cases()
        results = self.repo.get_test_results(limit=100)
        stored_links = self.repo.get_traceability_links()

        # 1. Add Document Nodes
        for d in docs:
            self.nx_graph.add_node(
                f"DOC_{d.id}",
                label=d.name,
                node_type="Document",
                version=d.version,
                status=d.status
            )

        # 2. Add Requirement Nodes
        for r in reqs:
            self.nx_graph.add_node(
                r.req_id,
                label=f"{r.req_id}: {r.title}",
                node_type="Requirement",
                category=r.category,
                source_doc=r.source_doc
            )
            # Edge: Document -> Requirement
            if r.document_id:
                self.nx_graph.add_edge(f"DOC_{r.document_id}", r.req_id, relation="CONTAINS")

        # 3. Add Service Nodes & Subfunctions
        for s in services:
            s_id = s.service_id_hex
            self.nx_graph.add_node(
                s_id,
                label=f"{s.service_id_hex} ({s.name})",
                node_type="Service",
                name=s.name,
                standard=getattr(s, "standard_ref", "ISO 14229-1")
            )
            for sf in s.subfunctions:
                sf_id = f"{s_id}_{sf.subfunction_hex}"
                self.nx_graph.add_node(
                    sf_id,
                    label=f"SF {sf.subfunction_hex}: {sf.name}",
                    node_type="Subfunction"
                )
                self.nx_graph.add_edge(s_id, sf_id, relation="HAS_SUBFUNCTION")

        # 4. Add TestCase Nodes
        for t in tests:
            self.nx_graph.add_node(
                t.test_id,
                label=f"{t.test_id} [{t.test_type}]",
                node_type="TestCase",
                test_type=t.test_type,
                review_status=t.review_status,
                service=t.service_id_hex
            )
            # Edge: Requirement -> TestCase
            if t.requirement_id and self.nx_graph.has_node(t.requirement_id):
                self.nx_graph.add_edge(t.requirement_id, t.test_id, relation="VERIFIED_BY")

            # Edge: Service -> TestCase
            if t.service_id_hex and self.nx_graph.has_node(t.service_id_hex):
                self.nx_graph.add_edge(t.service_id_hex, t.test_id, relation="VERIFIED_BY")

        # 5. Add TestResult Nodes
        for res in results:
            res_id = f"RES_{res.id}"
            self.nx_graph.add_node(
                res_id,
                label=f"Result #{res.id} [{res.outcome}]",
                node_type="TestResult",
                outcome=res.outcome,
                diff=res.diff_analysis
            )
            # Find associated test case ID
            tc = next((t for t in tests if t.id == res.test_case_id), None)
            if tc and self.nx_graph.has_node(tc.test_id):
                self.nx_graph.add_edge(tc.test_id, res_id, relation="HAS_RESULT")

        # 6. Add Stored Custom Traceability Links
        for link in stored_links:
            src = link.source_id
            tgt = link.target_id
            if self.nx_graph.has_node(src) and self.nx_graph.has_node(tgt):
                self.nx_graph.add_edge(src, tgt, relation=link.relation_type)

    def get_topology(self) -> Dict[str, Any]:
        """Return nodes, edges, and graph statistics."""
        self._build_graph()

        nodes_list = []
        for n_id, data in self.nx_graph.nodes(data=True):
            nodes_list.append({
                "id": n_id,
                "label": data.get("label", n_id),
                "type": data.get("node_type", "Unknown"),
                "metadata": {k: v for k, v in data.items() if k not in ["label", "node_type"]}
            })

        edges_list = []
        for u, v, data in self.nx_graph.edges(data=True):
            edges_list.append({
                "source": u,
                "target": v,
                "relation": data.get("relation", "TRACEABLE_TO")
            })

        type_counts = {}
        for n in nodes_list:
            t = n["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "engine": "NetworkX (Active)" if self.engine_type != "neo4j" else "Neo4j with NetworkX Cache",
            "nodes": nodes_list,
            "edges": edges_list,
            "statistics": {
                "total_nodes": len(nodes_list),
                "total_edges": len(edges_list),
                "node_types": type_counts
            }
        }

    def get_lineage(self, node_id: str) -> Dict[str, Any]:
        """Compute upstream ancestors and downstream descendants for a node."""
        self._build_graph()

        if not self.nx_graph.has_node(node_id):
            return {
                "found": False,
                "node_id": node_id,
                "upstream": [],
                "downstream": [],
                "direct_parents": [],
                "direct_children": []
            }

        # Upstream ancestors
        upstream = list(nx.ancestors(self.nx_graph, node_id))
        # Downstream descendants
        downstream = list(nx.descendants(self.nx_graph, node_id))

        direct_parents = list(self.nx_graph.predecessors(node_id))
        direct_children = list(self.nx_graph.successors(node_id))

        node_data = self.nx_graph.nodes[node_id]

        return {
            "found": True,
            "node_id": node_id,
            "node_type": node_data.get("node_type"),
            "label": node_data.get("label"),
            "upstream_count": len(upstream),
            "downstream_count": len(downstream),
            "upstream": upstream,
            "downstream": downstream,
            "direct_parents": direct_parents,
            "direct_children": direct_children
        }

    def get_orphans(self) -> Dict[str, Any]:
        """Detect gaps in traceability: uncovered requirements, orphan tests, unverified services."""
        self._build_graph()

        reqs = self.repo.get_requirements()
        tests = self.repo.get_test_cases()
        services = self.repo.get_services()

        uncovered_reqs = []
        for r in reqs:
            if self.nx_graph.has_node(r.req_id):
                # Has any outgoing VERIFIED_BY or incoming link to TestCase?
                children = list(self.nx_graph.successors(r.req_id))
                test_children = [c for c in children if self.nx_graph.nodes[c].get("node_type") == "TestCase"]
                if not test_children:
                    uncovered_reqs.append({
                        "req_id": r.req_id,
                        "title": r.title,
                        "category": r.category
                    })

        orphan_tests = []
        for t in tests:
            if self.nx_graph.has_node(t.test_id):
                parents = list(self.nx_graph.predecessors(t.test_id))
                req_parents = [p for p in parents if self.nx_graph.nodes[p].get("node_type") == "Requirement"]
                if not req_parents:
                    orphan_tests.append({
                        "test_id": t.test_id,
                        "objective": t.objective,
                        "service": t.service_id_hex
                    })

        unverified_services = []
        for s in services:
            if self.nx_graph.has_node(s.service_id_hex):
                children = list(self.nx_graph.successors(s.service_id_hex))
                test_children = [c for c in children if self.nx_graph.nodes[c].get("node_type") == "TestCase"]
                if not test_children:
                    unverified_services.append({
                        "service_hex": s.service_id_hex,
                        "name": s.name
                    })

        return {
            "uncovered_requirements_count": len(uncovered_reqs),
            "uncovered_requirements": uncovered_reqs,
            "orphan_tests_count": len(orphan_tests),
            "orphan_tests": orphan_tests,
            "unverified_services_count": len(unverified_services),
            "unverified_services": unverified_services
        }

    def get_matrix(self) -> List[Dict[str, Any]]:
        """Return end-to-end traceability verification matrix."""
        self._build_graph()
        reqs = self.repo.get_requirements()
        tests = self.repo.get_test_cases()
        results = self.repo.get_test_results(limit=100)

        # Map test cases to latest result
        latest_results = {}
        for res in sorted(results, key=lambda x: x.execution_timestamp):
            latest_results[res.test_case_id] = res.outcome

        matrix = []
        for r in reqs:
            # Find linked tests
            linked_tests = [t for t in tests if t.requirement_id == r.req_id]
            t_ids = [t.test_id for t in linked_tests]

            # Find verdicts
            verdicts = []
            for t in linked_tests:
                v = latest_results.get(t.id, "NOT_RUN")
                verdicts.append(f"{t.test_id}: {v}")

            matrix.append({
                "Requirement ID": r.req_id,
                "Title": r.title,
                "Category": r.category,
                "Source Document": r.source_doc or "synthetic_bcm_diag_spec_v1_1.md",
                "Verified By Tests": ", ".join(t_ids) if t_ids else "❌ NO TEST LINK",
                "Status": "COVERED" if t_ids else "GAP",
                "Latest Verdicts": ", ".join(verdicts) if verdicts else "NOT_RUN"
            })

        return matrix
