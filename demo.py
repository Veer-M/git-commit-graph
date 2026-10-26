import argparse
from pathlib import Path
import tempfile
import json
import subprocess
from history import export_data, read_history
from commit_graph import plot

def generate(output='examples'):
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as repository:
        def git(*args):
            result = subprocess.run(['git','-C',repository,*args],capture_output=True,text=True)
            if result.returncode:
                raise RuntimeError(result.stderr)
        def commit(message):
            git('commit','--allow-empty','-m',message)
        git('init','-b','main')
        git('config','user.name','Demo')
        git('config','user.email','demo@example.invalid')
        commit('Start example project')
        git('checkout','-b','feature/tracking')
        commit('Detect colored markers')
        commit('Keep object IDs between frames')
        git('checkout','main')
        commit('Add command-line configuration')
        git('merge','--no-ff','feature/tracking','-m','Merge tracking feature')
        git('tag','v1.0')
        git('checkout','-b','feature/reports')
        commit('Export movement statistics')
        git('checkout','main')
        commit('Document sample workflow')
        commits = read_history(repository,all_refs=True)
        graph = {c.sha:c.parents for c in commits}
        positions = plot(graph,output/'history.png',False,commits)
        plot(graph,output/'history.svg',False,commits)
        (output/'history.json').write_text(json.dumps(export_data(commits,positions),indent=2)+'\n',encoding='utf-8')
    return len(commits)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Render a disposable sample Git history without changing your repository')
    parser.add_argument('--output',default='examples')
    args = parser.parse_args()
    print(f'Generated example with {generate(args.output)} commits')
