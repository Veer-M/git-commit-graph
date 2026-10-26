from dataclasses import asdict, dataclass
import heapq
import subprocess

@dataclass
class Commit:
    sha: str
    parents: list
    author: str
    date: str
    subject: str
    refs: str

def git(repository, *arguments):
    result = subprocess.run(['git','-C',str(repository),*arguments],text=True,
                            encoding='utf-8',errors='replace',capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or 'Cannot read Git history')
    return result.stdout

def read_history(repository='.', limit=100, all_refs=False, ref=None):
    if not 1 <= limit <= 2000:
        raise ValueError('Limit must be between 1 and 2000 commits')
    if all_refs and ref is not None:
        raise ValueError('Choose either all refs or one ref')
    arguments = ['log','--topo-order',f'--max-count={limit}','--encoding=UTF-8',
                 '--pretty=format:%H%x00%P%x00%an%x00%aI%x00%s%x00%D']
    if all_refs:
        arguments.append('--all')
    elif ref is not None:
        resolved = git(repository,'rev-parse','--verify','--end-of-options',ref+'^{commit}').strip()
        arguments.append(resolved)
    commits = []
    for line in git(repository,*arguments).splitlines():
        sha,parents,author,date,subject,refs = line.split('\0',5)
        commits.append(Commit(sha,parents.split(),author,date,subject,refs))
    return commits

def topological_order(graph):
    order = {sha:i for i,sha in enumerate(graph)}
    children = dict.fromkeys(graph,0)
    for parents in graph.values():
        for parent in parents:
            if parent in children:
                children[parent] += 1
    ready = [(order[sha],sha) for sha,count in children.items() if count == 0]
    heapq.heapify(ready)
    result = []
    while ready:
        _,sha = heapq.heappop(ready)
        result.append(sha)
        for parent in graph[sha]:
            if parent in children:
                children[parent] -= 1
                if children[parent] == 0:
                    heapq.heappush(ready,(order[parent],parent))
    if len(result) != len(graph):
        raise ValueError('Commit ancestry contains a cycle')
    return result

def statistics(graph):
    children = dict.fromkeys(graph,0)
    edges,boundary = 0,0
    for parents in graph.values():
        for parent in parents:
            if parent in children:
                children[parent] += 1
                edges += 1
            else:
                boundary += 1
    return {'commits':len(graph),'visible_parent_edges':edges,'boundary_parent_edges':boundary,
            'merges':sum(len(parents)>1 for parents in graph.values()),
            'roots':sum(not parents for parents in graph.values()),
            'branch_points':sum(count>1 for count in children.values()),
            'tips':sum(count==0 for count in children.values())}

def export_data(commits, positions):
    graph = {c.sha:c.parents for c in commits}
    return {'statistics':statistics(graph),'commits':[
        {**asdict(c),'lane':positions[c.sha][0],'row':positions[c.sha][1],
         'outside_view_parents':[p for p in c.parents if p not in graph]}
        for c in commits]}
