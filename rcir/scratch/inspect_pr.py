from rcir.benchmarks.online_boutique import run_online_boutique_benchmark

res = run_online_boutique_benchmark()
pr = res['precision_recall']

print('False negatives (missed):')
for fn in pr['false_negative_details']:
    print(' ', fn)

print('\nFalse positives sample (first 25):')
for fp in pr['false_positive_details'][:25]:
    print(' ', fp['source'], '->', fp['target'], f"[{fp.get('edge_class')}]", fp.get('reason', '')[:50])

print('\nSummary:')
print('Total graph edges:', pr['overall']['total_graph_edges'])
print('Candidates evaluated:', pr['overall']['candidates_evaluated'])
print('Ground truth edges:', pr['overall']['ground_truth_edges'])
print('Precision:', pr['overall']['precision'])
print('Recall:', pr['overall']['recall'])
