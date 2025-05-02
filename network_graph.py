import heapq

class RouterGraph:
    def __init__(self):
        self.graph = {}

    def add_router(self, name):
        if name not in self.graph:
            self.graph[name] = {}

    def add_link(self, from_router, to_router, cost=1):
        self.add_router(from_router)
        self.add_router(to_router)
        self.graph[from_router][to_router] = cost
        self.graph[to_router][from_router] = cost

    def shortest_path(self, start, end):
        queue = [(0, start, [])]
        visited = set()

        while queue:
            (cost, current, path) = heapq.heappop(queue)
            if current in visited:
                continue
            path = path + [current]
            if current == end:
                return path
            visited.add(current)
            for neighbor, weight in self.graph[current].items():
                if neighbor not in visited:
                    heapq.heappush(queue, (cost + weight, neighbor, path))

        return None
