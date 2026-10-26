import os
os.environ['MPLBACKEND'] = 'Agg'
import subprocess
from commit_graph import layout, read_log, plot

def test_merge_lanes_and_render(tmp_path):
    graph = {'merge':['left','right'],'left':['root'],'right':['root'],'root':[]}
    points = layout(graph)
    assert points['left'][0] != points['right'][0]
    assert all(points[c][1] < points[p][1] for c,parents in graph.items() for p in parents)
    output = tmp_path/'graph.png'
    plot(graph,output,False)
    assert output.stat().st_size > 1000

def test_real_git_log(tmp_path):
    def git(*args):
        return subprocess.run(['git','-C',str(tmp_path),*args],check=True,capture_output=True,text=True)
    git('init')
    git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','--allow-empty','-m','root')
    git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','--allow-empty','-m','next')
    graph = read_log(tmp_path)
    assert len(graph) == 2
    commits = list(graph)
    assert graph[commits[0]] == [commits[1]]
