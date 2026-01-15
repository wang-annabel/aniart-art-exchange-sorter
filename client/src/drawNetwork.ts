// drawNetwork.ts
export interface Node extends d3.SimulationNodeDatum {
  id: string;
  group: string;
  name?: string;
  discord?: string;
  email?: string;
  matched?: boolean;
}

export interface Link extends d3.SimulationLinkDatum<Node> {
  source: string | Node;
  target: string | Node;
  value: number;
}

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
  hoveredNode?: Node | null,
  radius: number = 10 // Add radius parameter with default
) => {
  context.clearRect(0, 0, width, height);
  const totalNodes = nodes.length;
  const showAllNames = totalNodes < 50;
  const neighbors = hoveredNode ? getNeighbors(hoveredNode, links) : new Set();

  // Draw links
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
    context.lineWidth = isHighlighted ? 2 : 1;
    context.globalAlpha = hoveredNode && !isHighlighted ? 0.2 : 0.6;
    context.stroke();
    context.globalAlpha = 1;

    // Draw arrow for highlighted links
    if (isHighlighted) {
      const angle = Math.atan2(target.y - source.y, target.x - source.x);
      const arrowLength = 8;
      const arrowWidth = 6;

      const arrowX = target.x - Math.cos(angle) * (radius + 2);
      const arrowY = target.y - Math.sin(angle) * (radius + 2);

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

  // Draw nodes
  nodes.forEach((node) => {
    if (!node.x || !node.y) {
      return;
    }

    const isHovered = hoveredNode?.id === node.id;
    const isNeighbor = hoveredNode && neighbors.has(node.id);
    const isHighlighted = isHovered || isNeighbor;
    const isUnmatched = node.matched === false;

    context.globalAlpha = hoveredNode && !isHighlighted ? 0.3 : 1;

    context.beginPath();
    context.arc(
      node.x,
      node.y,
      isHovered ? radius + 2 : radius,
      0,
      2 * Math.PI
    );
    // Different colors for matched vs unmatched
    if (isUnmatched) {
      context.fillStyle = isHovered ? "#ef4444" : "#f87171"; // Red for unmatched
    } else {
      context.fillStyle = isHovered ? "#3b82f6" : "#6366f1"; // Blue for matched
    }
    context.fill();

    if (isUnmatched) {
      context.strokeStyle = isHighlighted ? "#dc2626" : "#ef4444";
    } else {
      context.strokeStyle = isHighlighted ? "#60a5fa" : "#4f46e5";
    }
    context.lineWidth = isHighlighted ? 2 : 1.5;
    context.stroke();

    context.globalAlpha = 1;

    // Draw labels with conditional visibility
    if (node.name) {
      const firstName = node.name.split(" ")[0];

      // Show name if: under threshold OR currently hovered
      if (showAllNames || isHovered) {
        context.fillStyle = "#342452";
        context.font = `${isHovered ? "bold " : ""}11px sans-serif`;
        context.textAlign = "center";
        context.textBaseline = "middle";
        context.fillText(firstName, node.x, node.y + radius + 12);
      }

      // Show discord handle ONLY if hovered
      if (isHovered && node.discord) {
        context.fillStyle = "#60a5fa"; // Lighter blue for discord
        context.font = "10px sans-serif";
        context.textAlign = "center";
        context.textBaseline = "middle";
        context.fillText(node.discord, node.x, node.y + radius + 24);
      }
    }
  });
};
