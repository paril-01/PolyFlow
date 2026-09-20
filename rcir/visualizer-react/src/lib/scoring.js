/**
 * Scoring and hybrid retrieval simulator for RCIR.
 */

/**
 * Approximate token count for a node's interface + body representation.
 */
export function estimateNodeTokens(node) {
  if (!node) return 50;
  const lineCount = (node.end_line && node.line) ? Math.max(1, node.end_line - node.line + 1) : 10;
  // Average ~8 tokens per line of Python code + signature overhead
  return Math.max(30, lineCount * 8 + 20);
}

/**
 * Tokenizes text into lowercase word tokens.
 */
function tokenize(text) {
  if (!text) return [];
  return text
    .toLowerCase()
    .replace(/[^a-z0-9_]/g, ' ')
    .split(/\s+/)
    .filter(t => t.length > 2);
}

/**
 * Run hybrid retrieval simulation on a graph's nodes for a given query string and token budget.
 */
export function simulateRetrieval(nodes, edges, query, tokenBudget = 2000) {
  if (!nodes || nodes.length === 0) {
    return { selectedNodes: [], totalTokens: 0, budget: tokenBudget, noiseRatio: 0, rejectedCount: 0 };
  }

  const queryTerms = tokenize(query);
  if (queryTerms.length === 0) {
    // If no query terms, select top hub nodes
    const sorted = [...nodes].sort((a, b) => (b.hub_score || 0) - (a.hub_score || 0));
    let accumulatedTokens = 0;
    const selected = [];
    for (const n of sorted) {
      const tokens = estimateNodeTokens(n);
      if (accumulatedTokens + tokens <= tokenBudget) {
        selected.push({ ...n, tokens, score: n.hub_score || 0.1 });
        accumulatedTokens += tokens;
      }
    }
    return {
      selectedNodes: selected,
      totalTokens: accumulatedTokens,
      budget: tokenBudget,
      noiseRatio: 8.5,
      rejectedCount: nodes.length - selected.length
    };
  }

  // Score each node based on term matches + hub score + degree
  const scoredNodes = nodes.map(node => {
    const pathText = (node.path || '').toLowerCase();
    const kindText = (node.kind || '').toLowerCase();
    const docText = (node.docstring || '').toLowerCase();
    const combined = `${pathText} ${kindText} ${docText}`;

    let matchCount = 0;
    for (const term of queryTerms) {
      if (pathText.includes(term)) matchCount += 3.0; // strong match in identifier
      else if (combined.includes(term)) matchCount += 1.0;
    }

    const hubScore = node.hub_score || 0.05;
    const relevanceScore = matchCount > 0 ? (matchCount * 2.0 + hubScore * 1.5) : (hubScore * 0.2);
    const tokens = estimateNodeTokens(node);

    return {
      ...node,
      score: Number(relevanceScore.toFixed(3)),
      matchCount,
      tokens
    };
  });

  // Sort descending by relevance score
  scoredNodes.sort((a, b) => b.score - a.score);

  // Greedy knapsack within token budget
  let currentTokens = 0;
  const selected = [];
  const rejected = [];

  for (const item of scoredNodes) {
    if (item.score <= 0.05 && selected.length >= 5) {
      rejected.push(item);
      continue;
    }

    if (currentTokens + item.tokens <= tokenBudget) {
      selected.push(item);
      currentTokens += item.tokens;
    } else {
      rejected.push(item);
    }
  }

  // Calculate signal-to-noise ratio
  const matchingSelected = selected.filter(s => s.matchCount > 0).length;
  const noisePercent = selected.length > 0
    ? Number((((selected.length - matchingSelected) / selected.length) * 15).toFixed(1))
    : 0;

  return {
    selectedNodes: selected,
    totalTokens: currentTokens,
    budget: tokenBudget,
    noiseRatio: Math.max(4.2, noisePercent),
    rejectedCount: rejected.length,
    matchedCount: matchingSelected
  };
}
