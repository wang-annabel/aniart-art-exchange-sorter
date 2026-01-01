// drawNetwork.ts
export interface Node extends d3.SimulationNodeDatum {
  id: string;
  group: string;
  name?: string;
  discord?: string;
  email?: string;
}

export interface Link extends d3.SimulationLinkDatum<Node> {
  source: string | Node;
  target: string | Node;
  value: number;
}

export const RADIUS = 10;

// Helper to get neighbors of a node
const getNeighbors = (node: Node, links: Link[]): Set<string> => {
  const neighbors = new Set<string>();
  links.forEach((link) => {
    const sourceId =
      typeof link.source === "object" ? link.source.id : link.source;
    const targetId =
      typeof link.target === "object" ? link.target.id : link.target;

    if (sourceId === node.id) {
      neighbors.add(targetId);
    }
    if (targetId === node.id) {
      neighbors.add(sourceId);
    }
  });
  return neighbors;
};

export const drawNetwork = (
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
  nodes: Node[],
  links: Link[],
  hoveredNode?: Node | null
) => {
  context.clearRect(0, 0, width, height);

  const neighbors = hoveredNode ? getNeighbors(hoveredNode, links) : new Set();

  // Draw the links
  links.forEach((link) => {
    const source =
      typeof link.source === "object"
        ? link.source
        : nodes.find((n) => n.id === link.source);
    const target =
      typeof link.target === "object"
        ? link.target
        : nodes.find((n) => n.id === link.target);

    if (
      !source ||
      !target ||
      !source.x ||
      !source.y ||
      !target.x ||
      !target.y
    ) {
      return;
    }

    const isHighlighted =
      hoveredNode &&
      (source.id === hoveredNode.id || target.id === hoveredNode.id);

    context.beginPath();
    context.moveTo(source.x, source.y);
    context.lineTo(target.x, target.y);
    context.strokeStyle = isHighlighted ? "#3b82f6" : "#64748b";
    context.lineWidth = isHighlighted ? 3 : 1.5;
    context.globalAlpha = hoveredNode && !isHighlighted ? 0.2 : 0.6;
    context.stroke();
    context.globalAlpha = 1;

    // Draw arrow for highlighted links
    if (isHighlighted) {
      const angle = Math.atan2(target.y - source.y, target.x - source.x);
      const arrowLength = 8;
      const arrowWidth = 6;

      // Position arrow at the edge of target node
      const arrowX = target.x - Math.cos(angle) * (RADIUS + 2);
      const arrowY = target.y - Math.sin(angle) * (RADIUS + 2);

      context.beginPath();
      context.moveTo(arrowX, arrowY);
      context.lineTo(
        arrowX - arrowLength * Math.cos(angle) + arrowWidth * Math.sin(angle),
        arrowY - arrowLength * Math.sin(angle) - arrowWidth * Math.cos(angle)
      );
      context.lineTo(
        arrowX - arrowLength * Math.cos(angle) - arrowWidth * Math.sin(angle),
        arrowY - arrowLength * Math.sin(angle) + arrowWidth * Math.cos(angle)
      );
      context.closePath();
      context.fillStyle = "#3b82f6";
      context.fill();
    }
  });

  // Draw the nodes
  nodes.forEach((node) => {
    if (!node.x || !node.y) {
      return;
    }

    const isHovered = hoveredNode?.id === node.id;
    const isNeighbor = hoveredNode && neighbors.has(node.id);
    const isHighlighted = isHovered || isNeighbor;

    // Dim non-highlighted nodes when hovering
    context.globalAlpha = hoveredNode && !isHighlighted ? 0.3 : 1;

    // Draw node circle
    context.beginPath();
    context.arc(
      node.x,
      node.y,
      isHovered ? RADIUS + 3 : RADIUS,
      0,
      2 * Math.PI
    );
    context.fillStyle = isHovered ? "#3b82f6" : "#6366f1";
    context.fill();

    // Draw border
    context.strokeStyle = isHighlighted ? "#60a5fa" : "#4f46e5";
    context.lineWidth = isHighlighted ? 2.5 : 2;
    context.stroke();

    context.globalAlpha = 1;

    // Draw label (first name only)
    if (node.name) {
      const firstName = node.name.split(" ")[0];
      //context.fillStyle = "white";
      context.font = `${isHovered ? "bold " : ""}12px sans-serif`;
      context.textAlign = "center";
      context.textBaseline = "middle";
      context.fillText(firstName, node.x, node.y + RADIUS + 15);
    }
  });
};
