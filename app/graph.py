from collections import deque, defaultdict
def cycles(nodes, links):
    '''Returns number of cycles in graph. Orphan nodes are not considered cycles.'''
    seen = set()
    cycles = 0
    graph = defaultdict(list)

    for link in links:
        graph[link['source']].append(link['target'])

    def bfs(start):
        q = deque()
        q.append(start)

        while q:
            node = q.popleft()
            seen.add(node)

            for neighbor in graph[node]:
                if neighbor not in seen:
                    q.append(neighbor)

    for node in nodes:
        if node not in seen and node in graph:
            bfs(node)
            cycles += 1

    return cycles
