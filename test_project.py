import os
os.environ['MPLBACKEND'] = 'Agg'
import subprocess
from commit_graph import layout, read_log, plot
from history import read_history, statistics, topological_order, export_data
import pytest

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

def test_unordered_graph_and_cycle_detection():
    graph = {'root':[],'left':['root'],'right':['root'],'merge':['left','right']}
    order = topological_order(graph)
    assert order[0] == 'merge' and order[-1] == 'root'
    positions = layout(graph)
    assert all(positions[c][1] < positions[p][1] for c,parents in graph.items() for p in parents)
    with pytest.raises(ValueError):
        layout({'a':['b'],'b':['a']})

def test_merge_metadata_refs_and_truncation(tmp_path):
    def git(*args):
        return subprocess.run(['git','-C',str(tmp_path),*args],check=True,capture_output=True,text=True).stdout
    git('init','-b','main')
    git('config','user.name','Example')
    git('config','user.email','example@example.invalid')
    git('commit','--allow-empty','-m','root')
    git('checkout','-b','feature')
    git('commit','--allow-empty','-m','feature')
    git('checkout','main')
    git('commit','--allow-empty','-m','main work')
    git('merge','--no-ff','feature','-m','merge feature')
    git('tag','v1')
    commits = read_history(tmp_path,all_refs=True)
    graph = {c.sha:c.parents for c in commits}
    stats = statistics(graph)
    assert stats == {'commits':4,'visible_parent_edges':4,'boundary_parent_edges':0,'merges':1,'roots':1,'branch_points':1,'tips':1}
    assert 'tag: v1' in commits[0].refs
    assert commits[0].subject == 'merge feature'
    assert commits[0].author == 'Example'
    assert len(read_history(tmp_path,ref='feature')) == 2
    truncated = read_history(tmp_path,limit=1)
    data = export_data(truncated,layout({c.sha:c.parents for c in truncated}))
    assert data['statistics']['boundary_parent_edges'] == 2
    assert len(data['commits'][0]['outside_view_parents']) == 2
    with pytest.raises(ValueError):
        read_history(tmp_path,ref='--all')

def test_missing_repo_and_bad_limits(tmp_path):
    with pytest.raises(ValueError):
        read_history(tmp_path)
    with pytest.raises(ValueError):
        read_history(tmp_path,limit=0)

def test_empty_and_disconnected_graphs(tmp_path):
    assert layout({}) == {}
    assert statistics({})['commits'] == 0
    plot({},tmp_path/'empty.svg',False)
    assert (tmp_path/'empty.svg').stat().st_size > 100
    positions = layout({'a':[],'b':[]})
    assert positions['a'][1] != positions['b'][1]
