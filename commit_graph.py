import argparse
import json
from pathlib import Path
from history import export_data, read_history, statistics, topological_order

def read_log(repository='.', limit=100, all_refs=False):
    return {c.sha:c.parents for c in read_history(repository,limit,all_refs)}

def layout(graph):
    lanes,positions = [],{}
    for row,commit in enumerate(topological_order(graph)):
        if commit not in lanes:
            if None in lanes:
                lanes[lanes.index(None)] = commit
            else:
                lanes.append(commit)
        lane = lanes.index(commit)
        positions[commit] = (lane,row)
        lanes[lane] = None
        for index,parent in enumerate(graph[commit]):
            if parent not in graph or parent in lanes or parent in positions:
                continue
            if index == 0 and lanes[lane] is None:
                lanes[lane] = parent
            elif None in lanes:
                lanes[lanes.index(None)] = parent
            else:
                lanes.append(parent)
    return positions

def short(text, width=65):
    return text if len(text) <= width else text[:width-1]+'…'

def plot(graph, output=None, show=True, metadata=None, subjects=True):
    import matplotlib
    if not show:
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    positions = layout(graph)
    details = {c.sha:c for c in metadata or []}
    lane_count = 1+max((p[0] for p in positions.values()),default=0)
    figure,axes = plt.subplots(figsize=(12,min(100,max(3,len(graph)*0.32+1))))
    figure.patch.set_facecolor('#101820')
    axes.set_facecolor('#101820')
    palette = ['#57c4e5','#ffb454','#b8de6f','#d7aefb','#ff8299','#71dbc3']
    label_column = lane_count+0.3
    for commit in topological_order(graph):
        parents = graph[commit]
        x,y = positions[commit]
        color = palette[x%len(palette)]
        for parent in parents:
            if parent in positions:
                px,py = positions[parent]
                bend = y+0.45
                axes.plot([x,x,px,px],[y,bend,bend,py],color=color,linewidth=1.8,zorder=1,alpha=0.85)
            else:
                axes.annotate('',xy=(x,y+0.7),xytext=(x,y+0.15),
                              arrowprops={'arrowstyle':'->','color':color,'linestyle':'dashed'})
        axes.scatter([x],[y],color=color,s=50,edgecolor='#101820',linewidth=1,zorder=2)
        detail = details.get(commit)
        label = commit[:7]
        if detail is not None:
            if subjects:
                label += '  '+short(detail.subject)
            if detail.refs:
                label += '  ['+short(detail.refs,55)+']'
        axes.text(label_column,y,label,va='center',fontsize=9,color='#edf4f7',fontfamily='DejaVu Sans')
    if not graph:
        axes.text(0.5,0.5,'No commits',ha='center',color='white',transform=axes.transAxes)
    summary = statistics(graph)
    axes.set_title(f"Git history · {summary['commits']} commits · {summary['merges']} merges",color='white',pad=16)
    axes.set_ylim(max(len(graph)-0.3,1),-0.8)
    axes.set_xlim(-0.5,label_column+max(6,lane_count*0.3))
    axes.axis('off')
    figure.tight_layout()
    if output:
        Path(output).parent.mkdir(parents=True,exist_ok=True)
        figure.savefig(output,dpi=160,facecolor=figure.get_facecolor(),bbox_inches='tight')
    if show:
        plt.show()
    plt.close(figure)
    return positions

def main():
    parser = argparse.ArgumentParser(description='Plot Git ancestry with commit subjects and branch labels')
    parser.add_argument('repository',nargs='?',default='.')
    parser.add_argument('--limit',type=int,default=100)
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument('--all',action='store_true')
    scope.add_argument('--ref',help='One branch, tag, or commit to follow')
    parser.add_argument('--output',help='PNG, SVG, or PDF image path')
    parser.add_argument('--json',dest='json_output',help='Save commit metadata, layout, and statistics')
    parser.add_argument('--no-show',action='store_true')
    parser.add_argument('--no-subjects',action='store_true')
    args = parser.parse_args()
    try:
        commits = read_history(args.repository,args.limit,args.all,args.ref)
        graph = {c.sha:c.parents for c in commits}
        positions = plot(graph,args.output,not args.no_show,commits,not args.no_subjects)
    except (ValueError,OSError) as error:
        parser.error(str(error))
    data = export_data(commits,positions)
    if args.json_output:
        target = Path(args.json_output)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(data['statistics'],indent=2))

if __name__ == '__main__':
    main()
