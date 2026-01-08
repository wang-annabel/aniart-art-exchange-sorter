import { useState } from "react";
import Graph from "./Graph";
import Cards from "./Cards";
import "./App.css";

function App() {
  const [count, setCount] = useState(0);
  // eventually set this to retrieve matchings from local storage
  const [matchings, setMatchings] = useState([]);

  return (
    <>
      <div className="content">
        <h1>Art Exchange Sorter</h1>
        <button className="upload-btn">
          <span>
            <img id="upload-btn-icon" src="\upload.png" />
          </span>
          <span>Upload CSV</span>
        </button>
      </div>
      <div id="content">
        {matchings.length == 0 && <Cards />}
        {matchings.length > 0 && <Graph width={400} height={400} />}
      </div>
    </>
  );
}

export default App;
