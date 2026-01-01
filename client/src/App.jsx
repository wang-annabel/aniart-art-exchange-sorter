import { useState } from "react";
import Graph from "./Graph";
import "./App.css";

function App() {
  const [count, setCount] = useState(0);

  return (
    <>
      <Graph width={400} height={400} />
    </>
  );
}

export default App;
