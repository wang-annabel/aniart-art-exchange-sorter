// Graph.jsx
import { useRef, useEffect, useState } from "react";
import * as d3 from "d3";
import { RADIUS, drawNetwork } from "./drawNetwork";

const sampleData = {
  nodes: [
    {
      id: "1",
      name: "Alice Chen",
      discord: "alice#1234",
      email: "alice@example.com",
    },
    {
      id: "2",
      name: "Bob Smith",
      discord: "bob#5678",
      email: "bob@example.com",
    },
    {
      id: "3",
      name: "Carol Wang",
      discord: "carol#9012",
      email: "carol@example.com",
    },
    {
      id: "4",
      name: "David Lee",
      discord: "david#3456",
      email: "david@example.com",
    },
    {
      id: "5",
      name: "Eve Park",
      discord: "eve#7890",
      email: "eve@example.com",
    },
  ],
  links: [
    { source: "1", target: "2", value: 1 },
    { source: "2", target: "3", value: 1 },
    { source: "3", target: "4", value: 1 },
    { source: "4", target: "5", value: 1 },
    { source: "5", target: "1", value: 1 },
  ],
};

function Graph({ width = 800, height = 600, data = sampleData }) {
  const links = data.links.map((d) => ({ ...d }));
  const nodes = data.nodes.map((d) => ({ ...d }));

  const canvasRef = useRef(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const hoveredNodeRef = useRef(null); // ← Add ref to track hover

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!context || !canvas) {
      return;
    }

    const simulation = d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3
          .forceLink(links)
          .id((d) => d.id)
          .distance(100)
      )
      .force("collide", d3.forceCollide().radius(RADIUS + 5))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .on("tick", () => {
        // Use ref instead of state
        drawNetwork(
          context,
          width,
          height,
          nodes,
          links,
          hoveredNodeRef.current
        );
      });

    const handleMouseMove = (event) => {
      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;

      let found = null;
      for (const node of nodes) {
        if (node.x && node.y) {
          const dx = node.x - x;
          const dy = node.y - y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < RADIUS + 5) {
            found = node;
            break;
          }
        }
      }

      // Update both ref and state
      hoveredNodeRef.current = found;
      setHoveredNode(found); // For tooltip display
      canvas.style.cursor = found ? "pointer" : "default";

      // Manually trigger a redraw
      drawNetwork(context, width, height, nodes, links, found);
    };

    canvas.addEventListener("mousemove", handleMouseMove);

    return () => {
      simulation.stop();
      canvas.removeEventListener("mousemove", handleMouseMove);
    };
  }, [width, height, nodes, links]); // hoveredNode NOT in dependencies

  return (
    <div style={{ position: "relative" }}>
      <canvas
        ref={canvasRef}
        style={{ width, height }}
        width={width}
        height={height}
      />
      {/* {hoveredNode && (
        <div
          style={{
            position: "absolute",
            top: "10px",
            left: "10px",
            background: "rgba(0, 0, 0, 0.8)",
            color: "white",
            padding: "8px 12px",
            borderRadius: "4px",
            pointerEvents: "none",
            fontSize: "14px",
          }}
        >
          <div>
            <strong>{hoveredNode.name}</strong>
          </div>
          <div>{hoveredNode.discord}</div>
          <div>{hoveredNode.email}</div>
        </div>
      )} */}
    </div>
  );
}

export default Graph;
