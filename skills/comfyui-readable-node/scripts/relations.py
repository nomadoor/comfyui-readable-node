"""Positions from relations, all at once (used by canvas.py's layout). Python standard library only.

A Problem holds positions along one axis (variables) and relations between them:
- a hard edge u -> v with d: pos[v] - pos[u] >= d. Hard edges are added first and are always kept.
- an equality pos[v] - pos[u] = c, added with try_equal. The two variables are merged into one block (a union-find
  with offsets: pos[v] = pos[block] + offset[v]). It is kept only if the relations kept so far can still be solved.
- an inequality added later with try_edge: kept only if they can still be solved.
"Can be solved" means: after merging the blocks, the edges between blocks form a graph without a cycle, and every edge
inside one block is met by the offsets (network simplex takes only such graphs). A relation that is not kept is
returned with the reason, never forced. Then solve() places the blocks: every hard and kept edge holds, and the sum of
the distances of the variables from their initial positions (a magnet, all of the same weight) is as small as possible.

Network simplex: Gansner, Koutsofios, North, Vo 1993, "A Technique for Drawing Directed Graphs", section 2.3 (Figures
2-1 and 2-2). A distance |a - b| is put in as in section 4.2: an extra node n with edges n -> a and n -> b.
"""
import math
from collections import defaultdict, deque

TOL = 0.5   # a relation inside one block holds when it is met within this (px)


class NetworkSimplex:
    """min sum w(e) * (rank[head] - rank[tail]) subject to rank[head] - rank[tail] >= d(e) for every edge.
    w >= 0, d an integer. The graph has no cycle and is connected. Ties are broken by the lower edge number, so the
    same problem gives the same result."""

    def __init__(self, n, edges):
        self.n = n
        self.edges = [(t, h, int(d), float(w)) for t, h, d, w in edges]
        self.out = defaultdict(list)
        self.inn = defaultdict(list)
        self.inc = defaultdict(list)
        for k, (t, h, d, w) in enumerate(self.edges):
            self.out[t].append(k)
            self.inn[h].append(k)
            self.inc[t].append(k)
            self.inc[h].append(k)
        self.rank = [0] * n
        self.iterations = 0

    def slack(self, k):
        t, h, d, _ = self.edges[k]
        return self.rank[h] - self.rank[t] - d

    def init_rank(self):
        indeg = [len(self.inn[v]) for v in range(self.n)]
        q = deque(v for v in range(self.n) if indeg[v] == 0)
        rank = [None] * self.n
        for v in q:
            rank[v] = 0
        seen = 0
        while q:
            v = q.popleft()
            seen += 1
            for k in self.out[v]:
                _, h, d, _ = self.edges[k]
                r = rank[v] + d
                rank[h] = r if rank[h] is None else max(rank[h], r)
                indeg[h] -= 1
                if indeg[h] == 0:
                    q.append(h)
        if seen != self.n:
            raise ValueError("the graph has a cycle")
        self.rank = rank

    def tight_tree(self, start=0):
        tree_nodes, tree_edges, stack = {start}, set(), [start]
        while stack:
            v = stack.pop()
            for k in sorted(self.inc[v]):
                t, h, _, _ = self.edges[k]
                u = h if t == v else t
                if u not in tree_nodes and self.slack(k) == 0:
                    tree_nodes.add(u)
                    tree_edges.add(k)
                    stack.append(u)
        return tree_edges, tree_nodes

    def feasible_tree(self):
        self.init_rank()
        while True:
            tree_edges, tree_nodes = self.tight_tree(0)
            if len(tree_nodes) == self.n:
                self.tree = tree_edges
                return
            best = None
            for v in sorted(tree_nodes):
                for k in self.inc[v]:
                    t, h, _, _ = self.edges[k]
                    if (t in tree_nodes) != (h in tree_nodes):
                        s = self.slack(k)
                        if best is None or (s, k) < best:
                            best = (s, k)
            if best is None:
                raise ValueError("the graph is not connected")
            s, k = best
            t, _, _, _ = self.edges[k]
            delta = s if t in tree_nodes else -s
            for v in tree_nodes:
                self.rank[v] += delta

    def root_tree(self):
        adj = defaultdict(list)
        for k in sorted(self.tree):
            t, h, _, _ = self.edges[k]
            adj[t].append((h, k))
            adj[h].append((t, k))
        self.parent = [None] * self.n
        self.pedge = [None] * self.n
        self.low = [0] * self.n
        self.lim = [0] * self.n
        order, counter = [], 0
        stack, visited = [(0, iter(adj[0]))], {0}
        while stack:
            v, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                stack.pop()
                self.lim[v] = counter
                counter += 1
                order.append(v)
                continue
            u, k = nxt
            if u in visited:
                continue
            visited.add(u)
            self.parent[u] = v
            self.pedge[u] = k
            self.low[u] = counter
            stack.append((u, iter(adj[u])))
        self.post = order

    def in_subtree(self, v, c):
        return self.low[c] <= self.lim[v] <= self.lim[c]

    def cut_values(self):
        a = [0.0] * self.n
        for t, h, _, w in self.edges:
            a[t] += w
            a[h] -= w
        s = a[:]
        for v in self.post:
            p = self.parent[v]
            if p is not None:
                s[p] += s[v]
        cut = {}
        for c in range(self.n):
            k = self.pedge[c]
            if k is None:
                continue
            t, _, _, _ = self.edges[k]
            cut[k] = s[c] if t == c else -s[c]
        return cut

    def solve(self, max_iter=100000):
        self.feasible_tree()
        while self.iterations < max_iter:
            self.root_tree()
            cut = self.cut_values()
            leave = min((k for k, v in cut.items() if v < -1e-9), default=None)
            if leave is None:
                break
            t, h, _, _ = self.edges[leave]
            child = t if self.parent[t] == h and self.pedge[t] == leave else h
            tail_is_sub = child == t
            best = None
            for k, (et, eh, _, _) in enumerate(self.edges):
                if k in self.tree:
                    continue
                et_in, eh_in = self.in_subtree(et, child), self.in_subtree(eh, child)
                if et_in == eh_in:
                    continue
                et_tail = et_in if tail_is_sub else not et_in
                eh_tail = eh_in if tail_is_sub else not eh_in
                if not et_tail and eh_tail:
                    s = self.slack(k)
                    if best is None or (s, k) < best:
                        best = (s, k)
            if best is None:
                raise ValueError("no edge to enter (the problem is unbounded)")
            s, enter = best
            for v in range(self.n):
                v_in = self.in_subtree(v, child)
                if (not v_in) if tail_is_sub else v_in:
                    self.rank[v] += s
            self.tree.remove(leave)
            self.tree.add(enter)
            self.iterations += 1
        return self.rank


class Problem:
    def __init__(self):
        self.names, self.index = [], {}
        self.parent, self.off = [], []
        self.init = []
        self.edges = []        # (u, v, d, label): pos[v] - pos[u] >= d
        self.wishes = []       # (u, cu, v, cv): |(pos[u] + cu) - (pos[v] + cv)| as small as possible (weight 1)
        self.joined_by = []    # the label of the relation that last joined each variable to its block

    def var(self, name, init=None):
        """The variable called name (made on first use). init: its initial position (the magnet pulls it there)."""
        if name in self.index:
            return self.index[name]
        i = len(self.names)
        self.names.append(name)
        self.index[name] = i
        self.parent.append(i)
        self.off.append(0.0)
        self.init.append(init)
        self.joined_by.append(None)
        return i

    def find(self, v):
        """(block, offset): pos[v] = pos[block] + offset."""
        o = 0.0
        while self.parent[v] != v:
            o += self.off[v]
            v = self.parent[v]
        return v, o

    def hard(self, u, v, d, label=""):
        """pos[v] - pos[u] >= d, always kept (the caller makes sure the hard edges alone have no cycle)."""
        self.edges.append((u, v, d, label))

    def wish(self, u, cu, v, cv):
        self.wishes.append((u, cu, v, cv))

    def _contracted(self):
        """The edges between blocks [(bu, bv, d)], or None when an edge inside a block is not met."""
        out = []
        for u, v, d, _ in self.edges:
            bu, ou = self.find(u)
            bv, ov = self.find(v)
            need = d + ou - ov   # pos[bv] - pos[bu] >= need
            if bu == bv:
                if need > TOL:
                    return None
                continue
            out.append((bu, bv, need))
        return out

    def solvable(self):
        es = self._contracted()
        if es is None:
            return False
        blocks = {self.find(v)[0] for v in range(len(self.names))}
        indeg = {b: 0 for b in blocks}
        out = defaultdict(list)
        for bu, bv, _ in es:
            out[bu].append(bv)
            indeg[bv] += 1
        q = deque(b for b in blocks if indeg[b] == 0)
        seen = 0
        while q:
            b = q.popleft()
            seen += 1
            for c in out[b]:
                indeg[c] -= 1
                if indeg[c] == 0:
                    q.append(c)
        return seen == len(blocks)

    def try_equal(self, u, v, c, label=""):
        """Keeps pos[v] - pos[u] = c if everything kept so far can still be solved. Returns (kept, why not)."""
        bu, ou = self.find(u)
        bv, ov = self.find(v)
        if bu == bv:
            if abs(ov - ou - c) <= TOL:
                return True, ""
            return False, f"already held otherwise by {self.joined_by[v] or self.joined_by[u] or 'an earlier relation'}"
        old = (self.parent[bv], self.off[bv], self.joined_by[bv])
        self.parent[bv], self.off[bv] = bu, c + ou - ov
        self.joined_by[bv] = label
        if self.solvable():
            for x in (u, v):
                if self.joined_by[x] is None:
                    self.joined_by[x] = label
            return True, ""
        self.parent[bv], self.off[bv], self.joined_by[bv] = old
        return False, "it cannot hold together with the relations kept before it"

    def try_edge(self, u, v, d, label=""):
        """Keeps pos[v] - pos[u] >= d if everything kept so far can still be solved. Returns (kept, why not)."""
        self.edges.append((u, v, d, label))
        if self.solvable():
            return True, ""
        self.edges.pop()
        return False, "it cannot hold together with the relations kept before it"

    def block_of(self, v):
        """The variables in v's block."""
        b = self.find(v)[0]
        return {u for u in range(len(self.names)) if self.find(u)[0] == b}

    def snapshot(self):
        """What has been kept so far, to go back to with restore (a choice that turns out to break a requirement the
        problem cannot express, such as a wire passing behind a node)."""
        return (list(self.parent), list(self.off), list(self.joined_by), list(self.edges), len(self.wishes))

    def restore(self, snap):
        self.parent, self.off, self.joined_by = list(snap[0]), list(snap[1]), list(snap[2])
        self.edges = list(snap[3])
        del self.wishes[snap[4]:]

    def replace_hard(self, drop, add):
        """Takes out the hard edges for which drop(u, v, label) holds and puts in add [(u, v, d, label)] (an order between
        variables chosen again, for a move that passes another node). The caller checks solvable() and restores."""
        self.edges = [e for e in self.edges if not drop(e[0], e[1], e[3])] + list(add)

    def try_edges(self, edges, label=""):
        """Keeps all of these edges [(u, v, d)] or none of them."""
        n = len(self.edges)
        self.edges += [(u, v, d, label) for u, v, d in edges]
        if self.solvable():
            return True, ""
        del self.edges[n:]
        return False, "it cannot hold together with the relations kept before it"

    def solve(self):
        """Positions of every variable [pos], with every hard and kept relation held and the magnet as small as possible."""
        n = len(self.names)
        blocks = sorted({self.find(v)[0] for v in range(n)})
        node = {b: k for k, b in enumerate(blocks)}
        top = len(blocks)
        size = [top + 1]
        es = []
        for bu, bv, need in self._contracted():
            es.append((node[bu], node[bv], math.ceil(need - 1e-6), 0.0))

        def dist(a, ca, b, cb):
            x = size[0]
            size[0] += 1
            es.append((x, a, -int(round(ca)), 1.0))
            es.append((x, b, -int(round(cb)), 1.0))
        for v in range(n):
            if self.init[v] is not None:
                b, o = self.find(v)
                dist(node[b], o, top, self.init[v])
        for u, cu, v, cv in self.wishes:
            bu, ou = self.find(u)
            bv, ov = self.find(v)
            if bu != bv:
                dist(node[bu], ou + cu, node[bv], ov + cv)
        # every block reached from the top (a block with no magnet would leave the graph unconnected)
        for b in blocks:
            es.append((top, node[b], -10 ** 7, 0.0))
        ns = NetworkSimplex(size[0], es)
        rank = ns.solve()
        base = {b: rank[node[b]] - rank[top] for b in blocks}
        return [base[self.find(v)[0]] + self.find(v)[1] for v in range(n)]
