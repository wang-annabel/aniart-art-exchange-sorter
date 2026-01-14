// RematchBtn.jsx

function RematchBtn({ apiBase, fileId, onRematchComplete }) {
  const handleRematch = async () => {
    try {
      console.log("Rematching with file_id:", fileId);

      const matchResponse = await fetch(
        `${apiBase}/matchings?file_id=${fileId}`,
        {
          method: "POST",
        }
      );

      if (!matchResponse.ok) {
        const errorData = await matchResponse.json();
        throw new Error(errorData.detail || "Matching creation failed");
      }

      const matchData = await matchResponse.json();
      const matchingId = matchData.matching_id;

      console.log("New matching created, ID:", matchingId);

      // Callback to parent with the new matching data
      onRematchComplete(matchingId, fileId);
    } catch (error) {
      console.error("Rematch error:", error);
      alert(`Error: ${error.message}`);
    }
  };

  return (
    <button id="rematch-btn" onClick={handleRematch}>
      Rematch
    </button>
  );
}

export default RematchBtn;
