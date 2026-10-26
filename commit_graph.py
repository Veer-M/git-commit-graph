import argparse
import subprocess

def read_log(repository='.', limit=100, all_refs=False):
    if limit < 1:
        raise ValueError('Limit must be positive')
    command = ['git','-C',str(repository),'log','--topo-order',f'--max-count={limit}','--pretty=format:%H|%P']
    if all_refs:
        command.append('--all')
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValueError(result.stderr.strip() or 'Cannot read Git history')
    graph = {}
    for line in result.stdout.splitlines():
        commit, parents = line.split('|',1)
        graph[commit] = parents.split()
    return graph

def layout(graph):
    lanes = []
    positions = {}
    for row, (commit, parents) in enumerate(graph.items()):
        if commit not in lanes:
            lanes.append(commit)
        lane = lanes.index(commit)
        positions[commit] = (lane,row)
        lanes[lane] = None
        for index, parent in enumerate(parents):
            if parent in lanes or parent in positions:
                continue
            if index == 0 and lanes[lane] is None:
                lanes[lane] = parent
            else:
                try:
                    vacant = lanes.index(None)
                    lanes[vacant] = parent
                except ValueError:
                    lanes.append(parent)
    return positions

def plot(graph, output=None, show=True):
    import matplotlib.pyplot as plt
    points = layout(graph)
    figure, axes = plt.subplots(figsize=(8,max(3,min(30,len(graph)*0.28))))
    for commit, parents in graph.items():
        x,y = points[commit]
        for parent in parents:
            if parent in points:
                px,py = points[parent]
                axes.plot([x,px],[y,py],color=f'C{x%10}',linewidth=1.5,zorder=1)
        axes.scatter([x],[y],color=f'C{x%10}',s=35,zorder=2)
        axes.annotate(commit[:7],(x,y),xytext=(8,0),textcoords='offset points',fontsize=8)
    if not graph:
        axes.text(0.5,0.5,'No commits',ha='center',transform=axes.transAxes)
    axes.invert_yaxis()
    axes.set_xlabel('History lane')
    axes.set_ylabel('Topological order (newest first)')
    axes.set_title('Git commit ancestry')
    axes.margins(x=0.3,y=0.05)
    figure.tight_layout()
    if output:
        figure.savefig(output,dpi=160)
    if show:
        plt.show()
    plt.close(figure)
    return points

def main():
    parser = argparse.ArgumentParser(description='Plot actual Git commit ancestry')
    parser.add_argument('repository',nargs='?',default='.')
    parser.add_argument('--limit',type=int,default=100)
    parser.add_argument('--all',action='store_true')
    parser.add_argument('--output')
    parser.add_argument('--no-show',action='store_true')
    args = parser.parse_args()
    try:
        graph = read_log(args.repository,args.limit,args.all)
    except ValueError as error:
        parser.error(str(error))
    plot(graph,args.output,not args.no_show)

if __name__ == '__main__':
    main()
