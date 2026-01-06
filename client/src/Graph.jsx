// Graph.jsx - Responsive version
import { useRef, useEffect, useState, useMemo } from "react";
import * as d3 from "d3";
import { drawNetwork } from "./drawNetwork";

import sampleData from "./sampleData";

// Make RADIUS configurable
const RADIUS = 8; // Smaller for larger graphs

function Graph({ data = sampleData, nodeRadius = RADIUS }) {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [hoveredNode, setHoveredNode] = useState(null);
  const hoveredNodeRef = useRef(null);

  // Memoize to prevent recreating on every render
  const links = useMemo(() => data.links.map((d) => ({ ...d })), [data.links]);
  const nodes = useMemo(() => data.nodes.map((d) => ({ ...d })), [data.nodes]);

  // Handle resize - update dimensions when container size changes
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height });
      }
    };

    // Set initial dimensions
    updateDimensions();

    // Listen for resize events
    window.addEventListener("resize", updateDimensions);

    return () => {
      window.removeEventListener("resize", updateDimensions);
    };
  }, []);

  // D3 simulation effect
  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!context || !canvas) {
      return;
    }

    // Scale force strengths based on number of nodes
    const nodeCount = nodes.length;
    const chargeStrength = -300 * Math.sqrt(nodeCount / 10); // Stronger repulsion for more nodes
    const linkDistance = Math.min(150, dimensions.width / 8); // Scale with canvas size

    const simulation = d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3
          .forceLink(links)
          .id((d) => d.id)
          .distance(linkDistance)
      )
      .force("collide", d3.forceCollide().radius(nodeRadius + 5))
      .force("charge", d3.forceManyBody().strength(chargeStrength))
      .force(
        "center",
        d3.forceCenter(dimensions.width / 2, dimensions.height / 2)
      )
      // Keep nodes within bounds
      .force("x", d3.forceX(dimensions.width / 2).strength(0.05))
      .force("y", d3.forceY(dimensions.height / 2).strength(0.05))
      .on("tick", () => {
        // Constrain nodes to canvas bounds
        nodes.forEach((node) => {
          if (node.x !== undefined && node.y !== undefined) {
            node.x = Math.max(
              nodeRadius,
              Math.min(dimensions.width - nodeRadius, node.x)
            );
            node.y = Math.max(
              nodeRadius,
              Math.min(dimensions.height - nodeRadius, node.y)
            );
          }
        });

        drawNetwork(
          context,
          dimensions.width,
          dimensions.height,
          nodes,
          links,
          hoveredNodeRef.current,
          nodeRadius
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

          if (distance < nodeRadius + 5) {
            found = node;
            break;
          }
        }
      }

      hoveredNodeRef.current = found;
      setHoveredNode(found);
      canvas.style.cursor = found ? "pointer" : "default";
      drawNetwork(
        context,
        dimensions.width,
        dimensions.height,
        nodes,
        links,
        found,
        nodeRadius
      );
    };

    canvas.addEventListener("mousemove", handleMouseMove);

    return () => {
      simulation.stop();
      canvas.removeEventListener("mousemove", handleMouseMove);
    };
  }, [dimensions, nodes, links, nodeRadius]);

  return (
    <div
      ref={containerRef}
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        minHeight: "400px", // Prevent collapse
      }}
    >
      <canvas
        ref={canvasRef}
        style={{
          width: "100%",
          height: "100%",
          display: "block",
        }}
        width={dimensions.width}
        height={dimensions.height}
      />
      {hoveredNode && (
        <div
          style={{
            position: "absolute",
            top: "16px",
            left: "16px",
            background: "rgba(0, 0, 0, 0.9)",
            color: "white",
            padding: "12px 16px",
            borderRadius: "8px",
            pointerEvents: "none",
            fontSize: "14px",
            boxShadow: "0 4px 6px rgba(0, 0, 0, 0.3)",
            maxWidth: "250px",
          }}
        >
          <div style={{ fontWeight: "bold", marginBottom: "4px" }}>
            {hoveredNode.name}
          </div>
          <div style={{ fontSize: "12px", opacity: 0.9 }}>
            {hoveredNode.discord}
          </div>
          <div style={{ fontSize: "12px", opacity: 0.8 }}>
            {hoveredNode.email}
          </div>
        </div>
      )}
    </div>
  );
}

export default Graph;
