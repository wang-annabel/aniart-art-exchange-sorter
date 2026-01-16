import "./App.css";

function Cards() {
  return (
    <>
      <div className="cards">
        <div className="card">
          <h2>1</h2>
          <h3>Upload CSV</h3>
          <p>
            Convert your responses from this{" "}
            <a href="https://docs.google.com/forms/d/e/1FAIpQLScFKhA3C6UjrvWAEmMqWF7RZaEtQQ-vc-uSoKasQf7ELw8z6g/viewform?usp=header">
              form template
            </a>{" "}
            to CSV format. Or try uploading this{" "}
            <a href="https://drive.google.com/file/d/1-mvbUAsLzPwFjjGxEuRutyTMHQc6uYz_/view?usp=sharing">
              sample input
            </a>
            .
          </p>
        </div>
        <div className="card">
          <h2>2</h2>
          <h3>Review Matching</h3>
          <p>
            Evaluate your matchings with an interactive network graph. You can
            rematch as many times as needed.
          </p>
        </div>
        <div className="card">
          <h2>3</h2>
          <h3>Confirm Matching</h3>
          <p>
            Download the CSV output of your chosen matchings. For best results,
            log in to confirm matchings; this prevents participants from getting
            the same matchings in the future.
          </p>
        </div>
      </div>
    </>
  );
}

export default Cards;
