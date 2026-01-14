// Graph.jsx
import { useRef, useEffect, useState, useMemo } from "react";
import * as d3 from "d3";
import { drawNetwork } from "./drawNetwork";

const RADIUS = 8;

function Graph({ data, nodeRadius = RADIUS }) {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [hoveredNode, setHoveredNode] = useState(null);
  const hoveredNodeRef = useRef(null);

  // Memoize to prevent recreating on every render
  const links = useMemo(
    () => (data?.links ? data.links.map((d) => ({ ...d })) : []),
    [data?.links]
  );

  const nodes = useMemo(
    () => (data?.nodes ? data.nodes.map((d) => ({ ...d })) : []),
    [data?.nodes]
  );

  // Handle resize - update dimensions when container size changes
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        const newWidth = Math.floor(width);
        const newHeight = Math.floor(height);

        setDimensions((prev) => {
          if (
            Math.abs(prev.width - newWidth) > 5 ||
            Math.abs(prev.height - newHeight) > 5
          ) {
            return { width: newWidth, height: newHeight };
          }
          return prev;
        });
      }
    };

    const timer = setTimeout(updateDimensions, 0);

    let resizeTimeout;
    const handleResize = () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(updateDimensions, 150);
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      clearTimeout(resizeTimeout);
      clearTimeout(timer);
    };
  }, []);

  // D3 simulation effect
  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");

    if (!context || !canvas || nodes.length === 0) {
      return;
    }

    const nodeCount = nodes.length;
    const chargeStrength = -300 * Math.sqrt(nodeCount / 10);
    const linkDistance = Math.min(100, dimensions.width / 8);

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
      .force("x", d3.forceX(dimensions.width / 2).strength(0.2))
      .force("y", d3.forceY(dimensions.height / 2).strength(0.2))
      .on("tick", () => {
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

  if (!data || nodes.length === 0) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "400px",
        }}
      >
        <p>No data to display</p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        minHeight: "400px",
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
    </div>
  );
}

export default Graph;
